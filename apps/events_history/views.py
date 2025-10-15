from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.models import Customer, UserHistoryEvent


@login_required
def history_view(request):

    if request.user.is_superuser or request.user.is_staff:
        active_customers = Customer.objects.filter(user__is_active=True).order_by("user__first_name")

    elif request.user.is_coach or request.user.is_supercoach:
        active_customers = Customer.objects.filter(user__is_active=True, coach__id=request.user.id).order_by("user__first_name")

    events = []

    if request.method == "POST":
        customer = list(filter(lambda x: str(x.id) == request.POST.get("customer_id"), active_customers)).pop()
        events = UserHistoryEvent.objects.filter(user=customer.user).order_by("date_created")

    return render(request, "events_history.html", {"customers": active_customers, "events": events})
