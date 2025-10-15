
import logging

from datetime import datetime
from isoweek import Week

from django.http import (
    JsonResponse, HttpResponseForbidden, HttpResponseBadRequest)
from django.views.generic import View

from apps.models import GuaranteeValue, Number, NumberValue, GuaranteeEarnings
from apps.journey.forms import WeekRangeForm
from apps.constants import (
    ROUND_DECIMAL_DIGITS, WEEK_DATE_FORMAT, QUARTER_FORMAT)
from apps.utils import get_weeks_between


logger = logging.getLogger(__name__)


TOTAL_WEEKS_DIFF_NUMBER = 46


class JourneyChart(View):

    http_method_names = ['get']

    def get(self, request):

        if not request.user.is_authenticated():
            logger.error('Not allowed to access NumbersChart.get')
            return HttpResponseForbidden()

        form = WeekRangeForm(request.GET)

        if not form.is_valid():
            return HttpResponseBadRequest('Invalid data')

        try:
            instance = GuaranteeValue.objects.get(
                user=request.user,
                is_archived=False,
                next_range_start_date__isnull=False,
                next_range_end_date__isnull=False)
        except GuaranteeValue.DoesNotExist:
            return JsonResponse({})

        week_start = Week.fromstring(form.cleaned_data['start_week'])
        week_end = Week.fromstring(form.cleaned_data['end_week'])

        range_start, range_end = week_start.sunday(), week_end.sunday()

        range_weeks = get_weeks_between(
            Week.withdate(range_start), Week.withdate(range_end))

        average_per_week = round(
            instance.target_revenue / TOTAL_WEEKS_DIFF_NUMBER,
            ROUND_DECIMAL_DIGITS)

        revenue_values = NumberValue.objects.filter(
            number=Number.objects.get(number_index='N_WEEK_SALES'),
            user=request.user,
            week_index__gte=week_start,
            week_index__lte=week_end)

        actuals = []

        for week in range_weeks:
            for value in revenue_values:
                if value.week_index == str(week) and value.actual_value:
                    actuals.append(
                        round(float(value.actual_value), ROUND_DECIMAL_DIGITS))
                    break
            else:
                actuals.append(0)

        targets = [average_per_week] * len(range_weeks)

        assert len(actuals) == len(targets) == len(range_weeks), \
            'Bad mismatch values len, guarantee chart'

        return JsonResponse({
            'targets': targets,
            'actuals': actuals,
            'weeks': [
                week.sunday().strftime(WEEK_DATE_FORMAT)
                for week in range_weeks
            ]
        })


class EarningsChart(View):

    http_method_names = ['get']

    def get(self, request):

        if not request.user.is_authenticated():
            logger.error('Not allowed to access NumbersChart.get')
            return HttpResponseForbidden()

        try:
            start_date = datetime.strptime(
                request.GET.get('start_quarter'), QUARTER_FORMAT).date()
            end_date = datetime.strptime(
                request.GET.get('end_quarter'), QUARTER_FORMAT).date()
        except (ValueError, TypeError):
            return HttpResponseBadRequest('Invalid data')

        earnings = GuaranteeEarnings.objects.filter(
            user=request.user, date__gte=start_date, date__lt=end_date
        ).order_by('date')

        return JsonResponse({
            'retained_earnings': [e.retained_earnings for e in earnings],
            'current_earnings': [e.current_earnings for e in earnings],
            'weeks': [str(e.date) for e in earnings]
        })
