import os

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from knox.auth import TokenAuthentication

import requests

from main.decorators import apigroup_admin_only, subject_to_api_limit
from main.models import APIGroup
from main.serializers import PublicAPIGroupSerializer


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_group_list(request):
    return Response(
        PublicAPIGroupSerializer(APIGroup.objects.all(), many=True).data, status=200
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
@apigroup_admin_only
def generate_apigroup_keypair(request):
    try:
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/generate_encryption_channel",
            timeout=5,
        )
        group = APIGroup.objects.get(api_key=request.data.get("api_key", None))
        group.public_diffie_hellman_key = response.json()["secret"]
        group.private_diffie_hellman_key = response.json()["public"]
        group.save()
        return Response(response.json())
    except requests.HTTPError:
        return Response({"error": "keypair not created"}, status=400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@subject_to_api_limit
@apigroup_admin_only
def get_apigroup_keypair(request):
    public_key = APIGroup.objects.get(
        api_key=request.data.get("api_key", None)
    ).public_diffie_hellman_key
    private_key = APIGroup.objects.get(
        api_key=request.data.get("api_key", None)
    ).private_diffie_hellman_key
    if public_key is None or private_key is None:
        return Response({"error": "keypair not created"}, status=400)
    return Response(
        {
            "public": public_key,
            "secret": private_key,
        },
        status=200,
    )
