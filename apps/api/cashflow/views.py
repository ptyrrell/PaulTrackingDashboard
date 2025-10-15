import json
import logging
from collections import OrderedDict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from isoweek import Week

from apps.cashflow.utils import generate_excel
from apps.constants import ROUND_DECIMAL_DIGITS
from apps.models import CashFlowInOut, CashFlowInOutValue, NumberValue
from apps.numbers import WEEK_DATE_FORMAT
from apps.utils import get_weeks_between

logger = logging.getLogger(__name__)

OPEN_BB_INDEX = 'N_BIB'
CREDIT_LM_INDEX = 'N_CR_LIMIT'


def get_start_balance(request, str_iso_weeks):
    try:
        balance = float(NumberValue.objects.get(user=request.user, number__number_index=OPEN_BB_INDEX,
                                                week_index=str_iso_weeks[0]).actual_value)
    except (ObjectDoesNotExist, ValueError, TypeError):
        balance = 0

    return balance


def get_open_bank_balance(request, str_iso_weeks, closing_bank_balance):
    balance = get_start_balance(request, str_iso_weeks)

    # weeks sort matters here
    str_iso_weeks = sorted(str_iso_weeks)

    result = {str_iso_weeks[0]: balance}

    for week in str_iso_weeks[1:]:
        prev = str(Week.fromstring(week) - 1)
        result.update({week: closing_bank_balance[prev]})

    return result


def get_closing_bank_balance(request, str_iso_weeks, cash_in, cash_out):
    balance = get_start_balance(request, str_iso_weeks)

    result = {}

    for week in str_iso_weeks:
        # lets make N/A good for this
        balance = balance + cash_in.get(week, 0) - cash_out.get(week, 0)
        result.update({week: round(float(balance), ROUND_DECIMAL_DIGITS)})

    return result


def get_week_value(week, values):
    for value in values:
        if value.week_index == str(week):
            return value.actual_value, value.target_value
    return 0, 0


def get_credit_limit(request, str_iso_weeks):
    try:
        limit = float(NumberValue.objects.get(user=request.user, number__number_index=CREDIT_LM_INDEX,
                                              week_index=str_iso_weeks[0]).actual_value)
    except (ObjectDoesNotExist, ValueError, TypeError):
        limit = 0
    return limit


def get_available_credit(request, str_iso_weeks, closing_bank_balance):
    limit = get_credit_limit(request, str_iso_weeks)

    result = {}
    for week in str_iso_weeks:
        result.update({week: limit + closing_bank_balance.get(week, 0)})
    return result


def get_cash_in_out_values(request, str_iso_weeks, cash_out=False):
    # Only actual values
    value_type = CashFlowInOut.CASH_OUT if cash_out else CashFlowInOut.CASH_IN

    values = CashFlowInOutValue.objects.filter(flow__user=request.user, flow__value_type=value_type,
                                               week_index__in=str_iso_weeks)
    result = {}
    for w in str_iso_weeks:
        if w not in result:
            result.update({w: 0})

        for v in values:
            if v.week_index == w:
                result[w] += round(float(v.actual_value), ROUND_DECIMAL_DIGITS) if v.actual_value else 0

    return result


def get_all_data(request, str_iso_weeks):
    cash_in = get_cash_in_out_values(request, str_iso_weeks)
    cash_out = get_cash_in_out_values(request, str_iso_weeks, cash_out=True)

    closing_balance = get_closing_bank_balance(request, str_iso_weeks, cash_in, cash_out)
    opening_balance = get_open_bank_balance(request, str_iso_weeks, closing_balance)

    limit = get_credit_limit(request, str_iso_weeks)
    available_credit = get_available_credit(request, str_iso_weeks, closing_balance)

    result = {"data": {}}

    for week in str_iso_weeks:
        result["data"].update({week: {

            "cash_in": round(cash_in.get(week), 2),
            "cash_out": round(cash_out.get(week), 2),
            "closing_balance": closing_balance.get(week),
            "opening_balance": opening_balance.get(week),
            "credit_limit": limit,
            "available_credit": available_credit.get(week)
        }})

    result.update({"total": {"cash_in": sum(cash_in.values()), "cash_out": sum(cash_out.values())}})

    return result


class CashSummaryApi(View):

    @method_decorator(login_required)
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CashSummaryApi, self).dispatch(*args, **kwargs)

    def get(self, request):
        start_week = request.GET.get("startWeek")
        end_week = request.GET.get("endWeek")

        if not start_week or not end_week:
            logger.error("Invalid start/end for cashflow summary")
            return HttpResponse(status=400)

        start_week = Week.fromstring(start_week)
        end_week = Week.fromstring(end_week)

        all_weeks = get_weeks_between(start_week, end_week)
        str_iso_weeks = [str(w) for w in all_weeks]

        result = get_all_data(request, str_iso_weeks)
        weeks = OrderedDict([(str(w), str(w.sunday().strftime(WEEK_DATE_FORMAT))) for w in all_weeks])
        result.update({"weeks": weeks})

        return HttpResponse(json.dumps(result), content_type="application/json")


