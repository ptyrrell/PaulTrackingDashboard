import io
import json
import logging

import xlsxwriter
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from isoweek import Week

from apps.constants import WEEK_DATE_FORMAT
from apps.models import Number, NumberValue
from apps.reports.utils import notify_coach_on_report_completion
from apps.utils import get_weeks_between
from . import read_week_numbers, serialize_number

logger = logging.getLogger(__name__)


class NumbersView(View):

    def get(self, request, week):
        """
        Returns number values per week
        :param request:
        :param week:
        :return:
        """
        if not request.user.is_authenticated():
            logger.error("Not allowed to access NumbersView.get")
            return HttpResponseForbidden()

        week = Week.fromstring(week)

        results = {"week": {"sunday": week.sunday().strftime(WEEK_DATE_FORMAT), "index": week.week}, "numbers": []}

        numbers = read_week_numbers(request.user, week)

        for number in numbers:
            results["numbers"].append(serialize_number(number, week))

        return HttpResponse(json.dumps(results), content_type="application/json")

    def put(self, request, week):
        """
        Updates data for week
        :param request:
        :param week:
        :return:
        """
        data = self.__read_json(request)
        if not data:
            return HttpResponseBadRequest()

        if not request.user.is_authenticated():
            logger.error("Not allowed to access NumbersView.put")
            return HttpResponseForbidden()

        for elm in data:
            number = Number.objects.get(id=int(elm['id']))

            try:
                value = NumberValue.objects.get(number=number, week_index=week, user=request.user)
            except ObjectDoesNotExist:
                value = NumberValue.objects.create(number=number, week_index=week, user=request.user)

            if 'target' in elm:
                value.target_value = self._read_input_val(number, elm, "target")

            if 'actual' in elm:
                value.actual_value = self._read_input_val(number, elm, "actual")

            value.save()

            if 'actual' in elm:
                notify_coach_on_report_completion(request.user, week)

        return HttpResponse("ok")

    @csrf_exempt
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NumbersView, self).dispatch(*args, **kwargs)

    def _read_input_val(self, number, data, attr="target"):
        if attr in data:
            try:
                if number.number_type == Number.TYPE_FLOAT:
                    return float(data[attr])
                elif number.number_type == Number.TYPE_BOOLEAN:
                    return int(data[attr])
            except ValueError:
                logger.exception("Can't read value")
                return None

            return data[attr]

    def __read_json(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            return data
        except ValueError:
            logger.exception("Can't decode json")
            return False


class NumbersExportView(View):

    @csrf_exempt
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(NumbersExportView, self).dispatch(*args, **kwargs)

    def get(self, request):

        start_week = Week.fromstring(request.GET.get("startWeek"))
        end_week = Week.fromstring(request.GET.get("endWeek"))

        weeks = get_weeks_between(start_week, end_week)

        buffer = io.BytesIO()

        workbook = xlsxwriter.Workbook(buffer, {"in_memory": True})
        worksheet = workbook.add_worksheet("Dashboard")

        worksheet.set_column(1, 1, 35)
        worksheet.set_column(3, 3 + len(weeks), 15)

        for i, week in enumerate(weeks):

            column = i + 2

            worksheet.write(0, column, "{}".format(week.sunday()))

            data = read_week_numbers(request.user, week)

            numbers = []
            for number in data:
                numbers.append(serialize_number(number, week))

            for index, number in enumerate(numbers):
                row = index + 1

                if i == 0:
                    worksheet.write(row, 1, number.get("name"))

                actual_value = number.get("value", {}).get("actual_value", "")

                if actual_value:
                    worksheet.write(row, column, "{}{}".format(number.get("actual_symbol"), actual_value))

        workbook.close()

        name = "Dashboard Summary {} - {}.xlsx".format(start_week.sunday(), end_week.sunday())

        response = HttpResponse(buffer.getvalue(),
                                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response["Content-Disposition"] = "attachment; filename={}".format(name)
        return response

