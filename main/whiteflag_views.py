from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
import json


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
    r = requests.post("http://localhost:9031/v1/whiteflag_encode", data=payload)
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
    r = requests.post("http://localhost:9031/v1/whiteflag_encode", data=payload)
    return Response(r.text)


@api_view(["POST"])
def whiteflag_encode(request):
    payload = json.dumps({
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
    })
    r = requests.post("http://localhost:9031/v1/whiteflag_encode", data=payload)
    try:
        return Response(r.json())
    except:
        return Response(r.text)


@api_view(["POST"])
def whiteflag_decode(request):
    payload = json.dumps(request.data["message"])
    r = requests.post("http://localhost:9031/v1/whiteflag_decode", data=payload)
    return Response(r.json())
