import json

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

# from silk.profiling.profiler import silk_profile  # DISABLED: Silk removed

import requests
from main.decorators import requires_mnemonic_created
from main.fennel_views import check_balance, record_signal_fee, signal_send_helper, signal_send_with_blockchain_data_helper
from main.serializers import (
    AnnotatedWhiteflagSignalSerializer,
    DecodeListSerializer,
    EncodeAndSendSignalSerializer,
    EncodeListSerializer,
    SignalTextSerializer,
)

from main.forms import SignalForm
from main.models import APIGroup, Signal, UserKeys
from main.signal_processors import process_decoding_signal
from main.whiteflag_helpers import whiteflag_encoder_helper, decode


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_encode_and_send_signal(request):
    user_key = UserKeys.objects.get(user=request.user)
    serializer = EncodeAndSendSignalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    mnemonic = user_key.mnemonic
    signal_body = serializer.validated_data["signal_body"]
    signal_text_encoded = whiteflag_encoder_helper(signal_body)
    payload = {
        "mnemonic": mnemonic,
        "content": signal_text_encoded,
    }
    try:
        response, success = record_signal_fee(payload)
        balance = check_balance(user_key)["balance"]
        if not success:
            return Response(
                {
                    "signal_response": response,
                    "balance": balance,
                },
                status=400,
            )
        return Response(
            {
                "signal_response": response,
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
def encode_and_send_signal(request):
    serializer = EncodeAndSendSignalSerializer(data=request.data)
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
    
    # Handle test message conversion if requested (admin only)
    signal_body = serializer.validated_data["signal_body"]
    if serializer.validated_data.get("is_test_message", False):
        # Only allow admins to create test messages
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "error": "Only administrators can create test messages",
                    "detail": "The is_test_message parameter requires admin privileges"
                },
                status=403,
            )
        from main.whiteflag_helpers import convert_to_test_message
        signal_body = convert_to_test_message(signal_body)
    
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        signal_body, sender_group, recipient_group
    )
    if not signal_encode_success:
        signal_text_encoded["step"] = "signal_encode"
        return Response(
            signal_text_encoded,
            status=400,
        )
    signal = Signal.objects.create(
        signal_text=signal_text_encoded,
        sender=request.user,
    )
    if recipient_group:
        signal.viewers.add(recipient_group)
    signal_sent_response, signal_success = signal_send_with_blockchain_data_helper(
        UserKeys.objects.get(user=request.user), signal
    )
    if not signal_success:
        return Response(
            signal_sent_response,
            status=400,
        )
    return Response(
        signal_sent_response,
        status=200,
    )


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
        response_json.append(process_decoding_signal(request.user, signal, depth=0))
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
    
    # Handle test message conversion if requested (admin only)
    signal_body = serializer.validated_data["signal_body"]
    if serializer.validated_data.get("is_test_message", False):
        # Only allow admins to create test messages
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "error": "Only administrators can create test messages",
                    "detail": "The is_test_message parameter requires admin privileges"
                },
                status=403,
            )
        from main.whiteflag_helpers import convert_to_test_message
        signal_body = convert_to_test_message(signal_body)
    
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(signal_body)
    if not signal_encode_success:
        return Response(
            {
                "error": "Failed to encode main signal",
                "details": signal_text_encoded
            },
            status=400,
        )
    
    # For test messages, pass annotations through unchanged
    # Users should manually add visual indicators to their annotation text if desired
    annotations_text = serializer.validated_data["annotations"]
    
    annotations_signal = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "text": annotations_text,
        "referenceIndicator": "3",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    
    # Apply test message conversion to annotation if the main signal was a test
    if serializer.validated_data.get("is_test_message", False):
        from main.whiteflag_helpers import convert_to_test_message
        annotations_signal = convert_to_test_message(annotations_signal)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG: Annotation signal after conversion: {annotations_signal}")
    
    annotation_text_encoded, annotation_encode_success = whiteflag_encoder_helper(annotations_signal)
    if not annotation_encode_success:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG: Annotation encoding failed: {annotation_text_encoded}")
        return Response(
            {
                "error": "Failed to encode annotation signal",
                "details": annotation_text_encoded
            },
            status=400,
        )
    
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
    recipient_group = serializer.validated_data.get("recipient_group", None)
    if recipient_group and recipient_group != "":
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
    
    # Handle test message conversion if requested (admin only)
    signal_body = serializer.validated_data["signal_body"]
    if serializer.validated_data.get("is_test_message", False):
        # Only allow admins to create test messages
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {
                    "error": "Only administrators can create test messages",
                    "detail": "The is_test_message parameter requires admin privileges"
                },
                status=403,
            )
        from main.whiteflag_helpers import convert_to_test_message
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG send_signal: Original signal_body: {signal_body}")
        signal_body = convert_to_test_message(signal_body)
        logger.error(f"DEBUG send_signal: Converted signal_body: {signal_body}")
    
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        signal_body, sender_group, recipient_group
    )
    if not signal_encode_success:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG send_signal: Main signal encoding failed: {signal_text_encoded}")
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
    signal_sent_response, signal_success = signal_send_with_blockchain_data_helper(
        UserKeys.objects.get(user=request.user), signal
    )
    # After helper, signal might have been replaced due to race condition
    # Get the actual signal ID from the response (fix from oct282025fix.md)
    if signal_success and "signal_id" in signal_sent_response:
        signal = Signal.objects.get(pk=signal_sent_response["signal_id"])
    else:
        # If not successful, try to get the original signal (might have been deleted)
        try:
            signal = Signal.objects.get(pk=signal.id)
        except Signal.DoesNotExist:
            # Signal was deleted in race condition handling, but we don't have the new ID
            return Response(
                {"error": "Signal was created but could not be retrieved", "details": signal_sent_response},
                status=500,
            )
    
    annotations_signal = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "text": serializer.validated_data["annotations"],
        "referenceIndicator": "3",
        "referencedMessage": signal.tx_hash,
    }
    
    # Apply test message conversion to annotation if the main signal was a test
    if serializer.validated_data.get("is_test_message", False):
        from main.whiteflag_helpers import convert_to_test_message
        annotations_signal = convert_to_test_message(annotations_signal)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG send_signal: Annotation signal after conversion: {annotations_signal}")
    
    annotation_text_encoded, annotation_encode_success = whiteflag_encoder_helper(
        annotations_signal, sender_group, recipient_group
    )
    
    if not annotation_encode_success:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"DEBUG send_signal: Annotation encoding failed: {annotation_text_encoded}")
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
        annotation_sent_response, annotation_success = signal_send_with_blockchain_data_helper(
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


# @silk_profile(name="send_signal_list")  # DISABLED: Silk removed
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
            signal_sent_response, signal_success = signal_send_with_blockchain_data_helper(
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


# @silk_profile(name="get_fee_for_discontinue_signal")  # DISABLED: Silk removed
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def get_fee_for_discontinue_signal(request, signal_id=None):
    user_key = UserKeys.objects.get(user=request.user)
    signal = Signal.objects.get(pk=signal_id)
    mnemonic = user_key.mnemonic
    signal_text_encoded = signal.signal_text
    signal_text, decode_success = decode(signal_text_encoded)
    if not decode_success:
        return Response(
            {"message": "signal could not be decoded"},
            status=400,
        )
    discontinue_signal = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": signal_text["messageCode"],
        "text": signal_text["text"],
        "referenceIndicator": "4",
        "referencedMessage": signal.tx_hash,
    }
    discontinue_text_encoded = whiteflag_encoder_helper(discontinue_signal)
    payload = {
        "mnemonic": mnemonic,
        "content": discontinue_text_encoded,
    }
    try:
        response, success = record_signal_fee(payload)
        balance = check_balance(user_key)["balance"]
        if not success:
            return Response(
                {
                    "signal_response": response,
                    "balance": balance,
                },
                status=400,
            )
        return Response(
            {
                "signal_response": response,
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


# @silk_profile(name="discontinue_signal")  # DISABLED: Silk removed
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@requires_mnemonic_created
def discontinue_signal(request, signal_id=None):
    signal = Signal.objects.get(pk=signal_id)
    signal_text_encoded = signal.signal_text
    signal_text, decode_success = decode(signal_text_encoded)
    if not decode_success:
        return Response(
            {"message": "signal could not be decoded"},
            status=400,
        )
    discontinue_signal = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": signal_text["messageCode"],
        "text": signal_text["text"],
        "referenceIndicator": "4",
        "referencedMessage": signal.tx_hash,
    }
    discontinue_text_encoded = whiteflag_encoder_helper(discontinue_signal)
    discontinue_signal = Signal.objects.create(
        signal_text=discontinue_text_encoded,
        sender=request.user,
    )
    discontinue_signal.references.add(signal)
    discontinue_signal.save()
    signal_sent_response, signal_success = signal_send_with_blockchain_data_helper(
        UserKeys.objects.get(user=request.user), discontinue_signal
    )
    if not signal_success:
        return Response(
            signal_sent_response,
            status=400,
        )
    signal.active = False
    signal.save()
    return Response(
        signal_sent_response,
        status=200,
    )
