import json
import os
from typing import Optional, Tuple

# from silk.profiling.profiler import silk_profile  # DISABLED: Silk removed

import requests

from main.models import APIGroup, WhiteflagAuthentication


# @silk_profile(name="submit_initial_authentication")  # DISABLED: Silk removed
def submit_initial_authentication(
    user,
    verification_method: str,
    verification_data: str
) -> Tuple[dict, bool]:
    """
    Submits A(0) initial authentication message for a user.

    Per Whiteflag spec 5.1.1: "Each account should be identified by sending
    an A(0) initial authentication message, before sending any other message."

    For Method 2 (Pre-shared Token): The verification_data is a private secret
    that will be HKDF-derived using the blockchain address as context to create
    a public verification token for the blockchain.

    Args:
        user: Django User object
        verification_method: "1" for URL validation, "2" for shared token
        verification_data: URL (Method 1) or HEX pre-shared secret (Method 2)

    Returns:
        (response_dict, success_bool)
    """
    # Check if user already has authentication
    if WhiteflagAuthentication.objects.filter(user=user, is_active=True).exists():
        return (
            {
                "error": "User already has active authentication",
                "fix": "Use A(4) discontinuation before re-authenticating"
            },
            False
        )

    # For Method 2, derive the public token using HKDF
    derived_token = None
    if verification_method == "2":
        try:
            # Get blockchain address for the user (context for HKDF)
            from main.models import UserKeys
            user_keys = UserKeys.objects.get(user=user)
            blockchain_address = user_keys.address

            if not blockchain_address:
                return (
                    {
                        "error": "User has no blockchain address",
                        "fix": "Create blockchain account first"
                    },
                    False
                )

            # Convert blockchain address to binary context for HKDF
            # Per Whiteflag spec 5.2.3: "the binary representation of the blockchain address"
            blockchain_context = blockchain_address.encode('utf-8').hex()

        except UserKeys.DoesNotExist:
            return (
                {
                    "error": "User has no blockchain keys",
                    "fix": "Create blockchain account first"
                },
                False
            )

        try:
            response = requests.post(
                f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/derive_auth_token",
                json={
                    "secret": verification_data,
                    "context": blockchain_context,
                },
                timeout=5,
            )

            if response.status_code != 200:
                return (
                    {"error": "Failed to derive authentication token", "details": response.text},
                    False
                )

            result = response.json()
            if not result.get("success"):
                return (
                    {"error": "Token derivation failed", "details": result.get("error")},
                    False
                )

            derived_token = result.get("derived_token")

        except requests.exceptions.RequestException as e:
            return (
                {"error": "Failed to connect to crypto service", "details": str(e)},
                False
            )

    # Create A(0) message payload
    payload = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "A",
        "referenceIndicator": "0",  # Initial authentication
        "referencedMessage": "0" * 64,  # No reference for A(0)
        "verificationMethod": verification_method,
        # For Method 2, use the derived token; for Method 1, use the URL directly
        "verificationData": derived_token if verification_method == "2" else verification_data,
    }

    # Submit via whiteflag encoder
    result, success = whiteflag_encoder_helper(payload)

    if success:
        # result is the encoded message string when successful
        # Store authentication record
        # Store the ORIGINAL secret for Method 2 (not the derived token)
        auth_record = WhiteflagAuthentication.objects.create(
            user=user,
            verification_method=verification_method,
            verification_data=verification_data,  # Store original secret
            transaction_hash=None,  # Will be updated after blockchain submission
            is_active=True
        )

        return (
            {
                "status": "authenticated",
                "verification_method": verification_method,
                "encoded_message": result,
                "message": "A(0) initial authentication submitted successfully",
                "authentication_id": auth_record.id,
                # Include derived token info for Method 2
                "derived_token": derived_token if verification_method == "2" else None,
            },
            True
        )

    # When not successful, result is an error dict
    return (result, False)


# @silk_profile(name="check_authentication_status")  # DISABLED: Silk removed
def check_authentication_status(user) -> bool:
    """
    Check if user has submitted A(0) initial authentication.

    Per Whiteflag spec 5.1.1: Messages sent before A(0) may be
    considered unauthenticated by recipients.

    Args:
        user: Django User object

    Returns:
        True if user has active authentication, False otherwise
    """
    return WhiteflagAuthentication.objects.filter(
        user=user,
        is_active=True
    ).exists()


# @silk_profile(name="generate_group_keys")  # DISABLED: Silk removed
def generate_group_keys(group: APIGroup) -> bool:
    if (
        group.public_diffie_hellman_key is not None
        and group.private_diffie_hellman_key is not None
    ):
        return True
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/generate_encryption_channel",
            timeout=5,
        )
    except requests.HTTPError:
        return False
    group.public_diffie_hellman_key = response.json()["secret"]
    group.private_diffie_hellman_key = response.json()["public"]
    group.save()
    return True


