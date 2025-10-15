import datetime
import logging

from apps.models import Customer, FocusSheetValue, CashFlowInOutValue, UserHistoryEvent
from apps.utils import send_html_mail
from django.template import loader

from django.core.management.base import BaseCommand
from isoweek import Week


logger = logging.getLogger(__name__)

# three days before
TYPE_THREE_DAYS = "Three Days Before"
# due day
TYPE_DUE = "Due Today"
# one day late
TYPE_LATE = "One Day Late"


class Command(BaseCommand):

    def handle(self, *args, **options):

        customers = Customer.objects.all()

        current_week = Week.thisweek()
        current_week_end = Week.thisweek().sunday()

        previous_week = (Week.thisweek() - 1)
        previous_week_end = previous_week.sunday()
        today = datetime.date.today()

        for customer in customers:

            # 3 days before
            if (current_week_end - today).days == 3:
                self._send_reminder(customer, current_week, TYPE_THREE_DAYS)

            # due date
            elif current_week_end == today:
                self._send_reminder(customer, current_week, TYPE_DUE)

            # one day late
            elif (today - previous_week_end).days == 1:
                self._send_reminder(customer, previous_week, TYPE_LATE)

    def _send_reminder(self, customer, current_week, mail_type=TYPE_THREE_DAYS):

        week_index = str(current_week)

        if not FocusSheetValue.objects.filter(user=customer.user, week_index=week_index).count():
            self._record_history_event(customer, "Reminder, {}, Focus Sheet, Week: {}".format(mail_type, current_week.sunday()))
            template = loader.get_template("emails/email_reminder_focus_sheet.html").render({"customer": customer})
            send_html_mail("Business Benchmark Group reminder", template, [customer.user.email])

        if not CashFlowInOutValue.objects.filter(flow__user=customer.user, week_index=week_index).count():
            self._record_history_event(customer, "Reminder, {}, Cashflow, Week: {}".format(mail_type, current_week.sunday()))
            template = loader.get_template("emails/email_reminder_cashflow.html").render({"customer": customer})
            send_html_mail("Business Benchmark Group reminder", template, [customer.user.email])

    def _record_history_event(self, customer, name):
        UserHistoryEvent.objects.create(user=customer.user, event_type="Email sent", event_name=name).save()
