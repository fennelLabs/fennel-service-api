import os

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404

import requests

from main.decorators import requires_mnemonic_created
from main.fennel_views import check_balance

from main.models import UserKeys, TrustConnection, TrustRequest, Transaction


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
        timeout=5,
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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/issue_trust",
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
def get_fee_for_remove_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_remove_trust",
        data=payload,
        timeout=5,
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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/remove_trust",
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
def get_fee_for_request_trust(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_request_trust",
        data=payload,
        timeout=5,
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
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/request_trust",
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
def get_fee_for_cancel_trust_request(request):
    user_key = UserKeys.objects.filter(user=request.user).first()
    payload = {
        "mnemonic": user_key.mnemonic,
        "address": request.data["address"],
    }
    response = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_fee_for_cancel_trust_request",
        data=payload,
        timeout=5,
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
        timeout=5,
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
