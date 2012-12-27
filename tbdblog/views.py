from django.http import HttpResponse
from django.shortcuts import render_to_response

from tbdblog.models import Error


def error_detail(request, error_id):
    eo = Error.objects.get(id=error_id)
    return HttpResponse(eo.traceback_html)
