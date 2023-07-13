from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from knox.auth import TokenAuthentication
import requests
import os

from main.models import UserKeys


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_keypair(request):
    try:
        r = requests.post(
            "{0}/v1/generate_encryption_channel".format(
                os.environ.get("FENNEL_CLI_IP", None)
            )
        )
        UserKeys.objects.update_or_create(
            user=request.user,
            public_diffie_hellman_key=r.json()["secret"],
            private_diffie_hellman_key=r.json()["public"],
        )
        return Response(
            {"success": "keypair created", "public_key": r.json()["public"]}
        )
    except Exception as e:
        return Response({"error": "keypair not created", "detail": str(e)})
