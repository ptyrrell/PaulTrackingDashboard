import logging

from django.conf import settings
from django.contrib.auth import login as auth_login, logout
from django.shortcuts import HttpResponseRedirect, render
from django.views.generic import View

from .forms import LoginForm

logger = logging.getLogger(__name__)


class LoginView(View):

    def get(self, request):
        form = LoginForm(request)
        return render(request, "login.html", {"form": form, "re_captcha_site_key": settings.RE_CAPTCHA_SITE_KEY})

    def post(self, request):
        redirect_to = "/"
        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            #TODO: Ensure the user-originating redirection url is safe.
            auth_login(request, form.get_user())

            if form.cleaned_data["remember_me"]:
                # keeps session alive for two months
                request.session.set_expiry(60 * 60 * 24 * 30)

            return HttpResponseRedirect(redirect_to)
        else:
            logger.error("Bad login: {}".format(form.errors))
        return render(request, "login.html", {"form": form, "re_captcha_site_key": settings.RE_CAPTCHA_SITE_KEY})


class LogOutView(View):

    def get(self, request):
        logout(request)
        return HttpResponseRedirect("/")
