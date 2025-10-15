import json
from django.views.generic import View
from django.http.response import HttpResponse


class FocusSheetApi(View):

    def get(self, request):
        return HttpResponse("Ok")


    def put(self, request):
        pass