# @silk_profile(name="generate_diffie_hellman_keys")  # DISABLED: Silk removed
def generate_diffie_hellman_keys() -> dict:
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/generate_encryption_channel",
            timeout=5,
        )
        return {
            "success": True,
            "public_key": response.json()["public"],
            "secret_key": response.json()["secret"],
        }
    except requests.HTTPError:
        return {
            "error": "keypair not created",
            "success": False,
            "public_key": None,
            "secret_key": None,
        }


def generate_brainpool_keys() -> dict:
    """
    Generates a brainpoolP256r1 keypair for Whiteflag RFC 5639 compliance.
    Calls fennel-cli's /v1/generate_brainpool_keypair endpoint.

    Returns:
        dict with success, private_key (32 bytes hex),
        public_key (33 bytes SEC1 compressed hex)
    """
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/generate_brainpool_keypair",
            timeout=5,
        )
        response_data = response.json()

        if response_data.get("success"):
            return {
                "success": True,
                "private_key": response_data["private_key"],
                "public_key": response_data["public_key"],
            }
        else:
            return {
                "success": False,
                "error": response_data.get("error", "Unknown error"),
                "private_key": None,
                "public_key": None,
            }
    except (requests.HTTPError, requests.RequestException) as e:
        return {
            "success": False,
            "error": f"Failed to generate brainpool keypair: {str(e)}",
            "private_key": None,
            "public_key": None,
        }


def compute_brainpool_shared_secret(my_private_key: str,
                                    their_public_key: str) -> dict:
    """
    Computes ECDH shared secret using brainpoolP256r1.
    Calls fennel-cli's /v1/compute_brainpool_shared_secret endpoint.

    Args:
        my_private_key: 32-byte private key (hex string)
        their_public_key: 33-byte SEC1 compressed public key (hex string)

    Returns:
        dict with success, shared_secret (32 bytes hex)
    """
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/compute_brainpool_shared_secret",
            json={
                "my_private_key": my_private_key,
                "their_public_key": their_public_key,
            },
            timeout=5,
        )
        response_data = response.json()

        if response_data.get("success"):
            return {
                "success": True,
                "shared_secret": response_data["shared_secret"],
            }
        else:
            return {
                "success": False,
                "error": response_data.get("error", "Unknown error"),
                "shared_secret": None,
            }
    except (requests.HTTPError, requests.RequestException) as e:
        return {
            "success": False,
            "error": f"Failed to compute brainpool shared secret: {str(e)}",
            "shared_secret": None,
        }


# @silk_profile(name="generate_shared_secret")  # DISABLED: Silk removed
def generate_shared_secret(our_group: APIGroup, their_group: APIGroup) -> (str, bool):
    if (
        our_group.private_diffie_hellman_key is None
        or our_group.public_diffie_hellman_key is None
    ):
        if not generate_group_keys(our_group):
            return ({"error": "our API group has no keypair"}, False)
    if (
        their_group.public_diffie_hellman_key is None
        or their_group.public_diffie_hellman_key is None
    ):
        if not generate_group_keys(their_group):
            return ({"error": "their API group has no keypair"}, False)
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/accept_encryption_channel",
            json={
                "secret": our_group.private_diffie_hellman_key,
                "public": their_group.public_diffie_hellman_key,
            },
            timeout=5,
        )
        if response.status_code != 200:
            return ({"error": "shared secret not generated"}), False
        return response.json()["shared_secret"], True
    except requests.HTTPError:
        return ({"error": "shared secret not generated"}), False


# @silk_profile(name="whiteflag_encrypt_helper")  # DISABLED: Silk removed
def whiteflag_encrypt_helper(message: str, shared_secret: str) -> (str, bool):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_encrypt",
            json={
                "plaintext": message[9:],
                "shared_secret": shared_secret,
            },
            timeout=5,
        )
        return (message[0:7] + "1" + message[8:9] + response.text), True
    except requests.HTTPError:
        return "message not encrypted", False


# @silk_profile(name="whiteflag_decrypt_helper")  # DISABLED: Silk removed
def whiteflag_decrypt_helper(message: str, shared_secret: str) -> (str, bool):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_decrypt",
            json={
                "ciphertext": message[9:],
                "shared_secret": shared_secret,
            },
            timeout=5,
        )
        if response.status_code != 200:
            return {"error": "message not decrypted"}, False
        return (message[0:9] + response.text), True
    except requests.HTTPError:
        return {"error": "message not decrypted"}, False


