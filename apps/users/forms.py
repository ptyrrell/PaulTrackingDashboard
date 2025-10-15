import json
import requests

from django import forms
from django.conf import settings
from django.contrib.auth.forms import AuthenticationForm


def re_captcha_valid(g_recaptcha_response):
    if isinstance(g_recaptcha_response, list):
        g_recaptcha_response = g_recaptcha_response[0]

    response = requests.post("https://www.google.com/recaptcha/api/siteverify",
                             data={"secret": settings.RE_CAPTCHA_SECRET, "response": g_recaptcha_response})
    data = json.loads(response.text)
    return data["success"]


class ReCaptchaWidget(forms.widgets.Widget):

    def value_from_datadict(self, data, files, name):
        return [data.get('g-recaptcha-response', None)]


class ReCaptchaField(forms.Field):

    widget = ReCaptchaWidget

    def validate(self, value):
        if settings.RE_CAPTCHA_ENABLED:
            if not re_captcha_valid(value):
                raise forms.ValidationError("Incorrect value has been entered")


class LoginForm(AuthenticationForm):
    g_recaptcha_response = ReCaptchaField()

    remember_me = forms.BooleanField(widget=forms.CheckboxInput, required=False)
