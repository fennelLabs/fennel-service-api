import os

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

import requests

from main.forms import DhDecryptWhiteflagMessageForm
from main.models import UserKeys
from main.whiteflag_helpers import (
    generate_diffie_hellman_keys,
    whiteflag_decrypt_helper,
    whiteflag_encrypt_helper,
)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def wf_is_this_encrypted(request):
    if request.data["message"][7] == "1":
        return Response({"encrypted": True})
    return Response({"encrypted": False})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_diffie_hellman_keypair(request):
    keys_dict = generate_diffie_hellman_keys()
    if keys_dict["success"]:
        UserKeys.objects.update_or_create(
            user=request.user,
            public_diffie_hellman_key=keys_dict["secret_key"],
            private_diffie_hellman_key=keys_dict["public_key"],
        )
    return Response(keys_dict)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_keypair(request):
    if UserKeys.objects.filter(user=request.user).exists():
        public_key = UserKeys.objects.get(user=request.user).public_diffie_hellman_key
        private_key = UserKeys.objects.get(user=request.user).private_diffie_hellman_key
        return Response(
            {
                "success": "keypair retrieved",
                "public_key": public_key,
                "private_key": private_key,
            }
        )
    return Response({"error": "no keypair exists for user"}, status=404)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_diffie_hellman_shared_secret(request):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/accept_encryption_channel",
            json={"secret": request.data["secret"], "public": request.data["public"]},
            timeout=5,
        )
        return Response(
            {
                "success": "shared secret created",
                "shared_secret": response.json()["shared_secret"],
            }
        )
    except requests.HTTPError:
        return Response({"error": "shared secret not created"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_encrypt_message(request):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_encrypt",
            json={
                "plaintext": request.data["message"],
                "shared_secret": request.data["shared_secret"],
            },
            timeout=5,
        )
        return Response({"success": "message encrypted", "encrypted": response.text})
    except requests.HTTPError:
        return Response({"error": "message not encrypted"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_decrypt_message(request):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_decrypt",
            json={
                "ciphertext": request.data["message"],
                "shared_secret": request.data["shared_secret"],
            },
            timeout=5,
        )
        return Response({"success": "message decrypted", "decrypted": response.text})
    except requests.HTTPError:
        return Response({"error": "message not decrypted"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_encrypt_whiteflag_message(request):
    form = DhDecryptWhiteflagMessageForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())})
    signal, success = whiteflag_encrypt_helper(form.cleaned_data)
    if success:
        return Response(signal, 200)
    return Response(signal, 400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_decrypt_whiteflag_message(request):
    form = DhDecryptWhiteflagMessageForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())})
    signal, success = whiteflag_decrypt_helper(
        form.cleaned_data["message"], form.cleaned_data["shared_secret"]
    )
    if success:
        return Response(signal, 200)
    return Response(signal, 400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_dh_public_key_by_username(request):
    if UserKeys.objects.filter(user__username=request.data["username"]).exists():
        public_key = UserKeys.objects.get(
            user__username=request.data["username"]
        ).public_diffie_hellman_key
        return Response({"public_key": public_key})
    return Response({"error": "no key exists for username"})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_dh_public_key_by_address(request):
    if UserKeys.objects.filter(address=request.data["address"]).exists():
        public_key = UserKeys.objects.get(
            address=request.data["address"]
        ).public_diffie_hellman_key
        return Response({"public_key": public_key})
    return Response({"error": "no key exists for address"})
