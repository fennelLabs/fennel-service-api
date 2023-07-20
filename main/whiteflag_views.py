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
    json_packet = {"prefix": "WF", "version": "1"}
    json_packet["encryptionIndicator"] = request.data.get("encryptionIndicator", None)
    json_packet["duressIndicator"] = request.data.get("duressIndicator", None)
    json_packet["messageCode"] = request.data.get("messageCode", None)
    json_packet["referenceIndicator"] = request.data.get("referenceIndicator", None)
    json_packet["referencedMessage"] = request.data.get("referencedMessage", None)
    json_packet["verificationMethod"] = request.data.get("verificationMethod", None)
    json_packet["verificationData"] = request.data.get("verificationData", None)
    json_packet["cryptoDataType"] = request.data.get("cryptoDataType", None)
    json_packet["cryptoData"] = request.data.get("cryptoData", None)
    json_packet["text"] = request.data.get("text", None)
    json_packet["resourceMethod"] = request.data.get("resourceMethod", None)
    json_packet["resourceData"] = request.data.get("resourceData", None)
    json_packet["pseudoMessageCode"] = request.data.get("pseudoMessageCode", None)
    json_packet["subjectCode"] = request.data.get("subjectCode", None)
    json_packet["datetime"] = request.data.get("datetime", None)
    json_packet["duration"] = request.data.get("duration", None)
    json_packet["objectType"] = request.data.get("objectType", None)
    json_packet["objectLatitude"] = request.data.get("objectLatitude", None)
    json_packet["objectLongitude"] = request.data.get("objectLongitude", None)
    json_packet["objectSizeDim1"] = request.data.get("objectSizeDim1", None)
    json_packet["objectSizeDim2"] = request.data.get("objectSizeDim2", None)
    json_packet["objectOrientation"] = request.data.get("objectOrientation", None)
    json_packet["objectTypeQuant"] = request.data.get("objectTypeQuant", None)
    payload = json.dumps({k: v for k, v in json_packet.items() if v})
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
