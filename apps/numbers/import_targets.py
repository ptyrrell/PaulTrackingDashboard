import json

from apps.constants import WEEK_DATE_FORMAT
from apps.models import NumberValue
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from isoweek import Week


@login_required
def import_targets(request, start_week, from_week, to_week):

    start_week = Week.fromstring(start_week)
    from_week = Week.fromstring(from_week)
    to_week = Week.fromstring(to_week)

    if to_week < from_week:
        # From week can't be greater than to
        return HttpResponse(status=400)

    diff = [from_week + i for i in range(0, (to_week - from_week + 1))]

    for w in diff:
        _week_import(request.user, start_week, w)

    _w = lambda w: w.sunday().strftime(WEEK_DATE_FORMAT)
    result = json.dumps({"start": _w(start_week), "from": _w(from_week),
                         "to": _w(to_week)})

    return HttpResponse(result, content_type="application/json")


def _week_import(user, from_week, to_week):

    values = NumberValue.objects.filter(week_index=str(from_week), user=user, number__is_target_formula=False)

    for val in values:
        try:
            record = NumberValue.objects.get(week_index=str(to_week), number=val.number, user=user)
        except ObjectDoesNotExist:
            record = NumberValue.objects.create(week_index=str(to_week), number=val.number, user=user)

        record.target_value = val.target_value
        record.save()
