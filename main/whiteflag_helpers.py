import json
import os

import requests


def whiteflag_encrypt_helper(payload: dict) -> (str, bool):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_encrypt",
            json={
                "plaintext": payload["message"][9:],
                "shared_secret": payload["shared_secret"],
            },
            timeout=5,
        )
        return (
            {
                "success": "message encrypted",
                "encrypted": (
                    payload["message"][0:7]
                    + "1"
                    + payload["message"][8:9]
                    + response.text
                ),
            }
        ), True
    except requests.HTTPError:
        return ({"error": "message not encrypted"}), False


def whiteflag_decrypt_helper(payload: dict) -> (str, bool):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/dh_decrypt",
            json={
                "ciphertext": payload["message"][9:],
                "shared_secret": payload["shared_secret"],
            },
            timeout=5,
        )
        return (
            {
                "success": "message decrypted",
                "decrypted": (payload["message"][0:9] + response.text),
            }
        ), True
    except requests.HTTPError:
        return ({"error": "message not decrypted"}), False


def whiteflag_encoder_helper(payload: dict) -> (dict, bool):
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
    try:
        return response.json(), True
    except requests.JSONDecodeError:
        return response.text, True


def decode(signal: str) -> (dict, bool):
    if signal[0:2] != "57":
        return ({"error": "not a whiteflag signal"}, False)
    if signal[7] == "1":
        return (
            {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "1",
                "signal_body": signal[8:],
            },
            True,
        )
    signal = json.dumps(signal)
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
        data=signal,
        timeout=5,
    )
    if response.status_code != 200:
        return ({"error": "could not decode signal"}, False)
    return (json.loads(response.json()), True)
