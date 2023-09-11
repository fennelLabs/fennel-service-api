import os
import datetime
from django.db import DataError

from django.shortcuts import get_object_or_404

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication

import requests
from main.decorators import requires_mnemonic_created

from main.forms import SignalForm
from main.models import (
    Signal,
    Transaction,
    UserKeys,
    ConfirmationRecord,
)
from main.serializers import SignalSerializer, TransactionSerializer


def record_signal_fee(payload: dict) -> (dict, bool):
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
        data=payload,
        timeout=5,
    )
    try:
        Transaction.objects.create(
            function="send_new_signal",
            payload_size=len(payload["content"]),
            fee=response.json()["fee"],
        )
    except DataError:
        return {
            "error": "could not record transaction",
            "content": payload["content"],
            "content_length": len(payload["content"]),
            "fee": response.json()["fee"],
        }, False
    return response.json(), True


def check_balance(key):
    try:
        payload = {"mnemonic": key.mnemonic}
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_account_balance",
            data=payload,
            timeout=5,
        )
        key.balance = response.json()["balance"]
        key.save()
        return response.json()
    except requests.HTTPError:
        return {"balance": key.balance}


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
                },
                status=400,
            )
        keys = UserKeys.objects.get(user=request.user)
    else:
        keys = UserKeys.objects.create(user=request.user)
    response = requests.get(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account",
        timeout=5,
    )
    mnemonic = response.json()["mnemonic"]
    keys.mnemonic = mnemonic
    keys.save()
    return Response(mnemonic == keys.mnemonic)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def download_account_as_json(request):
    key = UserKeys.objects.filter(user=request.user).first()
    try:
        payload = {"mnemonic": key.mnemonic}
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/download_account_as_json",
            data=payload,
            timeout=5,
        )
        return Response(response.json())
    except requests.HTTPError:
        return Response({"error": "could not get account json"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_account_balance(request):
    key = UserKeys.objects.filter(user=request.user).first()
    return Response(check_balance(key))


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_address(request):
    key = UserKeys.objects.filter(user=request.user).first()
    if key.address:
        return Response({"address": key.address})
    payload = {"mnemonic": key.mnemonic}
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address",
        data=payload,
        timeout=5,
    )
    key.address = response.json()["address"]
    key.save()
    return Response(response.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_transfer_token(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_transfer_token",
        data=payload,
        timeout=5,
    )
    Transaction.objects.create(
        function="transfer_token",
        payload_size=0,
        fee=response.json()["fee"],
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def transfer_token(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "to": request.data["to"],
        "amount": request.data["amount"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token",
        data=payload,
        timeout=5,
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_new_signal(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    form = SignalForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())}, status=400)
    mnemonic_from_database = user_key.mnemonic
    payload = {
        "mnemonic": mnemonic_from_database,
        "content": form.cleaned_data["signal"],
    }
    try:
        response, success = record_signal_fee(payload)
        code = 400 if not success else 200
        response["balance"] = check_balance(user_key)["balance"]
        return Response(response, status=code)
    except requests.HTTPError:
        return Response({"error": "could not get fee"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def send_new_signal(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    form = SignalForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())}, status=400)
    signal = Signal.objects.create(
        signal_text=form.cleaned_data["signal"], sender=request.user
    )
    mnemonic = user_key.mnemonic
    try:
        payload = {
            "mnemonic": mnemonic,
            "content": form.cleaned_data["signal"],
        }
        old_balance = int(check_balance(user_key)["balance"])
        signal_fee_result, success = record_signal_fee(payload)
        if signal_fee_result["fee"] > old_balance or old_balance == 0:
            return Response(
                {
                    "error": "insufficient balance",
                    "balance": check_balance(user_key)["balance"],
                    "fee": signal_fee_result["fee"],
                    "signal_id": signal.id,
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "synced": False,
                },
                status=400,
            )
        if not success:
            return Response(signal_fee_result, status=400)
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
            timeout=5,
        )
        if not "hash" in response.json():
            return Response(
                {
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "signal_id": signal.id,
                    "balance": check_balance(user_key)["balance"],
                    "synced": False,
                }
            )
        signal.tx_hash = response.json()["hash"]
        signal.synced = True
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        response_json = response.json()
        response_json["balance"] = check_balance(user_key)["balance"]
        response_json["signal_id"] = signal.id
        response_json["synced"] = True
        return Response(response_json)
    except requests.HTTPError:
        return Response(
            {
                "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                "signal_id": signal.id,
                "balance": check_balance(user_key)["balance"],
                "synced": False,
            }
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_sync_signal(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    signal_id = request.data["id"]
    signal = get_object_or_404(Signal, id=signal_id)
    payload = {
        "mnemonic": user_key.mnemonic,
        "content": signal.signal_text,
    }
    response, success = record_signal_fee(payload)
    code = 400 if not success else 200
    response["balance"] = check_balance(user_key)["balance"]
    return Response(response, status=code)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def sync_signal(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    signal_id = request.data["id"]
    signal = get_object_or_404(Signal, id=signal_id)
    if signal.sender != request.user:
        return Response({"error": "sender is not current user"}, status=400)
    mnemonic = user_key.mnemonic
    try:
        payload = {
            "mnemonic": mnemonic,
            "content": signal.signal_text,
        }
        signal_fee_result, success = record_signal_fee(payload)
        old_balance = int(check_balance(user_key)["balance"])
        if signal_fee_result["fee"] > old_balance or old_balance == 0:
            return Response(
                {
                    "error": "insufficient balance",
                    "balance": check_balance(user_key)["balance"],
                    "fee": signal_fee_result["fee"],
                    "signal_id": signal.id,
                    "synced": False,
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                },
                status=400,
            )
        if not success:
            return Response(signal_fee_result, status=400)
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
            timeout=5,
        )
        if not response.json()["hash"]:
            return Response(
                {
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "balance": check_balance(user_key)["balance"],
                    "signal_id": signal.id,
                    "synced": False,
                }
            )
        signal.synced = True
        signal.tx_hash = response.json()["hash"]
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        response_json = response.json()
        response_json["balance"] = check_balance(user_key)["balance"]
        return Response(response_json)
    except requests.HTTPError:
        return Response(
            {
                "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                "balance": check_balance(user_key)["balance"],
                "signal_id": signal.id,
                "synced": False,
            }
        )


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
def get_signal_by_id(request, signal_id):
    signal = get_object_or_404(Signal, id=signal_id)
    serializer = SignalSerializer(signal)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    if count is not None:
        queryset = Signal.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Signal.objects.all().order_by("-timestamp")
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_unsynced_signals(request):
    queryset = Signal.objects.filter(sender=request.user, synced=False)
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_fee_history(request, count=None):
    if count is not None:
        queryset = Transaction.objects.all().order_by("-timestamp")[:count]
    else:
        queryset = Transaction.objects.all().order_by("-timestamp")
    serializer = TransactionSerializer(queryset, many=True)
    return Response(serializer.data)
