from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import Http404
import requests
import json
import uuid
import hashlib
import os


@api_view(["GET"])
def fennel_cli_healthcheck(request):
    r = requests.get(
        "{0}/v1/hello_there/".format(os.environ.get("FENNEL_CLI_IP", None))
    )
    if r.status_code == 200:
        return Response("Ok")
    else:
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
    r = requests.post(
        "{0}/v1/whiteflag_encode".format(os.environ.get("FENNEL_CLI_IP", None)),
        data=payload,
    )
    try:
        return Response(r.json())
    except:
        return Response(r.text)


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
    r = requests.post(
        "{0}/v1/whiteflag_encode".format(os.environ.get("FENNEL_CLI_IP", None)),
        data=payload,
    )
    try:
        return Response(r.json())
    except:
        return Response(r.text)


@api_view(["POST"])
def whiteflag_encode(request):
    payload = json.dumps(
        {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": request.data["encryptionIndicator"],
            "duressIndicator": request.data["duressIndicator"],
            "messageCode": request.data["messageCode"],
            "referenceIndicator": request.data["referenceIndicator"],
            "referencedMessage": request.data["referencedMessage"],
            "verificationMethod": request.data["verificationMethod"],
            "verificationData": request.data["verificationData"],
            "cryptoDataType": request.data["cryptoDataType"],
            "cryptoData": request.data["cryptoData"],
            "text": request.data["text"],
            "resourceMethod": request.data["resourceMethod"],
            "resourceData": request.data["resourceData"],
            "pseudoMessageCode": request.data["pseudoMessageCode"],
            "subjectCode": request.data["subjectCode"],
            "datetime": request.data["datetime"],
            "duration": request.data["duration"],
            "objectType": request.data["objectType"],
            "objectLatitude": request.data["objectLatitude"],
            "objectLongitude": request.data["objectLongitude"],
            "objectSizeDim1": request.data["objectSizeDim1"],
            "objectSizeDim2": request.data["objectSizeDim2"],
            "objectOrientation": request.data["objectOrientation"],
            "objectTypeQuant": request.data["objectTypeQuant"],
        }
    )
    r = requests.post(
        "{0}/v1/whiteflag_encode".format(os.environ.get("FENNEL_CLI_IP", None)),
        data=payload,
    )
    try:
        return Response(r.json())
    except:
        return Response(r.text)


@api_view(["POST"])
def whiteflag_decode(request):
    payload = json.dumps(request.data["message"])
    r = requests.post(
        "{0}/v1/whiteflag_decode".format(os.environ.get("FENNEL_CLI_IP", None)),
        data=payload,
    )
    return Response(json.loads(r.json()))


@api_view(["GET"])
def whiteflag_generate_shared_token(request):
    r = {
        "sharedToken": str(uuid.uuid4()),
    }
    return Response(r)


@api_view(["POST"])
def whiteflag_generate_public_token(request):
    payload = json.dumps(
        {
            "sharedToken": request.data["sharedToken"],
            "address": request.data["address"],
        }
    )
    h = hashlib.sha3_512()
    h.update(payload.encode("utf-8"))
    r = h.hexdigest()
    return Response(r)
