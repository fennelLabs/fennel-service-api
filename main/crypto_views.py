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

from main.models import UserKeys


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def wf_is_this_encrypted(request):
    if request.data["message"][7] == "1":
        return Response({"encrypted": True})
    else:
        return Response({"encrypted": False})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_diffie_hellman_keypair(request):
    try:
        r = requests.post(
            "{0}/v1/generate_encryption_channel".format(
                os.environ.get("FENNEL_CLI_IP", None)
            )
        )
        UserKeys.objects.update_or_create(
            user=request.user,
            public_diffie_hellman_key=r.json()["secret"],
            private_diffie_hellman_key=r.json()["public"],
        )
        return Response(
            {"success": "keypair created", "public_key": r.json()["public"]}
        )
    except Exception as e:
        return Response({"error": "keypair not created", "detail": str(e)})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_diffie_hellman_shared_secret(request):
    try:
        r = requests.post(
            "{0}/v1/accept_encryption_channel".format(
                os.environ.get("FENNEL_CLI_IP", None)
            ),
            json={"secret": request.data["secret"], "public": request.data["public"]},
        )
        return Response(
            {
                "success": "shared secret created",
                "shared_secret": r.json()["shared_secret"],
            }
        )
    except Exception as e:
        return Response({"error": "shared secret not created", "detail": str(e)})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_encrypt_whiteflag_message(request):
    try:
        r = requests.post(
            "{0}/v1/dh_encrypt".format(os.environ.get("FENNEL_CLI_IP", None)),
            json={
                "plaintext": request.data["message"][9:],
                "shared_secret": request.data["shared_secret"],
            },
        )
        return Response(
            {
                "success": "message encrypted",
                "encrypted": (
                    request.data["message"][0:7]
                    + "1"
                    + request.data["message"][8:9]
                    + r.text
                ),
            }
        )
    except Exception as e:
        return Response({"error": "message not encrypted", "detail": str(e)})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def dh_decrypt_whiteflag_message(request):
    try:
        r = requests.post(
            "{0}/v1/dh_decrypt".format(os.environ.get("FENNEL_CLI_IP", None)),
            json={
                "ciphertext": request.data["message"][9:],
                "shared_secret": request.data["shared_secret"],
            },
        )
        return Response(
            {
                "success": "message decrypted",
                "decrypted": (request.data["message"][0:9] + r.text),
            }
        )
    except Exception as e:
        return Response({"error": "message not decrypted", "detail": str(e)})


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_dh_public_key_by_username(request):
    if UserKeys.objects.filter(user__username=request.data["username"]).exists():
        public_key = UserKeys.objects.get(
            user__username=request.data["username"]
        ).public_diffie_hellman_key
        return Response({"public_key": public_key})
    else:
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
    else:
        return Response({"error": "no key exists for address"})
