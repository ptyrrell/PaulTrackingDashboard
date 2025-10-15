import json

from apps.constants import (
    DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT,
    DEFAULT_SEL_START_WEEK,
)
from apps.models import Customer, CustomerGroup, Number
from apps.numbers import WEEK_DATE_FORMAT
from apps.utils import get_weeks_range
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import View
from isoweek import Week
from apps.permissions import is_supercoach

from .utils import calculate_week_report_completion


valid_numbers = Number.objects.filter(is_formula=False)


def calculate_customer_completion(customer, weeks):
    result = []
    for week in weeks:
        result.append({"week": str(week), "rate": calculate_week_report_completion(customer, week)})

    return result


@login_required
def reports_view(request):

    groups = CustomerGroup.objects.all()
    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT)

    week = Week.thisweek()

    for group in groups:
        if is_supercoach(request.user):
            customers = group.customers.filter(user__is_active=True)
        else:
            customers = Customer.objects.filter(coach=request.user, user__is_active=True, groups__in=[group,])

        for customer in customers:
            calculate_customer_completion(customer, [str(week - 1)])

    return render(request, "reports.html", {"groups": groups, "weeks": weeks, "week": week})


class ReportsApi(View):

    def get(self, request, group, start_week):

        iso_weeks = [str(w) for w in get_weeks_range(start_week, 6, True)]
        weeks = [{"name": w.sunday().strftime(WEEK_DATE_FORMAT), "iso": str(w)}
                 for w in get_weeks_range(start_week, 6, True)]

        if group == "all":
            # all customers
            if is_supercoach(request.user):
                customers = Customer.objects.filter()
            else:
                customers = Customer.objects.filter(coach=request.user)
        else:
            group = CustomerGroup.objects.get(id=group)

            if is_supercoach(request.user):
                customers = group.customers.filter(user__is_active=True)
            else:
                customers = Customer.objects.filter(coach=request.user, user__is_active=True, groups__in=[group,])

        result = {"weeks": weeks, "customers": []}
        for customer in customers:
            rates = calculate_customer_completion(customer, iso_weeks)
            result["customers"].append({"id": customer.id, "name": customer.name, "email": customer.user.email,
                                        "rates": rates})

        return HttpResponse(json.dumps(result), content_type="application/json")
