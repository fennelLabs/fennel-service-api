import os
import json

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

import requests

from main.models import Signal, UserKeys, ConfirmationRecord


def decode(signal: str) -> dict:
    if signal[7] == "1":
        return {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "1",
            "signal_body": signal[8:],
        }
    signal = json.dumps(signal)
    response = requests.post(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/whiteflag_decode",
        data=signal,
    )
    return json.loads(response.json())


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def decode_list(request):
    try:
        signals = request.data.getlist("signals")
    except AttributeError:
        signals = request.data.get("signals")
    if signals is None:
        return Response({"message": "No signals given"}, status=400)
    signals_list = Signal.objects.filter(
        pk__in=signals,
        signal_text__startswith="574631",
    )
    if len(signals_list) == 0:
        return Response({"message": "No signals found for the given list"}, status=400)
    return Response(
        [
            {
                "id": signal.id,
                "tx_hash": signal.tx_hash,
                "timestamp": signal.timestamp,
                "mempool_timestamp": signal.mempool_timestamp,
                "signal_text": decode(signal.signal_text),
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
            for signal in signals_list
        ]
    )
