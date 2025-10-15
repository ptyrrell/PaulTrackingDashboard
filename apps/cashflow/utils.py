
import io

import xlsxwriter
from django.core.exceptions import ObjectDoesNotExist
from isoweek import Week

from apps.models import Customer

DEFAULT_WEEKS = 13


def get_default_weeks_number(request):
    try:
        customer = Customer.objects.get(user=request.user)
        return customer.cashflow_weeks
    except ObjectDoesNotExist:
        return DEFAULT_WEEKS


def get_customer_start_week(request):
    try:
        customer = Customer.objects.get(user=request.user)
        week = Week.fromstring(customer.cashflow_start_week)
        return str(week)
    except (ObjectDoesNotExist, ValueError):
        return str(Week.thisweek())


def can_edit_cashflow(request):
    try:
        customer = Customer.objects.get(user=request.user)
        return customer.can_edit_cashflow
    except ObjectDoesNotExist:
        return True


def generate_excel(result):

    weeks = result.get("weeks")
    data = result.get("data")

    buffer = io.BytesIO()

    workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
    worksheet = workbook.add_worksheet("Summary")

    worksheet.set_column(0, 0, 20)
    worksheet.set_column(1, len(weeks), 12)

    column = 1

    worksheet.write(1, 0, "Opening bank balance")
    worksheet.write(2, 0, "Cash In")
    worksheet.write(3, 0, "Cash Out")
    worksheet.write(4, 0, "Closing Bank Balance")
    worksheet.write(5, 0, "Credit Limit")
    worksheet.write(6, 0, "Available Credit")

    for index, week in enumerate(data.keys()):

        row = data.get(week)

        worksheet.write(0, column, weeks.get(week))

        worksheet.write(1, column, row.get("opening_balance"))
        worksheet.write(2, column, row.get("cash_in"))
        worksheet.write(3, column, row.get("cash_out"))
        worksheet.write(4, column, row.get("closing_balance"))
        worksheet.write(5, column, row.get("credit_limit"))
        worksheet.write(6, column, row.get("available_credit"))

        column += 1

    workbook.close()
    return buffer
