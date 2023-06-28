from django.shortcuts import get_object_or_404
from .models import Signal, UserKeys
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
import requests
import os
import datetime


@api_view(["GET"])
def healthcheck(request):
    return Response()


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_account(request):
    if UserKeys.objects.filter(user=request.user).exists():
        return Response({
            "error": "user already has an account",
            "fix": "you can make other calls to /v1/fennel to get the address and balance"
        })
    r = requests.get(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/create_account")
    mnemonic = r.json()["mnemonic"]
    user_keys = UserKeys.objects.get_or_create(user=request.user, mnemonic=mnemonic)
    return Response(mnemonic == user_keys.mnemonic)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_account_balance(request):
    if not UserKeys.objects.filter(user=request.user).exists():
        return Response({
            "error": "user does not have an account",
            "fix": "call /v1/fennel/create_account first"
        })
    key = UserKeys.objects.filter(user=request.user).first()
    try:
        payload = key.mnemonic
        r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/get_account_balance", data=payload)
        key.balance = r.json()["balance"]
        key.save()
        return Response(r.json())
    except Exception:
        return Response({"balance": key.balance})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_address(request):
    key = UserKeys.objects.filter(user=request.user).first()
    if key.address:
        return Response({"address": key.address})
    payload = key.mnemonic
    r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/get_address", data=payload)
    key.address = r.json()["address"]
    key.save()
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_transfer_token(request):
    payload = {
        "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/get_fee_for_transfer_token", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def transfer_token(request):
    payload = {
        "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/transfer_token", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_new_signal(request):
    mnemonic_from_database = UserKeys.objects.filter(user=request.user).first().mnemonic
    payload = {
            "mnemonic": mnemonic_from_database,
            "content": request.data["content"]
    }
    r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/get_fee_for_new_signal", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_new_signal(request):
    signal = Signal.objects.create(signal_text=request.data["content"], sender=request.user)
    try:
        payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
            "content": request.data["content"]
        }
        r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/send_new_signal", data=payload)
        signal.synced = True
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception as e:
        return Response({"signal": "saved as unsynced", "error": str(e)})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_sync_signal(request):
    id = request.data["id"]
    signal = get_object_or_404(Signal, id=id)
    payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
            "content": signal.signal_text
    }
    r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/get_fee_for_new_signal", data=payload)
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def sync_signal(request):
    id = request.data["id"]
    signal = get_object_or_404(Signal, id=id)
    if signal.sender != request.user:
        return Response({"error": "sender is not current user"})
    try:
        r = requests.get(
            f"http://{os.environ.get('FENNEL_KEYSERVER_IP', None)}:6060/api/keys?user={request.user.username}"
        )
        payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic, 
            "content": signal.signal_text
        }
        r = requests.post(f"http://{os.environ.get('FENNEL_SUBSERVICE_IP', None)}:6060/send_new_signal", data=payload)
        signal.synced = True
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception as e:
        return Response({"signal": "saved as unsynced", "error": str(e)})


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    if count is not None:
        queryset = Signal.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Signal.objects.all().order_by("-timestamp")
    return Response(queryset)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signal_history(request):
    return Response(Signal.objects.all().order_by("-timestamp"))


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_unsynced_signals(request):
    return Response(Signal.objects.filter(sender=request.user, synced=False))
