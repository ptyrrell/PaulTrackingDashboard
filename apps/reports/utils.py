import logging

import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.template import Context, loader
from isoweek import Week

from apps.constants import ROUND_DECIMAL_DIGITS
from apps.models import CompletionReport, Customer, Number, NumberValue, CashFlowInOutValue
from apps.utils import send_html_mail

logger = logging.getLogger(__name__)


def calculate_week_report_completion(user, week_index):
    valid_numbers = Number.objects.filter(is_formula=False, is_optional=False)

    if isinstance(user, Customer):
        user = user.user

    values = NumberValue.objects.filter(user=user, number__in=valid_numbers, week_index=week_index)
    good_values = [v for v in values if v.actual_value is not None]

    return int(round(len(good_values)/float(len(valid_numbers)), ROUND_DECIMAL_DIGITS) * 100)


FOCUS_STATUS_DUE = 0
FOCUS_STATUS_SUBMITTED = 1
FOCUS_STATUS_UPDATED = 2
FOCUS_STATUS_NOT_UPDATED = 3


def calculate_due_dates(user, week_index):

    def _is_due_today():
        return Week.thisweek().sunday() == datetime.date.today()

    if isinstance(user, Customer):
        user = user.user

    result = {"cashflow": FOCUS_STATUS_NOT_UPDATED, "numbers": FOCUS_STATUS_NOT_UPDATED}

    cashflow_value = CashFlowInOutValue.objects.filter(flow__user=user, week_index=week_index).order_by("date_updated")[:1]
    numbers_value = NumberValue.objects.filter(user=user, week_index=week_index).order_by("date_updated")[:1]

    if cashflow_value:
        val = cashflow_value[0]

        result["cashflow"] = FOCUS_STATUS_SUBMITTED

        if val.date_updated > val.date_created:
            result["cashflow"] = FOCUS_STATUS_UPDATED
    else:
        if _is_due_today():
            result["cashflow"] = FOCUS_STATUS_DUE

    if numbers_value:
        val = numbers_value[0]

        result["numbers"] = FOCUS_STATUS_SUBMITTED

        if val.date_updated > val.date_created:
            result["numbers"] = FOCUS_STATUS_UPDATED
    else:
        if _is_due_today():
            result["numbers"] = FOCUS_STATUS_DUE

    return result


def calculate_week_cashflow_completion(user, week_index):

    if isinstance(user, Customer):
        user = user.user

    values = CashFlowInOutValue.objects.filter(flow__user=user, week_index=week_index)
    good_values = [v for v in values if v.actual_value is not None]
    # TODO: Expected value
    return int(round(len(good_values)))


def notify_coach_on_report_completion(user, week_index):

    try:
        customer = Customer.objects.get(user=user)
    except ObjectDoesNotExist:
        return

    if customer.disabled or not customer.user.is_active:
        return

    if not customer.coach:
        return

    completion_rate = calculate_week_report_completion(customer, week_index)
    if completion_rate < 10:
        return

    try:
        report = CompletionReport.objects.get(user=customer.user, week_index=week_index)
    except ObjectDoesNotExist:
        report = CompletionReport.objects.create(user=customer.user, week_index=week_index,
                                                 completion_rate=completion_rate)
        report.save()

    if not report.report_emailed:
        ctx = Context({"customer": customer, "week": Week.fromstring(week_index)})
        template = loader.get_template("email_coach_report_notify.html").render(ctx)

        send_html_mail("Key Numbers Report Notification", template, [customer.coach.email])

        report.report_emailed = True
        report.report_emailed_to = customer.coach.email
        report.save()
        logger.warning("Sent report to {} for week {} customer {}".format(report.report_emailed_to, week_index, customer))
    else:
        logger.warning("Completion report notification has been sent already to {} for {} customer {}".format(report.report_emailed_to, week_index, customer))
