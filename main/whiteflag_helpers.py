import json
import os
from typing import Optional

from silk.profiling.profiler import silk_profile

import requests

from main.models import APIGroup


def convert_to_test_message(signal_body: dict) -> dict:
    """
    Converts a regular WhiteFlag message to a Test (T) message.
    
    Test messages allow testing on live blockchains without polluting operational data.
    They are clearly marked with messageCode "T" and include a pseudoMessageCode field
    that indicates which message type is being tested.
    
    Args:
        signal_body: The original message body dict
        
    Returns:
        Modified message body dict with messageCode "T" and pseudoMessageCode set
        
    Example:
        Free Text message {"messageCode": "F", "text": "Hello"}
        becomes Test message {"messageCode": "T", "pseudoMessageCode": "F", "text": "Hello"}
    """
    # Store the original message code
    original_message_code = signal_body.get("messageCode", None)
    
    # If already a test message, return as-is
    if original_message_code == "T":
        return signal_body
    
    # Create a copy to avoid mutating the original
    test_message = signal_body.copy()
    
    # Convert to test message
    test_message["messageCode"] = "T"
    test_message["pseudoMessageCode"] = original_message_code
    
    return test_message


@silk_profile(name="generate_group_keys")
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


@silk_profile(name="generate_diffie_hellman_keys")
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


@silk_profile(name="generate_shared_secret")
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
        response.raise_for_status()
        response_data = response.json()
        if "shared_secret" not in response_data:
            return ({"error": "shared secret not generated: missing shared_secret in response"}), False
        return response_data["shared_secret"], True
    except (requests.RequestException, requests.JSONDecodeError, KeyError) as e:
        return ({"error": f"shared secret not generated: {str(e)}"}), False


@silk_profile(name="whiteflag_encrypt_helper")
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


@silk_profile(name="whiteflag_decrypt_helper")
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


@silk_profile(name="whiteflag_encoder_helper")
def whiteflag_encoder_helper(
    payload: dict,
    sender_group: Optional[APIGroup] = None,
    recipient_group: Optional[APIGroup] = None,
) -> (str, bool):
    datetime_field = payload.get("datetime", None)
    if datetime_field is None:
        datetime_field = payload.get("dateTime", None)
    encryption_indicator = payload.get("encryptionIndicator", None)
    if sender_group and recipient_group:
        encryption_indicator = "1"
    
    # Note: We do NOT hex-encode text fields here!
    # The Rust WhiteFlag encoder handles UTF-8 encoding automatically.
    # Text fields (text, verificationData, resourceData) should be passed as plain UTF-8 strings.
    
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
    
    # Debug: Log the exact payload being sent to the encoder
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"DEBUG ENCODER PAYLOAD (len={len(processed_payload)}): {processed_payload}")
    logger.error(f"DEBUG ENCODER PAYLOAD BYTES: {processed_payload.encode('utf-8')}")
    
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
            data=signal,
            timeout=5,
        )
    except requests.exceptions.ConnectionError:
        return ({"error": "could not decode signal"}, False)
    if response.status_code != 200:
        return ({"error": "could not decode signal"}, False)
    if not response.json()["success"]:
        return ({"error": response.json()["error"]}, False)
    decoded = json.loads(response.json()["decoded"])
    
    # Note: We do NOT need to hex-decode text fields here!
    # The Rust WhiteFlag decoder already returns UTF-8 strings for text fields.
    # Fields like text, verificationData, and resourceData are already decoded.
    
    return (
        decoded,
        response.json()["success"],
    )


@silk_profile(name="whiteflag_decoder_helper")
def decode(
    signal: str,
    sender_group: Optional[APIGroup] = None,
    recipient_group: Optional[APIGroup] = None,
) -> (dict, bool):
    # Ensure signal is a string
    if not isinstance(signal, str):
        return ({"error": "signal must be a string"}, False)
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
