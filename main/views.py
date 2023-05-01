from .models import Signal
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
import requests


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_account(request):
    r = requests.get("http://localhost:6060/create_account")
    mnemonic = r.json()["mnemonic"]
    r = requests.post(
        "http://localhost:1235/api/keys/",
        data={"user": request.user.username, "mnemonic": mnemonic},
    )
    if r.status_code != 200:
        return Response(r.json(), status=r.status_code)
    return Response(r.json()["mnemonic"] == mnemonic)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_account_balance(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    payload = {"mnemonic": r.json()[0]["mnemonic"]}
    r = requests.post("http://localhost:6060/get_account_balance", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_address(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    payload = {"mnemonic": r.json()[0]["mnemonic"]}
    r = requests.post("http://localhost:6060/get_address", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_transfer_token(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    payload = {
        "mnemonic": r.json()[0]["mnemonic"],
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    r = requests.post("http://localhost:6060/get_fee_for_transfer_token", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transfer_token(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    payload = {
        "mnemonic": r.json()[0]["mnemonic"],
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    r = requests.post("http://localhost:6060/transfer_token", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_new_signal(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    mnemonic_from_database = r.json()[0]["mnemonic"]
    payload = {"mnemonic": mnemonic_from_database, "content": request.data["content"]}
    r = requests.post("http://localhost:6060/get_fee_for_new_signal", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_new_signal(request):
    r = requests.get(
        "http://localhost:1235/api/keys?user={user}".format(user=request.user.username)
    )
    mnemonic_from_database = r.json()[0]["mnemonic"]
    Signal.objects.create(signal_text=request.data["content"])
    payload = {"mnemonic": mnemonic_from_database, "content": request.data["content"]}
    r = requests.post("http://localhost:6060/send_new_signal", data=payload)
    return Response(r.json())


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    if count is not None:
        queryset = Signal.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Signal.objects.all().order_by("-timestamp")
    return Response([{"content": signal.signal_text} for signal in queryset])


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signal_history(request):
    r = requests.get("http://localhost:6060/get_signal_history")
    return Response(r.json())
