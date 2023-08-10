from django.shortcuts import get_object_or_404
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import UserKeys
from .secret_key_utils import split_mnemonic, reconstruct_mnemonic
from .decorators import subject_to_api_limit
import requests
import os
import ast


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
def download_self_custodial_account_as_json(request):
    keys = get_object_or_404(UserKeys, user=request.user)
    key_shards = [
        ast.literal_eval(keys.key_shard),
        ast.literal_eval(bytes.fromhex(request.data["user_shard"]).decode("utf-8")),
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
@subject_to_api_limit
def get_self_custodial_account_address(request):
    payload = {"mnemonic": request.data["mnemonic"]}
    r = requests.post(
        f"{os.environ.get('FENNEL_SUBSERVICE_IP', None)}/get_address", data=payload
    )
    return Response(r.json())
