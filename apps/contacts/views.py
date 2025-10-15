import datetime
import hashlib

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views.generic import View

import settings
from apps.models import ContactsMessage
from apps.users.forms import ReCaptchaField
from apps.utils import send_html_mail


class ContactsForm(forms.Form):
    name = forms.CharField(label='Your name', max_length=100)
    email = forms.EmailField(label='Email', max_length=200)
    message = forms.CharField(label='Message', max_length=500)

    g_recaptcha_response = ReCaptchaField()


class ContactsPageView(View):

    def get(self, request):
        form = ContactsForm()
        return render(request, "contacts.html", {"form": form, "submitted": False,
                                                 "re_captcha_site_key": settings.RE_CAPTCHA_SITE_KEY})

    def post(self, request):
        form = ContactsForm(request.POST)
        if form.is_valid():
            name, email, message = form.cleaned_data["name"], form.cleaned_data["email"], form.cleaned_data["message"]

            md = hashlib.sha256()
            md.update(name.encode("utf-8") + email.encode("utf-8") + message.encode("utf-8"))
            hexhash = md.hexdigest()

            try:
                current = ContactsMessage.objects.get(hash=hexhash)
                if current:
                    return HttpResponseBadRequest()
            except ObjectDoesNotExist:
                pass

            message_obj = ContactsMessage.objects.create(name=name, email=email, hash=hexhash,
                                                         message=message, ip=request.META.get("HTTP_X_REAL_IP"))
            message_obj.save()

            form = ContactsForm()

            text = "{} ({}) says:<br><p> {} </p> <br>{}".format(name, email, message, datetime.datetime.utcnow())
            send_html_mail("Contact Us message from mybusinessbenchmark.com.au", text, settings.CONTACTS_EMAIL_SEND_TO)

            return render(request, "contacts.html", {"form": form, "submitted": True,
                                                     "re_captcha_site_key": settings.RE_CAPTCHA_SITE_KEY})
        else:
            return render(request, "contacts.html", {"form": form, "submitted": False,
                                                     "re_captcha_site_key": settings.RE_CAPTCHA_SITE_KEY})
