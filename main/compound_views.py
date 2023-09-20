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
from main.serializers import (
    AnnotatedWhiteflagSignalSerializer,
    ConfirmationRecordSerializer,
    SignalTextSerializer,
    UserSerializer,
)

from main.forms import SignalForm
from main.models import ConfirmationRecord, Signal, UserKeys
from main.serializers import SignalSerializer
from main.whiteflag_helpers import decode
from main.whiteflag_helpers import whiteflag_encoder_helper


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def encode_list(request):
    try:
        signals = request.data.getlist("signals")
    except AttributeError:
        signals = request.data.get("signals")
    if signals is None:
        return Response({"message": "No signals given"}, status=400)
    processed = []
    for signal in signals:
        if not isinstance(signal, dict):
            valid_signal = signal.replace("'", '"')
            signal_dict = json.loads(valid_signal)
        else:
            signal_dict = signal
        signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
            signal_dict
        )
        processed.append(
            {
                "signal": signal_text_encoded,
                "success": signal_encode_success,
                "message": "signal encoded",
            }
        )
    return Response(
        processed,
        status=200,
    )


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
        signal_body, success = decode(signal.signal_text)
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
                "signal_text": signal_body if success else signal.signal_text,
                "sender": UserSerializer(signal.sender).data,
                "synced": signal.synced,
                "references": SignalSerializer(signal.references, many=True).data,
                "confirmations": ConfirmationRecordSerializer(
                    ConfirmationRecord.objects.filter(signal=signal), many=True
                ).data,
                "decoded": success,
                "error": signal_body["error"] if not success else None,
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


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_send_signal_list(request):
    serializer = SignalTextSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    signals = serializer.data["signals"]
    if signals is None:
        return Response({"message": "No signals given"}, status=400)
    processed = []
    for signal in signals:
        form = SignalForm({"signal": signal})
        if not form.is_valid():
            processed.append(
                {
                    "signal": signal,
                    "success": False,
                    "message": form.errors,
                    "fee": 0,
                }
            )
        else:
            payload = {
                "mnemonic": UserKeys.objects.get(user=request.user).mnemonic,
                "content": form.cleaned_data["signal"],
            }
            fee_response, fee_success = record_signal_fee(payload)
            processed.append(
                {
                    "signal": signal,
                    "success": fee_success,
                    "message": fee_response,
                    "fee": fee_response["fee"],
                }
            )
    return Response(
        {
            "signals": processed,
            "total_fee": sum(signal["fee"] for signal in processed),
            "balance": check_balance(UserKeys.objects.get(user=request.user))[
                "balance"
            ],
        },
        status=200,
    )


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def send_signal_list(request):
    serializer = SignalTextSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    signals = serializer.data["signals"]
    if signals is None:
        return Response({"message": "No signals given"}, status=400)
    processed = []
    for signal in signals:
        form = SignalForm({"signal": signal})
        if not form.is_valid():
            processed.append(
                {
                    "signal": signal,
                    "success": False,
                    "message": form.errors,
                }
            )
        else:
            signal_object = Signal.objects.create(
                signal_text=form.cleaned_data["signal"],
                sender=request.user,
            )
            signal_sent_response, signal_success = signal_send_helper(
                UserKeys.objects.get(user=request.user), signal_object
            )
            processed.append(
                {
                    "signal": signal,
                    "success": signal_success,
                    "message": signal_sent_response,
                }
            )
    return Response(
        processed,
        status=200,
    )
