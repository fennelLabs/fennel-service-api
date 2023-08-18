import json
import uuid
import hashlib
import os

from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.http import Http404

import requests


@api_view(["GET"])
def fennel_cli_healthcheck(request):
    response = requests.get(f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/hello_there/")
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
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_encode",
        data=payload,
    )
    try:
        return Response(response.json())
    except requests.JSONDecodeError:
        return Response(response.text)


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
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_encode",
        data=payload,
    )
    try:
        return Response(response.json())
    except requests.JSONDecodeError:
        return Response(response.text)


@api_view(["POST"])
def whiteflag_encode(request):
    json_packet = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": request.data.get("encryptionIndicator", None),
        "duressIndicator": request.data.get("duressIndicator", None),
        "messageCode": request.data.get("messageCode", None),
        "referenceIndicator": request.data.get("referenceIndicator", None),
        "referencedMessage": request.data.get("referencedMessage", None),
        "verificationMethod": request.data.get("verificationMethod", None),
        "verificationData": request.data.get("verificationData", None),
        "cryptoDataType": request.data.get("cryptoDataType", None),
        "cryptoData": request.data.get("cryptoData", None),
        "text": request.data.get("text", None),
        "resourceMethod": request.data.get("resourceMethod", None),
        "resourceData": request.data.get("resourceData", None),
        "pseudoMessageCode": request.data.get("pseudoMessageCode", None),
        "subjectCode": request.data.get("subjectCode", None),
        "datetime": request.data.get("datetime", None),
        "duration": request.data.get("duration", None),
        "objectType": request.data.get("objectType", None),
        "objectLatitude": request.data.get("objectLatitude", None),
        "objectLongitude": request.data.get("objectLongitude", None),
        "objectSizeDim1": request.data.get("objectSizeDim1", None),
        "objectSizeDim2": request.data.get("objectSizeDim2", None),
        "objectOrientation": request.data.get("objectOrientation", None),
        "objectTypeQuant": request.data.get("objectTypeQuant", None),
    }
    payload = json.dumps({k: v for k, v in json_packet.items() if v})
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_encode",
        data=payload,
    )
    try:
        return Response(response.json())
    except requests.JSONDecodeError:
        return Response(response.text)


@api_view(["POST"])
def whiteflag_decode(request):
    payload = json.dumps(request.data["message"])
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
        data=payload,
    )
    return Response(json.loads(response.json()))


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
