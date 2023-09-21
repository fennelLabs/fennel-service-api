import json
import uuid
import hashlib
import os

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from silk.profiling.profiler import silk_profile

from django.http import Http404

from knox.auth import TokenAuthentication

import requests
from main.models import APIGroup

from main.whiteflag_helpers import (
    generate_shared_secret,
    whiteflag_encoder_helper,
    decode,
)


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
    result = whiteflag_encoder_helper(payload)
    if result[1]:
        return Response(result[0], 200)
    return Response(result[0], 400)


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
    result = whiteflag_encoder_helper(payload)
    if result[1]:
        return Response(result[0], 200)
    return Response(result[0], 400)


@api_view(["POST"])
def whiteflag_encode(request):
    result, success = whiteflag_encoder_helper(request.data)
    if success:
        return Response(result, 200)
    return Response(result, 400)


@silk_profile(name="whiteflag_generate_shared_secret_key")
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def whiteflag_generate_shared_secret_key(request, group_id=None):
    if group_id is None:
        return Response({"error": "group_id is required"})
    our_group = request.user.api_group_users.first()
    their_group = APIGroup.objects.get(id=group_id)
    shared_secret, success = generate_shared_secret(our_group, their_group)
    if success:
        return Response({"success": True, "shared_secret": shared_secret})
    return Response({"success": False, "error": "shared secret not generated"})


@silk_profile(name="whiteflag_decode")
@api_view(["POST"])
def whiteflag_decode(request):
    payload = json.dumps(request.data["message"])
    return Response(decode(payload))


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
    result = whiteflag_encoder_helper(payload)
    if result[1]:
        return Response(result[0], 200)
    return Response(result[0], 400)


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
