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

from main.decorators import silk_profile

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
    try:
        # Call the improved subservice for dynamic fee calculation
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_new_signal",
            data=payload,
            timeout=10,  # Increased timeout for blockchain calls
        )

        if response.status_code != 200:
            return (
                {
                    "error": "subservice fee calculation failed",
                    "status_code": response.status_code,
                    "content": payload["content"],
                },
                False,
            )

        try:
            fee_data = response.json()
        except ValueError as e:
            # Log the actual error for debugging but don't expose it to the client
            print(f"Subservice returned invalid JSON: {str(e)}")
            print(f"Response text: {response.text[:200]}")
            return (
                {
                    "error": "Fee calculation service returned invalid response",
                },
                False,
            )

        # Check if the response contains a fee
        if "fee" not in fee_data:
            # Log the actual response for debugging but don't expose it to the client
            print(f"Subservice response missing fee: {fee_data}")
            return (
                {
                    "error": "Fee calculation service response incomplete",
                },
                False,
            )

        Transaction.objects.create(
            function="send_new_signal",
            payload_size=len(payload["content"]),
            fee=fee_data["fee"],
        )

        return fee_data, True

    except requests.exceptions.Timeout:
        # Log the actual error for debugging but don't expose it to the client
        print(f"Subservice timeout for content length: {len(payload['content'])}")
        return (
            {
                "error": "Fee calculation service timeout",
            },
            False,
        )
    except requests.exceptions.RequestException as e:
        # Log the actual error for debugging but don't expose it to the client
        print(f"Subservice connection failed: {str(e)}")
        return (
            {
                "error": "Fee calculation service unavailable",
            },
            False,
        )
    except DataError:
        # Log the actual error for debugging but don't expose it to the client
        print(f"Could not record transaction in database for content length: {len(payload['content'])}")
        return (
            {
                "error": "Failed to record transaction",
            },
            False,
        )


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
    except TimeoutError:
        return {"balance": int(key.balance)}
    except requests.exceptions.ReadTimeout:
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

        # Check if fee calculation was successful
        if not success:
            return (signal_fee_result, False)

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

    try:
        # Call the improved subservice for dynamic fee calculation
        response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_transfer_token",
            data=payload,
            timeout=10,  # Increased timeout for blockchain calls
        )

        if response.status_code != 200:
            return Response(
                {
                    "error": "subservice fee calculation failed",
                    "status_code": response.status_code,
                },
                status=400,
            )

        fee_data = response.json()

        Transaction.objects.create(
            function="transfer_token",
            payload_size=0,
            fee=fee_data["fee"],
        )

        response_json = fee_data
        response_json["balance"] = check_balance(user_key)["balance"]
        return Response(response_json)

    except requests.exceptions.Timeout:
        return Response(
            {
                "error": "subservice timeout - blockchain may be slow",
            },
            status=400,
        )
    except requests.exceptions.RequestException as e:
        # Log the actual error for debugging but don't expose it to the client
        print(f"Subservice connection failed: {str(e)}")
        return Response(
            {
                "error": "subservice connection failed",
            },
            status=400,
        )


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
        
        # Sanitize the response to only include safe fields
        if success:
            sanitized_response = {
                "fee": response.get("fee", 0) if response and "fee" in response else 0,
                "balance": check_balance(user_key)["balance"],
            }
        else:
            sanitized_response = {
                "error": "Fee calculation failed",
                "balance": check_balance(user_key)["balance"],
            }
        
        return Response(sanitized_response, status=code)
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
    
    # Sanitize the response to only include safe fields
    if success:
        # In success case, extract only essential fields to avoid exposing sensitive data
        hash_value = result.get("hash") if result and "hash" in result else None
        balance_value = result.get("balance") if result and "balance" in result else None
        signal_id_value = result.get("signal_id") if result and "signal_id" in result else None
        synced_value = result.get("synced", True) if result else True
        
        sanitized_response = {
            "hash": hash_value,
            "balance": balance_value,
            "signal_id": signal_id_value,
            "synced": synced_value,
        }
    else:
        # In error case, extract only essential fields to avoid exposing sensitive data
        balance_value = result.get("balance") if result and "balance" in result else None
        signal_id_value = result.get("signal_id") if result and "signal_id" in result else None
        synced_value = result.get("synced", False) if result else False
        
        sanitized_response = {
            "error": "Signal sending failed",
            "balance": balance_value,
            "signal_id": signal_id_value,
            "synced": synced_value,
        }
    
    return Response(
        sanitized_response,
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


@silk_profile(name="search_signals")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_signals(request):
    query = request.GET.get("query", None)
    show_inactive = request.GET.get("include-inactive", False)
    groups = request.user.api_group_users.all()
    queryset = Signal.objects.filter(
        (Q(viewers=None) | Q(viewers__in=groups)) & Q(signal_text__icontains=query)
    ).order_by("-timestamp")
    if not show_inactive:
        queryset = queryset.filter(active=True)
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


def _build_author_query(authors, author):
    """Build query for author filtering."""
    query = Q()
    for item in authors:
        query = query | Q(sender__username__icontains=item)
    return query | Q(sender__username__icontains=author)


def _build_message_type_query(message_types):
    """Build query for message type filtering."""
    query = Q()
    for item in message_types:
        query = query | Q(signal_body__icontains=item)
    return query


def _build_infrastructure_type_query(infrastructure_types):
    """Build query for infrastructure type filtering."""
    query = Q()
    for item in infrastructure_types:
        query = query | Q(signal_body__icontains=item)
    return query


@silk_profile(name="get_signals")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals(request, count=None):
    show_inactive = request.GET.get("include-inactive", False)
    title = request.GET.get("title", None)
    author = request.GET.get("author", None)
    authors = author.split(",") if author is not None else []
    message_type = request.GET.get("message_type", None)
    message_types = message_type.split(",") if message_type is not None else []
    infrastructure_type = request.GET.get("infrastructure_type", None)
    infrastructure_types = (
        infrastructure_type.split(",") if infrastructure_type is not None else []
    )
    start = request.GET.get("start", None)
    end = request.GET.get("end", None)
    
    groups = request.user.api_group_users.all()
    queryset = Signal.objects.filter(
        (Q(viewers=None) | Q(viewers__in=groups))
    ).order_by("-timestamp")
    
    if not show_inactive:
        queryset = queryset.filter(active=True)
    if title is not None:
        queryset = queryset.filter(Q(signal_text__icontains=title) | Q(signal_body__icontains=title))
    if author is not None:
        query = _build_author_query(authors, author)
        queryset = queryset.filter(query)
    if message_type is not None:
        query = _build_message_type_query(message_types)
        queryset = queryset.filter(query | Q(message_code__in=message_types))
    if infrastructure_type is not None:
        query = _build_infrastructure_type_query(infrastructure_types)
        queryset = queryset.filter(query | Q(subject_code__in=infrastructure_types))
    if count is not None:
        queryset = queryset[:count]
    if start is not None and end is not None:
        queryset = queryset.filter(pk__range=(start, end))
    
    serializer = SignalSerializer(queryset, many=True)
    return Response(serializer.data)


@silk_profile(name="get_signals_in_range")
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_signals_in_range(request, start_index=None, end_index=None):
    show_inactive = request.GET.get("include-inactive", False)
    groups = request.user.api_group_users.all()
    queryset = Signal.objects.filter(
        (Q(viewers=None) | Q(viewers__in=groups))
        & Q(pk__range=(start_index, end_index))
    ).order_by("-timestamp")
    if not show_inactive:
        queryset = queryset.filter(active=True)
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