class CashValueApi(View):

    @method_decorator(login_required)
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CashValueApi, self).dispatch(*args, **kwargs)

    def get(self, request, cashflow_type):

        start_week = request.GET.get("startWeek")
        end_week = request.GET.get("endWeek")

        if not start_week or not end_week:
            logger.error("Invalid start/end for cashflow value api")
            return HttpResponse(status=400)

        start_week = Week.fromstring(start_week)
        end_week = Week.fromstring(end_week)

        weeks = [str(w) for w in get_weeks_between(start_week, end_week)]

        value_type = self.get_cashflow_type(cashflow_type)

        debtors = CashFlowInOut.objects.filter(user=request.user, value_type=value_type).order_by('order')
        rows = []

        for debtor in debtors:
            row = {"id": debtor.id, "name": debtor.debtor_name, "weeks": []}

            values = CashFlowInOutValue.objects.filter(flow=debtor, week_index__in=weeks)
            for week in weeks:
                actual, target = get_week_value(week, values)

                if not actual:
                    actual = 0

                if not target:
                    target = 0

                row["weeks"].append({"week": week, "actual": round(actual, 2), "target": round(target, 2)})

            rows.append(row)

        weeks = [{"iso": w, "name": str(Week.fromstring(w).sunday().strftime(WEEK_DATE_FORMAT))} for w in weeks]

        return HttpResponse(json.dumps({"weeks": weeks, "rows": rows}), content_type="application/json")

    def put(self, request, cashflow_type):
        """
        """
        value_type = self.get_cashflow_type(cashflow_type)

        try:
            data = json.loads(request.body.decode("utf-8"))

            debtor_id, week, input_value = int(data["debtor"]), data["week"], data.get("value", 0)

        except (TypeError, KeyError, ValueError) as e:
            return HttpResponseBadRequest(str(e))

        flow = CashFlowInOut.objects.get(id=debtor_id, user=request.user, value_type=value_type)

        try:
            value = CashFlowInOutValue.objects.get(flow=flow, week_index=week)
        except ObjectDoesNotExist:
            value = CashFlowInOutValue.objects.create(flow=flow, week_index=week)

        if input_value is not False:
            value.actual_value = float(input_value) if input_value else None

        value.save()

        return HttpResponse("Ok")

    def post(self, request, cashflow_type):
        """
        """
        value_type = self.get_cashflow_type(cashflow_type)
        try:
            data = json.loads(request.body.decode("utf-8"))
        except ValueError:
            return HttpResponseBadRequest()

        debtor = data.get("debtor", None)

        if not debtor or len(debtor) > 255:
            return HttpResponseBadRequest()

        instance = CashFlowInOut.objects.create(user=request.user, debtor_name=debtor, value_type=value_type)
        instance.save()
        return HttpResponse(json.dumps({"id": instance.id}), status=201)

    def delete(self, request, cashflow_type):
        """
        """
        try:
            data = json.loads(request.body.decode("utf-8"))
            _id = int(data["id"])

        except (TypeError, KeyError, ValueError) as e:
            return HttpResponseBadRequest()

        value_type = self.get_cashflow_type(cashflow_type)
        CashFlowInOut.objects.get(id=_id, user=request.user, value_type=value_type).delete()

        return HttpResponse("Ok", status=204)

    def get_cashflow_type(self, v):
        return CashFlowInOut.CASH_IN if v == "in" else CashFlowInOut.CASH_OUT


class CashOrderApi(View):

    @method_decorator(login_required)
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CashOrderApi, self).dispatch(*args, **kwargs)

    def post(self, request, cashflow_type):

        value_type = self.get_cashflow_type(cashflow_type)

        try:
            data = json.loads(request.body.decode("utf-8")).get("data")

            for _id in data.keys():
                CashFlowInOut.objects.filter(id=int(_id), user=request.user,
                                             value_type=value_type).update(order=data[_id])

        except (TypeError, KeyError, ValueError) as e:
            return HttpResponseBadRequest(str(e))

        return HttpResponse("Ok", status=200)

    def get_cashflow_type(self, v):
        return CashFlowInOut.CASH_IN if v == "in" else CashFlowInOut.CASH_OUT


class CashflowExcelExportApi(View):
    @method_decorator(login_required)
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(CashflowExcelExportApi, self).dispatch(*args, **kwargs)

    def get(self, request):

        start_week = request.GET.get("startWeek")
        end_week = request.GET.get("endWeek")

        if not start_week or not end_week:
            logger.error("Invalid start/end for cashflow summary")
            return HttpResponse(status=400)

        start_week = Week.fromstring(start_week)
        end_week = Week.fromstring(end_week)

        all_weeks = get_weeks_between(start_week, end_week)
        str_iso_weeks = [str(w) for w in all_weeks]

        result = get_all_data(request, str_iso_weeks)
        weeks = OrderedDict([(str(w), str(w.sunday().strftime(WEEK_DATE_FORMAT))) for w in all_weeks])
        result.update({"weeks": weeks})

        name = "Cashflow Summary {} - {}.xlsx".format(weeks.get(start_week), weeks.get(end_week))
        buffer = generate_excel(result)

        response = HttpResponse(buffer.getvalue(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = "attachment; filename={}".format(name)
        return response

