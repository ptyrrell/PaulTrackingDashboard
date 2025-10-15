import settings
from apps.constants import (
    DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT,
    DEFAULT_SEL_START_WEEK,
    DEFAULT_WEEKS_TARGET_IMPORT,
)
from apps.models import Number
from apps.numbers import read_week_numbers
from apps.utils import get_first_week_quarter, get_weeks_range, send_html_mail
from django.contrib.auth import decorators, get_user_model, logout
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import password_reset_confirm
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import HttpResponseRedirect, render
from django.template import Context, loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from isoweek import Week


def index(request):
    return render(request, "index.html")


@decorators.login_required
def numbers(request):

    w = request.COOKIES.get("numbers_week")
    default_week = Week.thisweek()

    if w:
        default_week = Week.fromstring(w)

    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT)

    numbers = read_week_numbers(request.user, default_week)

    chart_end_default_week = Week.thisweek() + 24
    chart_end_weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT)

    chart_default_week = get_first_week_quarter(str(Week.thisweek()))
    chart_numbers = Number.objects.filter(number_type=Number.TYPE_FLOAT).order_by("-weight")

    return render(request, "numbers.html",
                  # arguments
                  {"week": default_week, "numbers": numbers, "weeks": weeks, "chart_numbers": chart_numbers,
                   "chart_default_week": chart_default_week, "chart_end_default_week": chart_end_default_week,
                   "chart_end_weeks": chart_end_weeks})


@decorators.login_required
def targets(request):

    w = request.COOKIES.get("targets_week")
    default_week = Week.thisweek()

    if w:
        default_week = Week.fromstring(w)

    numbers = read_week_numbers(request.user, Week.thisweek())
    weeks = get_weeks_range(DEFAULT_SEL_START_WEEK, num_of_weeks_ahead=DEFAULT_NUM_WEEKS_AHEAD_OF_CURRENT)
    from_week = default_week + 1
    to_week = default_week + DEFAULT_WEEKS_TARGET_IMPORT

    return render(request, "targets.html",
                  # arguments
                  {"week": default_week, "weeks": weeks, "numbers": numbers,
                   "from_week": from_week, "to_week": to_week}
    )


def pages(request, page_name=None):
    if page_name is None:
        page_name = "index"

    return render(request, "{}.html".format(page_name))


def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/")


class PasswordForgotForm(PasswordResetForm):

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None):
        pass


def password_reset_confirm_view(request, uidb36=None, token=None):
    return password_reset_confirm(request, template_name='password_reset/reset_confirm.html',
        uidb64=uidb36, token=token, post_reset_redirect=reverse('login'))


def password_reset_view(request):

    if request.method == "POST":
        form = PasswordForgotForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"]
            user_model = get_user_model()

            try:
                user = user_model._default_manager.get(email__iexact=email, is_active=True)
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse("login"))

            if not user.has_usable_password():
                return HttpResponseRedirect(reverse("login"))

            subject = "{} - Password Reset".format(settings.DEFAULT_SITE_NAME)
            kwargs = {
                'email': user.email,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': default_token_generator.make_token(user),
                'domain': settings.DEFAULT_DOMAIN_NAME,
                'protocol': 'https'
            }
            ctx = Context(kwargs)
            template = loader.get_template("password_reset/reset_email.html").render(ctx)

            send_html_mail(subject, template, [email])
            return render(request, "password_reset/reset.html", {"form": PasswordResetForm(), "success": True})
    else:
        form = PasswordForgotForm()
        return render(request, "password_reset/reset.html", {"form": form, "success": False})
