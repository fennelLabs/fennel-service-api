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
from main.decorators import requires_mnemonic_created
from main.fennel_views import check_balance, record_signal_fee, signal_send_helper
from main.serializers import AnnotatedWhiteflagSignalSerializer

from main.models import Signal, UserKeys, ConfirmationRecord
from main.serializers import SignalSerializer
from main.whiteflag_views import whiteflag_encoder_helper


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
        timeout=5,
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
    response_json = []
    for signal in signals_list:
        signal_body = decode(signal.signal_text)
        if signal_body["encryptionIndicator"] != "1":
            signal.references.set(
                Signal.objects.filter(tx_hash=signal_body["referencedMessage"])
            )
        signal.save()
        response_json.append(
            {
                "id": signal.id,
                "tx_hash": signal.tx_hash,
                "timestamp": signal.timestamp,
                "mempool_timestamp": signal.mempool_timestamp,
                "signal_text": signal_body,
                "sender": {
                    "id": signal.sender.id,
                    "username": signal.sender.username,
                    "address": UserKeys.objects.get(user=signal.sender).address,
                },
                "synced": signal.synced,
                "references": SignalSerializer(signal.references, many=True).data,
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
        )
    return Response(
        response_json,
        status=200,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_send_signal_with_annotations(request):
    user_key = UserKeys.objects.get(user=request.user)
    serializer = AnnotatedWhiteflagSignalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    mnemonic = user_key.mnemonic
    signal_body = serializer.validated_data["signal_body"]
    annotations = serializer.validated_data["annotations"]
    signal_text_encoded = whiteflag_encoder_helper(signal_body)
    annotation_text_encoded = whiteflag_encoder_helper(annotations)
    payload = {
        "mnemonic": mnemonic,
        "content": signal_text_encoded,
    }
    payload_two = {
        "mnemonic": mnemonic,
        "content": annotation_text_encoded,
    }
    try:
        response, success = record_signal_fee(payload)
        response_two, success_two = record_signal_fee(payload_two)
        balance = check_balance(user_key)["balance"]
        if not success or not success_two:
            return Response(
                {
                    "signal_response": response,
                    "annotation_response": response_two,
                    "total_fee": response["fee"] + response_two["fee"],
                    "balance": balance,
                },
                status=400,
            )
        return Response(
            {
                "signal_response": response,
                "annotation_response": response_two,
                "total_fee": response["fee"] + response_two["fee"],
                "balance": balance,
            },
            status=200,
        )
    except requests.HTTPError:
        return Response(
            {
                "message": "could not get fees",
            },
            status=400,
        )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def send_signal_with_annotations(request):
    serializer = AnnotatedWhiteflagSignalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        serializer.validated_data["signal_body"]
    )
    if not signal_encode_success:
        return Response(
            {
                "message": "could not encode signal",
            },
            status=400,
        )
    signal = Signal.objects.create(
        signal_text=signal_text_encoded,
        sender=request.user,
    )
    signal_sent_response, signal_success = signal_send_helper(
        UserKeys.objects.get(user=request.user), signal
    )
    signal = Signal.objects.get(pk=signal.id)
    annotations_signal = {
        "messageCode": "F",
        "text": serializer.validated_data["annotations"],
        "referenceIndicator": "3",
        "referencedMessage": signal.tx_hash,
    }
    annotation_text_encoded, annotation_encode_success = whiteflag_encoder_helper(
        annotations_signal
    )
    if not annotation_encode_success:
        return Response(
            {
                "message": "could not encode annotation",
            },
            status=400,
        )
    annotation = Signal.objects.create(
        signal_text=annotation_text_encoded,
        sender=request.user,
    )
    signal.references.add(annotation)
    signal.save()
    if signal_success:
        annotation_sent_response, annotation_success = signal_send_helper(
            UserKeys.objects.get(user=request.user), annotation
        )
    if not signal_success:
        return Response(
            signal_sent_response,
            status=400,
        )
    if not annotation_success:
        return Response(
            {
                "signal_response": signal_sent_response,
                "annotation_response": annotation_sent_response,
            },
            status=400,
        )
    return Response(
        {
            "signal_response": signal_sent_response,
            "annotation_response": annotation_sent_response,
        },
        status=200,
    )
