from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect, render
from isoweek import Week

from apps.constants import ROUND_DECIMAL_DIGITS, LATEST_YEAR, QUARTER_FORMAT
from apps.models import GuaranteeEarnings, GuaranteeValue, Number, NumberValue
from apps.permissions import is_coach
from apps.utils import (
    get_first_date_of_current_quarter,
    get_first_month_of_quarter,
    get_quarter_num
)
from .forms import GuaranteeEarningsForm, GuaranteeValueForm, WeekRangeForm


def get_revenue_values_in_week_range(user, week_start, week_end):
    number = Number.objects.get(number_index="N_WEEK_SALES")
    values = NumberValue.objects.filter(number=number, user=user, week_index__gte=week_start, week_index__lte=week_end)
    return values


def calculate_total_revenue_by_values(revenue_values):

    total = 0
    for value in revenue_values:
        if value.actual_value:
            total += float(value.actual_value)

    return total


@login_required
def guarantee_view(request):

    user = request.user

    if hasattr(user, "is_impersonate") and user.is_impersonate:
        permission_user = request.impersonator
    else:
        permission_user = user

    if not is_coach(permission_user):
        raise PermissionDenied

    try:
        instance = GuaranteeValue.objects.get(user=user, is_archived=False)
    except GuaranteeValue.DoesNotExist:
        instance = GuaranteeValue(user=user)

    try:
        initial_year = int(user.numbervalue_set.order_by('week_index')[0].week_index[:4])
    except IndexError:
        initial_year = datetime.now().year

    form = GuaranteeValueForm(
        data=request.POST or None,
        instance=instance,
        initial={
            'year_1_lbl': instance.year_1_lbl or initial_year,
            'year_2_lbl': instance.year_2_lbl or initial_year + 1,
            'year_3_lbl': instance.year_3_lbl or initial_year + 2
        })

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.info(request, "Data has been saved succesfully.")
        return redirect("guarantee_view")

    weeks_to_go = revenue_to_date = difference = average_per_week = None
    total_weeks_diff_number = 46

    if instance.next_range_month_delta:
        range_start = instance.next_range_start_date
        range_end = instance.next_range_end_date

        weeks_to_go = Week.withdate(range_end) - Week.thisweek()

        average_per_week = round(
            instance.target_revenue/total_weeks_diff_number, ROUND_DECIMAL_DIGITS)

        revenue_values = get_revenue_values_in_week_range(
            user, Week.withdate(range_start), Week.withdate(range_end))

        revenue_to_date = round(calculate_total_revenue_by_values(revenue_values), ROUND_DECIMAL_DIGITS)
        difference = round(instance.target_revenue - revenue_to_date, ROUND_DECIMAL_DIGITS)

    return render(request, "journey/journey.html", {
        "instance": instance,
        "form": form,
        "average_per_week": average_per_week,
        "weeks_to_go": weeks_to_go,
        "revenue_to_date": revenue_to_date,
        "difference": difference,
        "week_range_form": WeekRangeForm()
    })


@login_required
def journey_archive_view(request):

    queryset = GuaranteeValue.objects.filter(
        user=request.user, is_archived=True)

    paginator = Paginator(queryset, per_page=20)

    try:
        page = paginator.page(request.GET.get('page', 1))
    except (PageNotAnInteger, EmptyPage):
        page = paginator.page(1)

    return render(request, "journey/archive.html", {'page_obj': page})


@login_required
def earnings_view(request):

    if hasattr(request.user, "is_impersonate") and request.user.is_impersonate:
        permission_user = request.impersonator
    else:
        permission_user = request.user

    if not is_coach(permission_user):
        raise PermissionDenied

    user_earnings = GuaranteeEarnings.objects.filter(user=request.user)

    try:
        current_date = datetime.strptime(
            request.GET.get('quarter'), QUARTER_FORMAT).date()
        quarter = get_quarter_num(current_date.month)
    except (ValueError, TypeError):
        quarter = get_first_date_of_current_quarter()
        current_date = date(
            datetime.now().year, get_first_month_of_quarter(quarter), 1)

    try:
        instance = user_earnings.get(date=current_date)
    except ObjectDoesNotExist:
        instance = GuaranteeEarnings(user=request.user, date=current_date)

    form = GuaranteeEarningsForm(data=request.POST or None, instance=instance)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.info(request, "Data has been saved successfully.")
        return redirect(request.get_full_path())

    start_year = _get_earnings_start_year(user_earnings)

    context = {
        "form": form,
        "values": user_earnings.order_by("date"),
        "quarter": quarter,
        "current_date": current_date,
        "start_quarters": _get_quarters(start_year, current_date),
        "end_quarters": _get_quarters(
            start_year, current_date + relativedelta(years=1))
    }

    return render(request, "journey/earnings.html", context)


def _get_earnings_start_year(earnings):
    try:
        return earnings.order_by('date')[0].date.year
    except IndexError:
        quarter = get_first_date_of_current_quarter()

        return date(
            datetime.now().year, get_first_month_of_quarter(quarter), 1).year


def _get_quarters(start_year, current_date):

    quarters = []

    for year in range(start_year, LATEST_YEAR + 1):
        for quarter, month in enumerate([1, 4, 7, 10], start=1):
            d = date(year, month, 1)
            quarters.append({
                'is_current': current_date == d,
                'value': d.strftime(QUARTER_FORMAT),
                'label': '{} - Q{}'.format(d.strftime('%b.%d, %Y'), quarter)
            })

    return quarters
