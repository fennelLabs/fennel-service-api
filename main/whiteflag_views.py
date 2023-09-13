import json
import uuid
import hashlib
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import Http404

import requests


def whiteflag_encoder_helper(payload):
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
        return Response(
            {
                "error": "the whiteflag service is inaccessible",
            },
            status=400,
        )
    try:
        return Response(response.json())
    except requests.JSONDecodeError:
        return Response(response.text)


@api_view(["GET"])
def fennel_cli_healthcheck(request):
    response = requests.get(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/hello_there/", timeout=5
    )
    if response.status_code == 200:
        return Response("Ok")
    raise Http404


@api_view(["POST"])
def whiteflag_authenticate(request):
    payload = json.dumps(
        {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",
            "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
            "verificationMethod": request.data["verificationMethod"],
            "verificationData": request.data["verificationData"],
        }
    )
    return whiteflag_encoder_helper(payload)


@api_view(["POST"])
def whiteflag_discontinue_authentication(request):
    payload = json.dumps(
        {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "4",
            "referencedMessage": request.data["referencedMessage"],
            "verificationMethod": request.data["verificationMethod"],
            "verificationData": request.data["verificationData"],
        }
    )
    return whiteflag_encoder_helper(payload)


@api_view(["POST"])
def whiteflag_encode(request):
    return whiteflag_encoder_helper(request.data)


@api_view(["POST"])
def whiteflag_decode(request):
    payload = json.dumps(request.data["message"])
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
        data=payload,
        timeout=5,
    )
    if response.status_code == 502:
        return Response(
            {
                "error": "the whiteflag service is inaccessible",
            },
            status=400,
        )
    return Response(json.loads(response.json()))


@api_view(["POST"])
def whiteflag_announce_public_key(request):
    payload = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "K",
        "referenceIndicator": "0",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        "cryptoDataType": "1",
        "cryptoData": request.data["public_key"],
    }
    return whiteflag_encoder_helper(payload)


@api_view(["GET"])
def whiteflag_generate_shared_token(request):
    response = {
        "sharedToken": str(uuid.uuid4()),
    }
    return Response(response)


@api_view(["POST"])
def whiteflag_generate_public_token(request):
    payload = json.dumps(
        {
            "sharedToken": request.data["sharedToken"],
            "address": request.data["address"],
        }
    )
    payload_hash = hashlib.sha3_512()
    payload_hash.update(payload.encode("utf-8"))
    response = payload_hash.hexdigest()
    return Response(response)
