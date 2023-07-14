import requests
import os
import json
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from knox.auth import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import Signal, UserKeys, ConfirmationRecord


def __decode(signal: str) -> dict:
    if signal[7] == "1":
        return {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "1",
            "signal_body": signal[8:],
        }
    else:
        signal = json.dumps(signal)
        r = requests.post(
            "{0}/v1/whiteflag_decode".format(os.environ.get("FENNEL_CLI_IP", None)),
            data=signal,
        )
        return json.loads(r.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def decode_list(request):
    print(request.data)
    print(request.data.getlist("signals"))
    signals = request.data.getlist("signals")
    print(signals)
    return Response(
        [
            {
                "id": signal.id,
                "tx_hash": signal.tx_hash,
                "timestamp": signal.timestamp,
                "mempool_timestamp": signal.mempool_timestamp,
                "signal_text": __decode(signal.signal_text),
                "sender": {
                    "id": signal.sender.id,
                    "username": signal.sender.username,
                    "address": UserKeys.objects.get(user=signal.sender).address,
                },
                "synced": signal.synced,
                "confirmations": [
                    {
                        "id": confirmation.id,
                        "timestamp": confirmation.timestamp,
                        "confirming_user": {
                            "id": confirmation.confirmer.id,
                            "username": confirmation.confirmer.username,
                        },
                    }
                    for confirmation in ConfirmationRecord.objects.filter(signal=signal)
                ],
            }
            for signal in Signal.objects.filter(pk__in=signals)
        ]
    )
