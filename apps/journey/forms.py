
from datetime import datetime, date

from django.forms import (
    ChoiceField, FloatField, ModelForm, Select, BooleanField, ValidationError,
    Form)
from isoweek import Week

from apps.constants import (
    DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT, DEFAULT_SEL_START_WEEK)
from apps.models import GuaranteeEarnings, GuaranteeValue
from apps.utils import get_first_week_quarter, get_weeks_range

current_year = datetime.now().year

YEARS_RANGE = [x for x in range(current_year - 5, current_year + 5)]
YEAR_START_FROM = current_year - 1


def _get_range_choices(year_start, year_end):
    return [
        (date(x, y, 1).strftime('%Y-%m-%d'), date(x, y, 1).strftime('%b, %Y'))
        for x in range(year_start, year_end)
        for y in range(1, 13)
    ]


class GuaranteeYearField(ChoiceField):

    def __init__(self, *args, **kwargs):
        super().__init__(
            required=True,
            widget=Select(attrs={"class": "form-control"}),
            choices=[(str(x), x) for x in YEARS_RANGE],
            *args, **kwargs)


class GuaranteeValueForm(ModelForm):

    rev_1_year = FloatField(required=True, label="Revenue year 1")
    rev_2_year = FloatField(required=True, label="Revenue year 2")
    rev_3_year = FloatField(required=True, label="Revenue year 3")
    guarantee_val = FloatField(required=True, label="Guarantee # value")

    year_1_lbl = GuaranteeYearField()
    year_2_lbl = GuaranteeYearField()
    year_3_lbl = GuaranteeYearField()

    minimum_profit = FloatField(required=True, label="Revenue year 3")
    minimum_profit_year = GuaranteeYearField()

    next_range_start_date = ChoiceField(
        choices=_get_range_choices(YEAR_START_FROM, current_year + 1),
        widget=Select(attrs={"class": "form-control"}))

    next_range_end_date = ChoiceField(
        choices=_get_range_choices(YEAR_START_FROM, current_year + 2),
        widget=Select(attrs={"class": "form-control"}))

    is_archived = BooleanField(required=False, initial=False)

    def clean(self):
        data = self.cleaned_data

        start_date = data['next_range_start_date']
        end_date = data['next_range_end_date']

        if start_date and end_date and start_date >= end_date:
            raise ValidationError('Date range cannot end before it starts.')

    class Meta:
        model = GuaranteeValue
        exclude = ("user", "date_created", "date_updated", )


class GuaranteeEarningsForm(ModelForm):

    class Meta:
        model = GuaranteeEarnings
        exclude = ("user", "date", "date_created", "date_updated", )


class WeekRangeForm(Form):

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        this_week = Week.thisweek()

        weeks = get_weeks_range(
            DEFAULT_SEL_START_WEEK,
            num_of_weeks_ahead=DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT)

        week_choices = [(w, w.sunday().strftime('%B %d, %Y')) for w in weeks]

        self.fields['start_week'] = ChoiceField(
            initial=get_first_week_quarter(str(this_week)),
            choices=week_choices)

        self.fields['end_week'] = ChoiceField(
            initial=this_week + 24,
            choices=week_choices)
