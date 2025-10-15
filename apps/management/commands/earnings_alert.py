import datetime
import logging

from apps.models import Customer, GuaranteeEarnings
from apps.utils import (
    get_first_date_of_current_quarter,
    get_first_month_of_quarter,
    send_html_mail,
)
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.template import loader


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):

        current_date = datetime.date(datetime.datetime.now().year,
                                     get_first_month_of_quarter(get_first_date_of_current_quarter()), 1)

        customers = Customer.objects.all()
        for customer in customers:
            if customer.coach:

                try:
                    GuaranteeEarnings.objects.get(user=customer.user, date=current_date)
                except ObjectDoesNotExist:

                    # sending notification to coach
                    template = loader.get_template("email_earnings_alert.html").render({"customer": customer})
                    send_html_mail("Business Benchmark Group reminder", template, [customer.coach.email])
                    logger.debug("Send earnings alert email to coach {} for customer {} for date {}".format(
                        customer.coach.email, customer.user.email, current_date))
