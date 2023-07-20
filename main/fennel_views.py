from django.shortcuts import get_object_or_404

from main.forms import SignalForm
from .models import Signal, Transaction, UserKeys, ConfirmationRecord
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


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_account(request):
    if UserKeys.objects.filter(user=request.user).exists():
        return Response(
            {
                "error": "user already has an account",
                "fix": "you can make other calls to /v1/fennel to get the address and balance",
            }
        )
    r = requests.get(f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account")
    mnemonic = r.json()["mnemonic"]
    user_keys = UserKeys.objects.get_or_create(user=request.user, mnemonic=mnemonic)
    return Response(mnemonic == user_keys.mnemonic)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_account_balance(request):
    if not UserKeys.objects.filter(user=request.user).exists():
        return Response(
            {
                "error": "user does not have an account",
                "fix": "call /v1/fennel/create_account first",
            }
        )
    key = UserKeys.objects.filter(user=request.user).first()
    try:
        payload = {"mnemonic": key.mnemonic}
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
            data=payload,
        )
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
    payload = {"mnemonic": key.mnemonic}
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address", data=payload
    )
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
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_transfer_token",
        data=payload,
    )
    Transaction.objects.create(
        function="transfer_token",
        payload_size=0,
        fee=r.json()["fee"],
    )
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
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token", data=payload
    )
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_new_signal(request):
    form = SignalForm(request.POST)
    mnemonic_from_database = UserKeys.objects.filter(user=request.user).first().mnemonic
    payload = {"mnemonic": mnemonic_from_database, "content": form.signal}
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
        data=payload,
    )
    Transaction.objects.create(
        function="send_new_signal",
        payload_size=len(form.signal),
        fee=r.json()["fee"],
    )
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_new_signal(request):
    form = SignalForm(request.POST)
    signal = Signal.objects.create(signal_text=form.signal, sender=request.user)
    try:
        payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
            "content": form.signal,
        }
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        signal.tx_hash = r.json()["hash"]
        signal.synced = True
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception as e:
        return Response({"signal": "saved as unsynced", "error": e.message})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_sync_signal(request):
    id = request.data["id"]
    signal = get_object_or_404(Signal, id=id)
    payload = {
        "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
        "content": signal.signal_text,
    }
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
        data=payload,
    )
    Transaction.objects.create(
        function="sync_signal",
        payload_size=len(signal.signal_text),
        fee=r.json()["fee"],
    )
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
            f"{os.environ.get('FENNEL_KEYSERVER_IP', None)}/api/keys?user={request.user.username}"
        )
        payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
            "content": signal.signal_text,
        }
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        signal.synced = True
        signal.tx_hash = r.json()["hash"]
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception as e:
        return Response({"signal": "saved as unsynced", "error": e.message})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def confirm_signal(request):
    signal = get_object_or_404(Signal, id=request.data["id"])
    ConfirmationRecord.objects.update_or_create(signal=signal, confirmer=request.user)
    return Response({"status": "ok"})


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    if count is not None:
        queryset = Signal.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Signal.objects.all().order_by("-timestamp")
    return Response(
        [
            {
                "id": signal.id,
                "tx_hash": signal.tx_hash,
                "timestamp": signal.timestamp,
                "mempool_timestamp": signal.mempool_timestamp,
                "signal_text": signal.signal_text,
                "sender": {
                    "id": signal.sender.id,
                    "username": signal.sender.username,
                    "address": UserKeys.objects.get(user=signal.sender).address,
                },
                "synced": signal.synced,
                "confirmations": [
                    {
                        "id": confirmation.id,
                        "timestamp": confirmation.timestamp,
                        "confirming_user": {
                            "id": confirmation.confirmer.id,
                            "username": confirmation.confirmer.username,
                        },
                    }
                    for confirmation in ConfirmationRecord.objects.filter(signal=signal)
                ],
            }
            for signal in queryset
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_unsynced_signals(request):
    return Response(
        [
            {
                "id": signal.id,
                "timestamp": signal.timestamp,
                "mempool_timestamp": signal.mempool_timestamp,
                "signal_text": signal.signal_text,
                "sender": {"id": signal.sender.id, "username": signal.sender.username},
                "synced": signal.synced,
            }
            for signal in Signal.objects.filter(sender=request.user, synced=False)
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_history(request, count=None):
    if count is not None:
        queryset = Transaction.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Transaction.objects.all().order_by("-timestamp")
    return Response(
        [
            {
                "timestamp": transaction.timestamp,
                "function": transaction.function,
                "payload_size": transaction.payload_size,
                "fee": transaction.fee,
            }
            for transaction in queryset
        ]
    )
