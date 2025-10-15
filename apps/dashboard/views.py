from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from isoweek import Week

from apps.constants import ROUND_DECIMAL_DIGITS
from apps.focus_sheet.views import UPDATE_DAYS
from apps.models import Customer, FocusSheetValue, CashFlowInOutValue
from apps.utils import get_weeks_between


def calculate_focus_sheet_performance(customer, weeks_list):
    data = FocusSheetValue.objects.filter(week_index__in=weeks_list, user=customer.user)

    submitted = len(data)
    updated = len([x for x in data if (x.date_updated - x.date_created).days > UPDATE_DAYS])

    return round(float(submitted) / len(weeks_list), ROUND_DECIMAL_DIGITS) * 100, round(
        float(updated) / len(weeks_list), ROUND_DECIMAL_DIGITS) * 100


def calculate_cashflow_performance(customer, weeks_list):
    data = CashFlowInOutValue.objects.filter(flow__user=customer.user, week_index__in=weeks_list)
    return round(float(len(data)) / len(weeks_list), ROUND_DECIMAL_DIGITS) * 100


@login_required
def dashboard_view(request):

    if request.user.is_superuser or request.user.is_staff:
        customers = Customer.objects.filter(user__is_active=True).order_by("user__first_name")

    elif request.user.is_coach or request.user.is_supercoach:
        customers = Customer.objects.filter(user__is_active=True, coach__id=request.user.id).order_by("user__first_name")

    current = Week.thisweek()

    last_twelve_weeks = [str(x) for x in get_weeks_between((current - 4 * 3), current)]
    last_year_weeks = [str(x) for x in get_weeks_between((current - 4 * 12), current)]

    focus_data = {"twelve": {"submitted": 0, "updated": 0}, "year": {"submitted": 0, "updated": 0}}
    cashflow_data = {"twelve": {"submitted": 0}, "year": {"submitted": 0}}

    customer = None

    if request.method == "POST":
        customer = list(filter(lambda c: str(c.id) == request.POST.get("customer_id"), customers)).pop()

        focus_data["twelve"]["submitted"], focus_data["twelve"]["updated"] = calculate_focus_sheet_performance(customer,
                                                                                                               last_twelve_weeks)
        focus_data["year"]["submitted"], focus_data["year"]["updated"] = calculate_focus_sheet_performance(customer,
                                                                                                           last_year_weeks)

        cashflow_data["twelve"]["submitted"] = calculate_cashflow_performance(customer, last_twelve_weeks)
        cashflow_data["year"]["submitted"] = calculate_cashflow_performance(customer, last_year_weeks)

    return render(request, "dashboard.html", {"customers": customers, "customer": customer,
                                              "focus_data": focus_data, "cashflow_data": cashflow_data})
