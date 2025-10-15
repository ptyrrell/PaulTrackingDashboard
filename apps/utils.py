import datetime
import threading
from django.core.mail import EmailMessage
from isoweek import Week

import settings
from .constants import WEEK_DATE_FORMAT

QUARTERS = ((1, 2, 3,), (4, 5, 6,), (7, 8, 9,), (10, 11, 12,))


def get_first_week_month(week):
    """

    :param week:
    :return:
    """
    week = Week.fromstring(week)
    month = week.sunday().month

    prev = [week - i for i in range(5, 0, -1)] + [week]
    for w in prev:
        if w.sunday().month == month:
            return w


def get_quarter_num(month):
    quarter = 1

    q1, q2, q3, q4 = QUARTERS
    if month in q1:
        quarter = 1
    elif month in q2:
        quarter = 2
    elif month in q3:
        quarter = 3
    elif month in q4:
        quarter = 4
    return quarter


def get_first_week_quarter(week):
    """
    """
    week = Week.fromstring(week)
    month = week.sunday().month

    quarter = None

    weeks = []

    # Get quarter
    for q in QUARTERS:
        for m in q:
            if m == month:
                quarter = q
                break
    first = quarter[0]
    prev = [week - i for i in range(20, 0, -1)] + [week]

    for w in prev:
        if w.sunday().month == first:
            weeks.append(w)

    return min(weeks)


def get_first_week_year(week):
    """
    """
    week = Week.fromstring(week)
    weeks = Week.weeks_of_year(week.sunday().year)
    w = next(weeks)
    return w


def get_weeks_range(start_week, num_of_weeks_ahead=12, include_current=False):

    if not isinstance(start_week, Week):
        start_week = Week.fromstring(start_week)

    diff = Week.thisweek() - start_week + num_of_weeks_ahead
    range_start = 0 if include_current else 1

    weeks = list()
    for i in range(range_start, diff):
        weeks.append(start_week + i)
    return weeks


def get_weeks_between(start, end):
    if not isinstance(start, Week):
        start = Week.fromstring(start)

    if not isinstance(end, Week):
        end = Week.fromstring(end)
    diff = end - start
    weeks = list()
    for i in range(0, diff + 1):
        weeks.append(start + i)
    return weeks


def get_weeks_from(start_week, number_of_weeks_ahead):

    if not isinstance(start_week, Week):
        start_week = Week.fromstring(start_week)

    weeks = [start_week]
    for i in range(1, number_of_weeks_ahead):
        weeks.append(start_week + i)
    return weeks


def get_first_date_of_current_quarter():
    quarter = (datetime.datetime.now().month - 1)//3 + 1
    return quarter


def get_first_month_of_quarter(quarter):
    m = {1: 1, 2: 4, 3: 7, 4: 10}
    return m[quarter]


def format_week_name(week_index):
    return str(Week.fromstring(week_index).sunday().strftime(WEEK_DATE_FORMAT))


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run(self):
        msg = EmailMessage(self.subject, self.html_content, settings.DEFAULT_EMAIL_FROM, self.recipient_list)
        msg.content_subtype = "html"
        msg.send()


def send_html_mail(subject, html_content, recipient_list):
    EmailThread(subject, html_content, recipient_list).start()
