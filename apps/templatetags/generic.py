from django import template
from apps.reports.utils import FOCUS_STATUS_DUE, FOCUS_STATUS_SUBMITTED, FOCUS_STATUS_UPDATED


register = template.Library()


@register.filter(name="focus_status")
def focus_status(value):

    if value == FOCUS_STATUS_UPDATED:
        return "Updated"
    elif value == FOCUS_STATUS_SUBMITTED:
        return "Submitted"
    elif value == FOCUS_STATUS_DUE:
        return "Due"
    else:
        return "Not Updated"


@register.filter(name="focus_class")
def focus_class(value):

    if value == FOCUS_STATUS_UPDATED:
        return "focus-green"
    elif value == FOCUS_STATUS_SUBMITTED:
        return "focus-orange"
    elif value == FOCUS_STATUS_DUE:
        return "focus-blue"
    else:
        return "focus-red"
