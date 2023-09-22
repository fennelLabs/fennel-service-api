import json
import os
from typing import Optional

import requests

from main.models import APIGroup


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


def generate_shared_secret(our_group: APIGroup, their_group: APIGroup) -> (str, bool):
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
            return "message not decrypted", False
        return (message[0:9] + response.text), True
    except requests.HTTPError:
        return "message not decrypted", False


def whiteflag_encoder_helper(
    payload: dict,
    sender_group: Optional[APIGroup] = None,
    recipient_group: Optional[APIGroup] = None,
) -> (dict, bool):
    datetime_field = payload.get("datetime", None)
    if datetime_field is None:
        datetime_field = payload.get("dateTime", None)
    json_packet = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": payload.get("encryptionIndicator", None),
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
        "datetime": datetime_field,
        "duration": payload.get("duration", None),
        "objectType": payload.get("objectType", None),
        "objectLatitude": payload.get("objectLatitude", None),
        "objectLongitude": payload.get("objectLongitude", None),
        "objectSizeDim1": payload.get("objectSizeDim1", None),
        "objectSizeDim2": payload.get("objectSizeDim2", None),
        "objectOrientation": payload.get("objectOrientation", None),
        "objectTypeQuant": payload.get("objectTypeQuant", None),
    }
    processed_payload = json.dumps({k: v for k, v in json_packet.items() if v})
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_encode",
        data=processed_payload,
        timeout=5,
    )
    if response.status_code == 502:
        return (
            {
                "error": "the whiteflag service is inaccessible",
            },
            False,
        )
    if json_packet["encryptionIndicator"] == "1":
        shared_key, shared_secret_success = generate_shared_secret(
            sender_group, recipient_group
        )
        if not shared_secret_success:
            return shared_key, False
        return whiteflag_encrypt_helper(response.text, shared_key)
    try:
        return response.json(), True
    except requests.JSONDecodeError:
        return response.text, True


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
    signal = json.dumps(signal)
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
        data=signal,
        timeout=5,
    )
    if response.status_code != 200:
        return ({"error": "could not decode signal"}, False)
    return (json.loads(response.json()), True)
