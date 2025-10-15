import logging

from apps.models import Customer
from apps.reports.utils import calculate_week_report_completion
from apps.utils import send_html_mail
from django.core.management.base import BaseCommand
from django.template import loader
from isoweek import Week


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        customers = Customer.objects.filter(user__is_active=True)
        week = str(Week.thisweek())

        for customer in customers:
            rate = calculate_week_report_completion(customer, week)
            if rate < 10:
                template = loader.get_template("email_completion_alert.html").render({"customer": customer})
                send_html_mail("Business Benchmark Group reminder", template, [customer.user.email])
                logger.debug("Send completion alert email to {} for {}".format(customer.user.email, week))
