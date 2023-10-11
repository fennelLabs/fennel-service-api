import json

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

from silk.profiling.profiler import silk_profile

import requests
from main.decorators import requires_mnemonic_created
from main.fennel_views import check_balance, record_signal_fee, signal_send_helper
from main.serializers import (
    AnnotatedWhiteflagSignalSerializer,
    DecodeListSerializer,
    EncodeListSerializer,
    SignalTextSerializer,
)

from main.forms import SignalForm
from main.models import APIGroup, Signal, UserKeys
from main.signal_processors import process_decoding_signal
from main.whiteflag_helpers import whiteflag_encoder_helper


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def encode_list(request):
    serializer = EncodeListSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    signals = serializer.data["signals"]
    sender_group = request.user.api_group_users.first()
    recipient_group = serializer.data.get("recipient_group", None)
    processed = []
    for signal in signals:
        if not isinstance(signal, dict):
            valid_signal = signal.replace("'", '"')
            signal_dict = json.loads(valid_signal)
        else:
            signal_dict = signal
        signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
            signal_dict, sender_group, recipient_group
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
    serializer = DecodeListSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    signals = serializer.data["signals"]
    signals_list = Signal.objects.filter(
        pk__in=signals,
        signal_text__startswith="574631",
    )
    if len(signals_list) == 0:
        return Response({"message": "No signals found for the given list"}, status=400)
    response_json = []
    for signal in signals_list:
        response_json.append(process_decoding_signal(request.user, signal))
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
    signal_text_encoded = whiteflag_encoder_helper(signal_body)
    annotations_signal = {
        "messageCode": "F",
        "text": serializer.validated_data["annotations"],
        "referenceIndicator": "3",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    annotation_text_encoded = whiteflag_encoder_helper(annotations_signal)
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
    sender_group = None
    recipient_group = None
    if serializer.validated_data.get("recipient_group", None):
        sender_group = request.user.api_group_users.first()
        if APIGroup.objects.filter(
            name=serializer.validated_data["recipient_group"]
        ).exists():
            recipient_group = APIGroup.objects.get(
                name=serializer.validated_data["recipient_group"]
            )
        else:
            return Response(
                {
                    "message": "specified recipient group does not exist",
                },
                status=400,
            )
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        serializer.validated_data["signal_body"], sender_group, recipient_group
    )
    if not signal_encode_success:
        signal_text_encoded["step"] = "signal_encode"
        return Response(
            {
                "signal_response": signal_text_encoded,
            },
            status=400,
        )
    signal = Signal.objects.create(
        signal_text=signal_text_encoded,
        sender=request.user,
    )
    if recipient_group:
        signal.viewers.add(recipient_group)
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
        annotations_signal, sender_group, recipient_group
    )
    if not annotation_encode_success:
        return Response(
            {
                "signal_response": signal_sent_response,
                "annotation_response": annotation_text_encoded,
            },
            status=400,
        )
    annotation = Signal.objects.create(
        signal_text=annotation_text_encoded,
        sender=request.user,
    )
    if recipient_group:
        annotation.viewers.add(recipient_group)
    annotation.references.add(signal)
    annotation.save()
    annotation_sent_response = None
    annotation_success = False
    if signal_success:
        annotation_sent_response, annotation_success = signal_send_helper(
            UserKeys.objects.get(user=request.user), annotation
        )
    if not annotation_success or not signal_success:
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


@silk_profile(name="send_signal_list")
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
        if not isinstance(signal, dict):
            # Python dictionaries have single-quotes, JSON has double-quotes.
            # This makes sure that regardless of how the request was sent to us,
            # we can parse it as JSON.
            signal = signal.replace("'", '"')
            signal = json.loads(signal)
        form = SignalForm(
            {
                "signal": signal["signal"],
                "recipient_group": signal.get("recipient_group", None),
            }
        )
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
