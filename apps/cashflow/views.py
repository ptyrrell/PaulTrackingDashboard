import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from isoweek import Week

from apps.utils import get_weeks_between
from .utils import (
    can_edit_cashflow
)


@login_required
def cashflow_view(request):
    edit_cashflow = can_edit_cashflow(request)

    start_week = Week.thisweek()
    default_start_week = Week.withdate(datetime.date(2018, 7, 1))
    default_end_week = Week.thisweek() + 52
    end_week = Week.thisweek() + 13

    all_weeks = get_weeks_between(default_start_week, default_end_week)

    return render(request, "cashflow.html", {"weeks": all_weeks,
                                             "start_week": start_week,
                                             "end_week": end_week,
                                             "can_edit_cashflow": edit_cashflow})
