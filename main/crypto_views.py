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

from main.forms import DhDecryptWhiteflagMessageForm, DhEncryptWhiteflagMessageForm
from main.models import UserKeys
from main.whiteflag_helpers import (
    generate_diffie_hellman_keys,
    generate_brainpool_keys,
    compute_brainpool_shared_secret,
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
    form = DhEncryptWhiteflagMessageForm(request.data)
    if not form.is_valid():
        return Response({"error": dict(form.errors.items())})
    signal, success = whiteflag_encrypt_helper(
        form.cleaned_data["message"], form.cleaned_data["shared_secret"]
    )
    if success:
        return Response(
            {
                "encrypted": signal,
            },
            200,
        )
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
        return Response(
            {
                "decrypted": signal,
            },
            200,
        )
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


# ============================================================================
# Brainpool P256r1 Endpoints (Whiteflag RFC 5639 Compliance)
# ============================================================================


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_brainpool_keypair(request):
    """
    Generates a brainpoolP256r1 keypair for Whiteflag authentication (RFC 5639).
    Stores both private and public keys in the user's UserKeys record.
    
    Returns:
        {
            "success": bool,
            "private_key": str (32 bytes hex),
            "public_key": str (33 bytes SEC1 compressed hex),
            "error": str (optional)
        }
    """
    keys_dict = generate_brainpool_keys()
    if keys_dict["success"]:
        UserKeys.objects.update_or_create(
            user=request.user,
            defaults={
                "private_brainpool_key": keys_dict["private_key"],
                "public_brainpool_key": keys_dict["public_key"],
            }
        )
    return Response(keys_dict)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_brainpool_keypair(request):
    """
    Retrieves the current user's brainpoolP256r1 keypair.
    
    Returns:
        {
            "success": str,
            "private_key": str (32 bytes hex),
            "public_key": str (33 bytes SEC1 compressed hex)
        }
        OR
        {
            "error": str
        }
    """
    if UserKeys.objects.filter(user=request.user).exists():
        user_keys = UserKeys.objects.get(user=request.user)
        private_key = user_keys.private_brainpool_key
        public_key = user_keys.public_brainpool_key
        
        if private_key and public_key:
            return Response(
                {
                    "success": "brainpool keypair retrieved",
                    "private_key": private_key,
                    "public_key": public_key,
                }
            )
        else:
            return Response(
                {"error": "no brainpool keypair exists for user"},
                status=404
            )
    return Response({"error": "user keys not found"}, status=404)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def compute_brainpool_shared_secret_view(request):
    """
    Computes ECDH shared secret using brainpoolP256r1.
    Requires my_private_key and their_public_key in request body.
    
    Request body:
        {
            "my_private_key": str (32 bytes hex),
            "their_public_key": str (33 bytes SEC1 compressed hex)
        }
    
    Returns:
        {
            "success": str,
            "shared_secret": str (32 bytes hex)
        }
        OR
        {
            "error": str
        }
    """
    my_private_key = request.data.get("my_private_key")
    their_public_key = request.data.get("their_public_key")
    
    if not my_private_key or not their_public_key:
        return Response(
            {"error": "Both my_private_key and their_public_key are required"},
            status=400
        )
    
    result = compute_brainpool_shared_secret(my_private_key, their_public_key)
    
    if result["success"]:
        return Response(
            {
                "success": "brainpool shared secret computed",
                "shared_secret": result["shared_secret"],
            }
        )
    else:
        return Response(
            {"error": result.get("error", "Failed to compute shared secret")},
            status=500
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_brainpool_public_key_by_username(request):
    """
    Retrieves another user's brainpool public key by username.
    Used for initiating Whiteflag authentication handshakes.
    
    Request body:
        {
            "username": str
        }
    
    Returns:
        {
            "public_key": str (33 bytes SEC1 compressed hex)
        }
        OR
        {
            "error": str
        }
    """
    username = request.data.get("username")
    if not username:
        return Response({"error": "username is required"}, status=400)
    
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(username=username)
        if UserKeys.objects.filter(user=user).exists():
            user_keys = UserKeys.objects.get(user=user)
            public_key = user_keys.public_brainpool_key
            if public_key:
                return Response({"public_key": public_key})
            else:
                return Response(
                    {"error": "no brainpool key exists for username"},
                    status=404
                )
        else:
            return Response({"error": "user keys not found"}, status=404)
    except User.DoesNotExist:
        return Response({"error": "user not found"}, status=404)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_brainpool_public_key_by_address(request):
    """
    Retrieves a user's brainpool public key by blockchain address.
    Used for Whiteflag authentication with known blockchain participants.
    
    Request body:
        {
            "address": str
        }
    
    Returns:
        {
            "public_key": str (33 bytes SEC1 compressed hex)
        }
        OR
        {
            "error": str
        }
    """
    address = request.data.get("address")
    if not address:
        return Response({"error": "address is required"}, status=400)
    
    if UserKeys.objects.filter(address=address).exists():
        user_keys = UserKeys.objects.get(address=address)
        public_key = user_keys.public_brainpool_key
        if public_key:
            return Response({"public_key": public_key})
        else:
            return Response(
                {"error": "no brainpool key exists for address"},
                status=404
            )
    return Response({"error": "address not found"}, status=404)

