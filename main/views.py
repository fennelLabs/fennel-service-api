from knox.views import LoginView as KnoxLoginView
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
import requests


@api_view()
@permission_classes([IsAuthenticated])
def whiteflag_authenticate(request):
    payload = {
        "verificationMethod": request.data['verificationMethod'],
        "verificationData": request.data['verificationData'],
    }
    r = requests.post("http://localhost:6060/whiteflag/authenticate", data=payload)
    return Response(r.json())


@api_view()
def whiteflag_discontinue_authentication(request):
    payload = {
        "referencedMessage": request.data['referencedMessage'],
        "verificationMethod": request.data['verificationMethod'],
        "verificationData": request.data['verificationData'],
    }
    r = requests.post(
        "http://localhost:6060/whiteflag/discontinue_authentication", data=payload
    )
    return Response(r.json())


@api_view(["POST"])
def whiteflag_encode(request):
    payload = {
        "encryptionIndicator": request.data['encryptionIndicator'],
        "duressIndicator": request.data['duressIndicator'],
        "messageCode": request.data['messageCode'],
        "referenceIndicator": request.data['referenceIndicator'],
        "referencedMessage": request.data['referencedMessage'],
        "verificationMethod": request.data['verificationMethod'],
        "verificationData": request.data['verificationData'],
        "cryptoDataType": request.data['cryptoDataType'],
        "cryptoData": request.data['cryptoData'],
        "text": request.data['text'],
        "resourceMethod": request.data['resourceMethod'],
        "resourceData": request.data['resourceData'],
        "pseudoMessageCode": request.data['pseudoMessageCode'],
        "subjectCode": request.data['subjectCode'],
        "dateTime": request.data['dateTime'],
        "duration": request.data['duration'],
        "objectType": request.data['objectType'],
        "objectLatitude": request.data['objectLatitude'],
        "objectLongitude": request.data['objectLongitude'],
        "objectSizeDim1": request.data['objectSizeDim1'],
        "objectSizeDim2": request.data['objectSizeDim2'],
        "objectOrientation": request.data['objectOrientation'],
        "objectTypeQuant": request.data['objectTypeQuant'],
    }
    r = requests.post("http://localhost:6060/whiteflag/encode", data=payload)
    return Response(r.json())


@api_view()
def whiteflag_decode(request):
    payload = {"message": request.data['message']}
    r = requests.post("http://localhost:6060/whiteflag/decode", data=payload)
    return Response(r.json())


@api_view()
def create_account(request):
    r = requests.get("http://localhost:6060/create_account")
    mnemonic = r.json()["mnemonic"]
    r = requests.post(
        "http://localhost:1235/api/keys",
        data={"user": request.user.username, "mnemonic": mnemonic},
    )
    return Response(r.json())


@api_view()
def get_account_balance(request):
    payload = {"mnemonic": request.data['mnemonic']}
    r = requests.post("http://localhost:6060/get_account_balance", data=payload)
    return Response(r.json())


@api_view()
def get_fee_for_new_signal(request):
    r = requests.get("http://localhost:1235/api/keys?user={}", request.user.username)
    mnemonic_from_database = r.json()["mnemonic"]
    payload = {"mnemonic": mnemonic_from_database, "content": request.data['content']}
    r = requests.post("http://localhost:6060/get_fee_for_new_signal", data=payload)
    return Response(r.json())


@api_view()
def send_new_signal(request):
    r = requests.get("http://localhost:1235/api/keys?user={}", request.user.username)
    mnemonic_from_database = r.json()["mnemonic"]
    payload = {"mnemonic": mnemonic_from_database, "content": request.data['content']}
    r = requests.post("http://localhost:6060/send_new_signal", data=payload)
    return Response(r.json())


@api_view()
def get_signal_history(request):
    r = requests.get("http://localhost:6060/get_signal_history")
    return Response(r.json())
