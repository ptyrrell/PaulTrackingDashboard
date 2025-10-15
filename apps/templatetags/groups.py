from apps.models import Customer
from apps.permissions import is_coach, is_supercoach
from django import template
from django.core.exceptions import ObjectDoesNotExist


register = template.Library()


@register.filter(name='is_manager')
def is_manager(user):
    if not user:
        return False
    return user.is_coach


@register.filter(name="is_supercoach")
def is_supercoach_tag(user):
    return is_supercoach(user)


@register.filter(name="is_coach")
def is_coach_tag(user):
    return is_coach(user)


@register.filter(name="can_edit_target")
def can_edit_target(user):
    if is_manager(user):
        return True

    try:
        customer = Customer.objects.get(user=user)
        return customer.can_edit_target
    except ObjectDoesNotExist:
        return False


@register.filter(name="can_edit_cashflow")
def can_edit_cashflowt(user):
    if is_manager(user):
        return True

    try:
        customer = Customer.objects.get(user=user)
        return customer.can_edit_cashflow
    except ObjectDoesNotExist:
        return False
