import os
import datetime

from django.db import DataError
from django.db.models import Q

from django.shortcuts import get_object_or_404

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from silk.profiling.profiler import silk_profile

from knox.auth import TokenAuthentication

import requests

from main.decorators import requires_mnemonic_created
from main.forms import SignalForm
from main.models import (
    APIGroup,
    Signal,
    Transaction,
    UserKeys,
    ConfirmationRecord,
)
from main.serializers import SignalSerializer, TransactionSerializer


@silk_profile(name="record_signal_fee")
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
            "fee": int(response.json()["fee"]),
        }, False
    return response.json(), True


@silk_profile(name="check_balance")
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
        return {"balance": int(key.balance)}
    except requests.HTTPError:
        return {"balance": int(key.balance)}


@silk_profile(name="signal_send_helper")
def signal_send_helper(user_key: UserKeys, signal: Signal) -> (dict, bool):
    try:
        payload = {
            "mnemonic": user_key.mnemonic,
            "content": signal.signal_text,
        }
        signal_fee_result, success = record_signal_fee(payload)
        old_balance = int(check_balance(user_key)["balance"])
        if signal_fee_result["fee"] > old_balance or old_balance == 0:
            return (
                {
                    "error": "insufficient balance",
                    "balance": check_balance(user_key)["balance"],
                    "fee": signal_fee_result["fee"],
                    "signal_id": signal.id,
                    "synced": False,
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                },
                False,
            )
        if not success:
            return (signal_fee_result, False)
        response_json = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
            timeout=5,
        ).json()
        if "hash" not in response_json:
            return (
                {
                    "error": "hash couldn't be retrieved from the chain",
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "fee": signal_fee_result["fee"],
                    "balance": check_balance(user_key)["balance"],
                    "signal_id": signal.id,
                    "synced": False,
                },
                False,
            )
        signal.synced = True
        signal.tx_hash = response_json["hash"][2:]
        signal.mempool_timestamp = datetime.datetime.now()
        signal.save()
        response_json["balance"] = check_balance(user_key)["balance"]
        response_json["signal_id"] = signal.id
        response_json["synced"] = True
        return response_json, True
    except requests.HTTPError:
        return (
            {
                "error": "subservice was unavailable",
                "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                "fee": signal_fee_result["fee"],
                "balance": check_balance(user_key)["balance"],
                "signal_id": signal.id,
                "synced": False,
            },
            False,
        )


@silk_profile(name="create_account")
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


@silk_profile(name="download_account_as_json")
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


@silk_profile(name="get_account_balance")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_account_balance(request):
    key = UserKeys.objects.filter(user=request.user).first()
    response = check_balance(key)
    response["balance"] = int(response["balance"])
    return Response(response)


@silk_profile(name="get_address")
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


@silk_profile(name="get_fee_for_transfer_token")
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
    response_json["fee"] = response_json["fee"]
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@silk_profile(name="transfer_token")
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


@silk_profile(name="get_fee_for_new_signal")
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
        response["fee"] = response["fee"]
        response["balance"] = check_balance(user_key)["balance"]
        return Response(response, status=code)
    except requests.HTTPError:
        return Response({"error": "could not get fee"})


@silk_profile(name="send_new_signal")
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
    if form.cleaned_data["recipient_group"]:
        signal.viewers.add(
            APIGroup.objects.get(name=form.cleaned_data["recipient_group"])
        )
    result, success = signal_send_helper(user_key, signal)
    return Response(
        result,
        status=200 if success else 400,
    )


@silk_profile(name="get_fee_for_sync_signal")
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
    response["fee"] = response["fee"]
    response["balance"] = check_balance(user_key)["balance"]
    return Response(response, status=code)


@silk_profile(name="sync_signal")
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
    result, success = signal_send_helper(user_key, signal)
    return Response(
        result,
        status=200 if success else 400,
    )


@silk_profile(name="confirm_signal")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def confirm_signal(request):
    signal = get_object_or_404(Signal, id=request.data["id"])
    ConfirmationRecord.objects.update_or_create(signal=signal, confirmer=request.user)
    return Response({"status": "ok"})


@silk_profile(name="get_signal_by_id")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signal_by_id(request, signal_id):
    signal = get_object_or_404(Signal, id=signal_id)
    serializer = SignalSerializer(signal)
    return Response(serializer.data)


@silk_profile(name="get_signals")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    groups = request.user.api_group_users.all()
    queryset = Signal.objects.filter(Q(viewers=None) | Q(viewers__in=groups)).order_by(
        "-timestamp"
    )
    if count is not None:
        queryset = queryset[:count]
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@silk_profile(name="get_signals_in_range")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals_in_range(request, start_index=None, end_index=None):
    groups = request.user.api_group_users.all()
    queryset = Signal.objects.filter(
        (Q(viewers=None) | Q(viewers__in=groups))
        & Q(pk__range=(start_index, end_index))
    ).order_by("-timestamp")
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@silk_profile(name="get_unsynced_signals")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_unsynced_signals(request):
    queryset = Signal.objects.filter(sender=request.user, synced=False)
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@silk_profile(name="get_fee_history")
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
