from django.http import Http404
from rest_framework.decorators import (
    api_view,
)
from rest_framework.response import Response
import requests
import os


@api_view(["GET"])
def get_version(request):
    return Response({"version": "v1.0.0-alpha.6"})


@api_view(["GET"])
def healthcheck(request):
    return Response()


@api_view(["GET"])
def subservice_healthcheck(request):
    r = requests.get(f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/healthcheck")
    if r.status_code == 200:
        return Response("Ok")
    else:
        raise Http404
