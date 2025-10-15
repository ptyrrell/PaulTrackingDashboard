import datetime
import logging

from django.core.management.base import BaseCommand

from apps.models import UserHistoryEvent

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        date = datetime.date.today() - datetime.timedelta(days=60)
        UserHistoryEvent.objects.filter(date_created__lte=date).delete()
