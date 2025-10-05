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
        response.raise_for_status()
        response_data = response.json()
        if "secret" not in response_data or "public" not in response_data:
            return Response(
                {"error": "keypair not created: incomplete response from service"},
                status=400
            )
        group = APIGroup.objects.get(api_key=request.data.get("api_key", None))
        group.public_diffie_hellman_key = response_data["secret"]
        group.private_diffie_hellman_key = response_data["public"]
        group.save()
        return Response(response_data)
    except (requests.RequestException, requests.JSONDecodeError, KeyError) as e:
        return Response({"error": f"keypair not created: {str(e)}"}, status=400)


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