def create_whiteflag_encoder_response(
    json_packet, response, sender_group, recipient_group
):
    if response.status_code == 502:
        return (
            {
                "error": "the whiteflag service is inaccessible",
            },
            False,
        )
    try:
        return_value = response.json()
    except requests.JSONDecodeError:
        return_value = response.text
    if response.status_code != 200:
        return ({"error": return_value}, False)
    if not response.json()["success"]:
        return ({"error": return_value["error"]}, False)
    if json_packet["encryptionIndicator"] == "1":
        shared_key, shared_secret_success = generate_shared_secret(
            sender_group, recipient_group
        )
        if not shared_secret_success:
            return shared_key, False
        return whiteflag_encrypt_helper(return_value["encoded"], shared_key)
    return (return_value["encoded"], True)


# @silk_profile(name="whiteflag_encoder_helper")  # DISABLED: Silk removed
def whiteflag_encoder_helper(
    payload: dict,
    sender_group: Optional[APIGroup] = None,
    recipient_group: Optional[APIGroup] = None,
) -> (dict, bool):
    datetime_field = payload.get("datetime", None)
    if datetime_field is None:
        datetime_field = payload.get("dateTime", None)
    encryption_indicator = payload.get("encryptionIndicator", None)
    if sender_group and recipient_group:
        encryption_indicator = "1"
    if payload.get("text", None):
        payload["text"] = payload["text"].encode("utf-8").hex()
    json_packet = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": encryption_indicator,
        "duressIndicator": payload.get("duressIndicator", None),
        "messageCode": payload.get("messageCode", None),
        "referenceIndicator": payload.get("referenceIndicator", None),
        "referencedMessage": payload.get("referencedMessage", None),
        "verificationMethod": payload.get("verificationMethod", None),
        "verificationData": payload.get("verificationData", None),
        "cryptoDataType": payload.get("cryptoDataType", None),
        "cryptoData": payload.get("cryptoData", None),
        "text": payload.get("text", None),
        "resourceMethod": payload.get("resourceMethod", None),
        "resourceData": payload.get("resourceData", None),
        "pseudoMessageCode": payload.get("pseudoMessageCode", None),
        "subjectCode": payload.get("subjectCode", None),
        "dateTime": datetime_field,
        "duration": payload.get("duration", None),
        "objectType": payload.get("objectType", None),
        "objectLatitude": payload.get("objectLatitude", None),
        "objectLongitude": payload.get("objectLongitude", None),
        "objectSizeDim1": payload.get("objectSizeDim1", None),
        "objectSizeDim2": payload.get("objectSizeDim2", None),
        "objectOrientation": payload.get("objectOrientation", None),
        "objectTypeQuant": payload.get("objectTypeQuant", None),
    }
    if payload.get("referencedMessage", None) is None:
        json_packet["referencedMessage"] = (
            "0000000000000000000000000000000000000000000000000000000000000000"
        )
    processed_payload = json.dumps({k: v for k, v in json_packet.items() if v})
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_encode",
        data=processed_payload,
        timeout=5,
    )
    return create_whiteflag_encoder_response(
        json_packet, response, sender_group, recipient_group
    )


def send_decode_final_request(signal: str) -> (dict, bool):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
            json=signal,
            timeout=5,
        )
    except requests.exceptions.ConnectionError:
        return ({"error": "could not decode signal"}, False)
    if response.status_code != 200:
        return ({"error": "could not decode signal"}, False)
    if not response.json()["success"]:
        return ({"error": response.json()["error"]}, False)
    decoded = json.loads(response.json()["decoded"])
    if decoded.get("text", None):
        try:
            decoded["text"] = bytes.fromhex(decoded["text"]).decode("utf-8")
        except (ValueError, AttributeError):
            # Text field is not valid hex or cannot be decoded - leave as-is
            pass
    return (
        decoded,
        response.json()["success"],
    )


# @silk_profile(name="whiteflag_decoder_helper")  # DISABLED: Silk removed
def decode(
    signal: str,
    sender_group: Optional[APIGroup] = None,
    recipient_group: Optional[APIGroup] = None,
) -> (dict, bool):
    if signal[0:2] != "57":
        return ({"error": "not a whiteflag signal"}, False)
    if signal[7] == "1":
        if sender_group is None or recipient_group is None:
            return (
                {
                    "prefix": "WF",
                    "version": "1",
                    "encryptionIndicator": "1",
                    "signal_body": signal[8:],
                },
                True,
            )
        shared_key, success = generate_shared_secret(sender_group, recipient_group)
        if not success:
            return shared_key, False
        signal, decrypt_success = whiteflag_decrypt_helper(signal, shared_key)
        if not decrypt_success:
            return signal, False
    return send_decode_final_request(json.dumps(signal))
