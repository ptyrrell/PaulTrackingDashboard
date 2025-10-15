import datetime
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import generic
from isoweek import Week

from apps.constants import DEFAULT_SEL_START_WEEK
from apps.models import Customer, FocusSheetValue
from apps.reports.utils import calculate_due_dates, FOCUS_STATUS_DUE, FOCUS_STATUS_UPDATED, FOCUS_STATUS_NOT_UPDATED, \
    FOCUS_STATUS_SUBMITTED
from apps.utils import get_weeks_range, format_week_name

NUM_WEEKS_AHEAD_OF_CURRENT = 4
UPDATE_DAYS = 3


def get_focus_sheet_status(focus_value=None):

    if not focus_value:

        if Week.thisweek().sunday() == datetime.date.today():
            return FOCUS_STATUS_DUE, 0

        return FOCUS_STATUS_NOT_UPDATED, 0

    goals = [focus_value.goal_1_achieved, focus_value.goal_2_achieved, focus_value.goal_3_achieved,
             focus_value.goal_4_achieved]

    goals_achieved = float(len([True for x in goals if x]))/len(goals) * 100.0

    status = FOCUS_STATUS_SUBMITTED

    if (focus_value.date_updated - focus_value.date_created).days > 3:
        status = FOCUS_STATUS_UPDATED

    return status, int(goals_achieved)


class FocusSheetForm(forms.ModelForm):
    """
    Focus sheet data input form
    """

    class Meta:
        model = FocusSheetValue
        exclude = ["user", "date_created", "date_updated"]


@method_decorator(login_required, name="dispatch")
class FocusSheetList(generic.ListView):
    """
    Focus sheet list
    """

    template_name = "focus-sheet/list.html"

    def get_queryset(self):
        return FocusSheetValue.objects.filter(user=self.request.user)


@login_required
def focus_sheet_input_view(request):
    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=NUM_WEEKS_AHEAD_OF_CURRENT)[::-1]
    week = Week.thisweek()

    form = FocusSheetForm()

    if request.method == "POST":
        form = FocusSheetForm(request.POST)

        if form.is_valid():
            focus_sheet_data = form.instance
            focus_sheet_data.user = request.user
            focus_sheet_data.save()

            return redirect(reverse("focus_sheet_list"))

    return render(request, "focus-sheet/form.html", {"weeks": weeks, "week": week, "form": form})


@login_required
def focus_sheet_edit_view(request, pk):
    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=NUM_WEEKS_AHEAD_OF_CURRENT)
    week = Week.thisweek()

    instance = FocusSheetValue.objects.get(id=pk, user=request.user)

    form = FocusSheetForm(instance=instance)

    if request.method == "POST":
        form = FocusSheetForm(request.POST, instance=instance)

        if form.is_valid():
            focus_sheet_data = form.instance
            focus_sheet_data.user = request.user
            focus_sheet_data.save()

            return redirect(reverse("focus_sheet_list"))

    return render(request, "focus-sheet/form.html", {"weeks": weeks[::-1], "week": week, "form": form, "update": True})


@login_required
def focus_sheet_admin_view(request):
    customers = []

    if request.method == "POST":
        week_index = request.POST.get("week")

        customers = Customer.objects.filter(user__is_active=True, coach__id=request.POST.get("coach")). \
            order_by("user__first_name")

        for customer in customers:
            customer.focus_data = calculate_due_dates(customer, week_index)
            customer.focus_data.update({"week": format_week_name(week_index)})

            try:
                focus_value = FocusSheetValue.objects.filter(user=customer.user, week_index=week_index).get()
            except Exception:
                focus_value = None

            focus_status, focus_goals_achieved = get_focus_sheet_status(focus_value)
            customer.focus_data.update({"focus_status": focus_status, "focus_goals_achieved": focus_goals_achieved})

    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=NUM_WEEKS_AHEAD_OF_CURRENT)
    week = Week.thisweek()

    user_model = get_user_model()

    coaches = user_model.objects.filter(Q(is_coach=True) | Q(is_supercoach=True))

    return render(request, "focus-sheet/coach-dashboard.html", {"weeks": weeks[::-1], "week": week, "coaches": coaches,
                                                                "customers": customers})
