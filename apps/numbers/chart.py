import json
import logging
from collections import OrderedDict

from apps.models import Number, NumberValue
from apps.utils import (
    get_first_week_month,
    get_first_week_quarter,
    get_first_week_year,
    get_quarter_num,
    get_weeks_between,
)
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic import View
from isoweek import Week

from . import WEEK_DATE_FORMAT, calculate_week_number_value


logger = logging.getLogger(__name__)


class NumbersChart(View):

    PERIOD_WEEKLY = "weekly"
    PERIOD_MONTHLY = "monthly"
    PERIOD_QUARTERLY = "quarterly"
    PERIOD_YEARLY = "yearly"
    PERIODS = [PERIOD_WEEKLY, PERIOD_MONTHLY, PERIOD_QUARTERLY, PERIOD_YEARLY]

    def get(self, request, number_id, start_week, end_week=None):
        """

        :param request:
        :param number_id:
        :param start_week:
        :return:
        """
        if not request.user.is_authenticated():
            logger.error("Not allowed to access NumbersChart.get")
            return HttpResponseForbidden()

        if not end_week:
            end_week = str(Week.thisweek())

        period = request.GET.get("period", self.PERIOD_MONTHLY)
        if period not in self.PERIODS:
            period = self.PERIOD_WEEKLY

        if period == self.PERIOD_MONTHLY:
            start_week = get_first_week_month(start_week)
        elif period == self.PERIOD_QUARTERLY:
            start_week = get_first_week_quarter(start_week)
        elif period == self.PERIOD_YEARLY:
            start_week = get_first_week_year(start_week)

        number = Number.objects.get(id=number_id)
        response = {"number_id": number.id, "target_symbol": number.target_symbol,
                    "actual_symbol": number.actual_symbol, "description": number.description, "results": []}

        periodic_data = OrderedDict()

        weeks = get_weeks_between(start_week, end_week)

        all_periods = self.get_periods(str(start_week), end_week, period)

        kwargs = {"user": request.user, "week_index__gte": start_week,
                  "week_index__lte": end_week}

        all_numbers = Number.objects.filter().order_by("-weight")
        all_values = NumberValue.objects.filter(**kwargs).order_by("week_index")

        def find_week_values(w):
            v = []
            for value in all_values:
                if value.week_index == str(w):
                    v.append(value)
            return v

        for week in weeks:
            values = find_week_values(week)

            if hasattr(number, "value"):
                delattr(number, "value")

            calculate_week_number_value(request.user, number, week, all_numbers, values)

            val = number.value
            selector = self.get_period_lbl(week, period)
            # init dict
            if selector not in periodic_data:
                periodic_data[selector] = {"actual_value": 0, "target_value": 0}

            data = periodic_data[selector]

            if val.target_value is not None:
                data['target_value'] += float(val.target_value)

            if val.actual_value is not None:
                data['actual_value'] += float(val.actual_value)

        for key in all_periods:
            if key in periodic_data:
                data = periodic_data[key]
                response["results"].append(
                    {"target_value": data['target_value'], "actual_value": data['actual_value'], "x_value_name": key})
            else:
                response["results"].append(
                    {"target_value": None, "actual_value": None, "x_value_name": key})

        return HttpResponse(json.dumps(response), content_type="application/json")

    def get_periods(self, start_week, end_week, period):

        start_week = Week.fromstring(start_week)
        end_week = Week.fromstring(end_week)

        delta = end_week - start_week + 1
        labels = []

        for i in range(0, delta):
            week = start_week + i
            lbl = self.get_period_lbl(week, period)
            if lbl not in labels:
                labels.append(lbl)
        return labels

    def get_period_lbl(self, week, period):
        year = week.sunday().year
        quarter = get_quarter_num(week.sunday().month)

        selector = None
        if period == self.PERIOD_WEEKLY:
            selector = week.sunday().strftime(WEEK_DATE_FORMAT)
        elif period == self.PERIOD_MONTHLY:
            selector = week.sunday().strftime("%b %Y")
        elif period == self.PERIOD_QUARTERLY:
            selector = "Q{}, {}".format(quarter, year)
        elif period == self.PERIOD_YEARLY:
            selector = year
        return selector
