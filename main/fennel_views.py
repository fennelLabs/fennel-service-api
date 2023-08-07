import ast
import json
from django.shortcuts import get_object_or_404
from main.decorators import subject_to_api_limit

from main.forms import SignalForm
from main.secret_key_utils import reconstruct_mnemonic, split_mnemonic
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


def __record_signal_fee(payload: dict) -> dict:
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
        data=payload,
    )
    Transaction.objects.create(
        function="send_new_signal",
        payload_size=len(payload["content"]),
        fee=r.json()["fee"],
    )
    return r.json()


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def create_account(request):
    if UserKeys.objects.filter(user=request.user).exists():
        if UserKeys.objects.get(user=request.user).mnemonic:
            return Response(
                {
                    "error": "user already has an account",
                    "fix": "you can make other calls to /v1/fennel to get the address and balance",
                }
            )
        else:
            keys = UserKeys.objects.get(user=request.user)
    else:
        keys = UserKeys.objects.create(user=request.user)
    r = requests.get(f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account")
    mnemonic = r.json()["mnemonic"]
    keys.mnemonic = mnemonic
    keys.save()
    return Response(mnemonic == keys.mnemonic)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
def create_self_custodial_account(request):
    if UserKeys.objects.filter(user=request.user).exists():
        if UserKeys.objects.get(user=request.user).mnemonic:
            return Response(
                {
                    "error": "user already has an account",
                }
            )
        else:
            keys = UserKeys.objects.get(user=request.user)
    else:
        keys = UserKeys.objects.create(user=request.user)
    r = requests.get(f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account")
    mnemonic = r.json()["mnemonic"]
    key_shards = split_mnemonic(mnemonic)
    keys.key_shard = str(key_shards[1])
    keys.save()
    return Response(
        {
            "user_shard": str(key_shards[0]).encode("utf-8").hex(),
            "recovery_shard": str(key_shards[2]).encode("utf-8").hex(),
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
def reconstruct_self_custodial_account(request):
    keys = get_object_or_404(UserKeys, user=request.user)
    key_shards = [
        ast.literal_eval(keys.key_shard),
        ast.literal_eval(bytes.fromhex(request.data["user_shard"]).decode("utf-8")),
    ]
    mnemonic = reconstruct_mnemonic(key_shards)
    return Response(
        {
            "mnemonic": mnemonic,
        }
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
def get_self_custodial_account_address(request):
    payload = {"mnemonic": request.data["mnemonic"]}
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address", data=payload
    )
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
def download_self_custodial_account_as_json(request):
    keys = get_object_or_404(UserKeys, user=request.user)
    key_shards = [
        ast.literal_eval(keys.key_shard),
        ast.literal_eval(request.data["user_shard"]),
    ]
    mnemonic = reconstruct_mnemonic(key_shards)
    try:
        payload = {"mnemonic": mnemonic}
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/download_account_as_json",
            data=payload,
        )
        return Response(r.json())
    except Exception:
        return Response({"error": "could not get account json"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def download_account_as_json(request):
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
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/download_account_as_json",
            data=payload,
        )
        return Response(r.json())
    except Exception:
        return Response({"error": "could not get account json"})


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
    if not payload["mnemonic"]:
        return Response({"error": "user does not have a blockchain account"})
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
    if not payload["mnemonic"]:
        return Response({"error": "user does not have a blockchain account"})
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token", data=payload
    )
    return Response(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_for_new_signal(request):
    form = SignalForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())})
    mnemonic_from_database = UserKeys.objects.filter(user=request.user).first().mnemonic
    if not mnemonic_from_database:
        return Response({"error": "user does not have a blockchain account"})
    payload = {
        "mnemonic": mnemonic_from_database,
        "content": form.cleaned_data["signal"],
    }
    try:
        response = __record_signal_fee(payload)
        return Response(response)
    except Exception:
        return Response({"error": "could not get fee"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_new_signal(request):
    form = SignalForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())})
    signal = Signal.objects.create(
        signal_text=form.cleaned_data["signal"], sender=request.user
    )
    try:
        payload = {
            "mnemonic": UserKeys.objects.filter(user=request.user).first().mnemonic,
            "content": form.cleaned_data["signal"],
        }
        if not payload["mnemonic"]:
            return Response({"error": "user does not have a blockchain account"})
        __record_signal_fee(payload)
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        signal.tx_hash = r.json()["hash"]
        signal.synced = True
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception:
        return Response({"signal": "saved as unsynced"})


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
    if not payload["mnemonic"]:
        return Response({"error": "user does not have a blockchain account"})
    response = __record_signal_fee(payload)
    return Response(response)


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
        if not payload["mnemonic"]:
            return Response({"error": "user does not have a blockchain account"})
        __record_signal_fee(payload)
        r = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        signal.synced = True
        signal.tx_hash = r.json()["hash"]
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        return Response(r.json())
    except Exception:
        return Response({"signal": "saved as unsynced"})


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
