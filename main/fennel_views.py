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
    TrustConnection,
    TrustRequest,
    UserKeys,
    ConfirmationRecord,
)


def record_signal_fee(payload: dict) -> (dict, bool):
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
        data=payload,
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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/create_account"
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
    return check_balance(key)


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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address", data=payload
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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/transfer_token", data=payload
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
        signal_fee_result, success = record_signal_fee(payload)
        if not success:
            return Response(signal_fee_result, status=400)
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        if not response.json()["hash"]:
            return Response(
                {
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "balance": check_balance(user_key)["balance"],
                }
            )
        signal.tx_hash = response.json()["hash"]
        signal.synced = True
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
        if not success:
            return Response(signal_fee_result, status=400)
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/send_new_signal",
            data=payload,
        )
        if not response.json()["hash"]:
            return Response(
                {
                    "signal": "saved as unsynced. call /v1/fennel/sync_signal to complete the transaction",
                    "balance": check_balance(user_key)["balance"],
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


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_issue_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_issue_trust",
        data=payload,
    )
    Transaction.objects.create(
        function="issue_trust",
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
def issue_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    if payload["address"] == user_key.address:
        return Response({"error": "user cannot trust themselves"}, status=400)
    trust_target = get_object_or_404(UserKeys, address=payload["address"]).user
    if not trust_target:
        return Response({"error": "user does not exist"})
    TrustConnection.objects.update_or_create(
        user=request.user, trusted_user=trust_target
    )
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/issue_trust", data=payload
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_remove_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_remove_trust",
        data=payload,
    )
    Transaction.objects.create(
        function="remove_trust",
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
def remove_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    if payload["address"] == user_key.address:
        return Response({"error": "user cannot trust themselves"}, status=400)
    trust_target = get_object_or_404(UserKeys, address=payload["address"]).user
    if not trust_target:
        return Response({"error": "user does not exist"})
    TrustConnection.objects.filter(
        user=request.user, trusted_user=trust_target
    ).delete()
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/remove_trust", data=payload
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_request_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_request_trust",
        data=payload,
    )
    Transaction.objects.create(
        function="request_trust",
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
def request_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    if payload["address"] == user_key.address:
        return Response({"error": "user cannot trust themselves"}, status=400)
    trust_target = get_object_or_404(UserKeys, address=payload["address"]).user
    if not trust_target:
        return Response({"error": "user does not exist"})
    TrustRequest.objects.update_or_create(user=request.user, trusted_user=trust_target)
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/request_trust", data=payload
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_cancel_trust_request(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_cancel_trust_request",
        data=payload,
    )
    Transaction.objects.create(
        function="cancel_trust_request",
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
def cancel_trust_request(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    if payload["address"] == user_key.address:
        return Response({"error": "user cannot trust themselves"}, status=400)
    trust_target = get_object_or_404(UserKeys, address=payload["address"]).user
    if not trust_target:
        return Response({"error": "user does not exist"})
    TrustRequest.objects.filter(user=request.user, trusted_user=trust_target).delete()
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/cancel_trust_request",
        data=payload,
    )
    response_json = response.json()
    response_json["balance"] = check_balance(user_key)["balance"]
    return Response(response_json)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trust_requests(request):
    return Response(
        [
            {
                "id": trust_request.id,
                "timestamp": trust_request.timestamp,
                "requesting_user": {
                    "id": trust_request.user.id,
                    "username": trust_request.user.username,
                },
            }
            for trust_request in TrustRequest.objects.filter(trusted_user=request.user)
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trust_connections(request):
    return Response(
        [
            {
                "id": trust_connection.id,
                "timestamp": trust_connection.timestamp,
                "trusted_user": {
                    "id": trust_connection.trusted_user.id,
                    "username": trust_connection.trusted_user.username,
                },
            }
            for trust_connection in TrustConnection.objects.filter(user=request.user)
        ]
    )


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def check_if_trust_exists(request):
    Response(
        {
            "trust_exists": TrustConnection.objects.filter(
                user=get_object_or_404(UserKeys, address=request.data["address"]).user,
                trusted_user=get_object_or_404(
                    UserKeys, address=request.data["address"]
                ).user,
            ).exists()
        }
    )
