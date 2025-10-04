import os
from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from django.http import JsonResponse


def api_root(request):
    """API root endpoint - provides basic information about the Fennel API"""
    return JsonResponse({
        "message": "Welcome to Fennel API v1",
        "version": "v1.0.0-alpha.20",
        "documentation": "View available endpoints by navigating to this URL in a browser",
        "dashboard": "/api/dashboard/",
        "key_endpoints": {
            "version": "/api/v1/get_version/",
            "health": "/api/v1/healthcheck/",
            "create_account": "/api/v1/fennel/create_account/",
            "auth": {
                "register": "/api/v1/auth/register/",
                "login": "/api/v1/auth/login/"
            }
        },
        "note": "The API might take several minutes to run all tests and confirm full availability."
    })


@api_view(["GET"])
def get_version(request):
    return Response({"version": "v1.0.0-alpha.20"})


@api_view(["GET"])
def livecheck(request):
    response = requests.get(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/hello_there/", timeout=5
    )
    if response.status_code != 200:
        print("bitwise is unreachable")
        raise Http404
    response = requests.get(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/healthcheck",
        timeout=5,
    )
    if response.status_code != 200:
        print("subservice is unreachable.")
        raise Http404
    return Response()


@api_view(["GET"])
def healthcheck(request):
    return Response()


@api_view(["GET"])
def subservice_healthcheck(request):
    response = requests.get(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/healthcheck",
        timeout=5,
    )
    if response.status_code == 200:
        return Response("Ok")
    raise Http404
