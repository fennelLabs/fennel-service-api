import json

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from knox.auth import TokenAuthentication

from main.decorators import silk_profile

import requests
from main.decorators import requires_mnemonic_created
from main.fennel_views import check_balance, record_signal_fee, signal_send_helper
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
        
        # Sanitize the response to only include safe fields
        sanitized_response = {
            "fee": response.get("fee") if isinstance(response, dict) else None,
        }
        
        return Response(
            {
                "signal_response": sanitized_response,
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
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        serializer.validated_data["signal_body"], sender_group, recipient_group
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
    signal_sent_response, signal_success = signal_send_helper(
        UserKeys.objects.get(user=request.user), signal
    )
    if not signal_success:
        # Sanitize the response to only include safe fields
        sanitized_response = {
            "error": "Signal sending failed",
            "signal_id": signal_sent_response.get("signal_id"),
            "synced": signal_sent_response.get("synced", False),
        }
        # Only include balance and fee if they exist and are safe
        if "balance" in signal_sent_response:
            sanitized_response["balance"] = signal_sent_response["balance"]
        if "fee" in signal_sent_response:
            sanitized_response["fee"] = signal_sent_response["fee"]
        
        return Response(
            sanitized_response,
            status=400,
        )
    
    # Sanitize the successful response to only include safe fields
    sanitized_success_response = {
        "hash": signal_sent_response.get("hash"),
        "balance": signal_sent_response.get("balance"),
        "signal_id": signal_sent_response.get("signal_id"),
        "synced": signal_sent_response.get("synced", True),
    }
    
    return Response(
        sanitized_success_response,
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
    signal_body = serializer.validated_data["signal_body"]
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(signal_body)
    if not signal_encode_success:
        return Response(
            {
                "error": "Failed to encode signal",
                "step": "signal_encode"
            },
            status=400,
        )
    
    annotations_signal = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "text": serializer.validated_data["annotations"],
        "referenceIndicator": "3",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    annotation_text_encoded, annotation_encode_success = whiteflag_encoder_helper(annotations_signal)
    if not annotation_encode_success:
        return Response(
            {
                "error": "Failed to encode annotation",
                "step": "annotation_encode"
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
            # Sanitize responses to only include safe fields
            # Extract only the fee fields to avoid exposing sensitive data
            signal_fee = response.get("fee", 0) if response and "fee" in response else 0
            annotation_fee = response_two.get("fee", 0) if response_two and "fee" in response_two else 0
            
            sanitized_signal_response = {
                "error": "Signal fee calculation failed" if not success else None,
                "fee": signal_fee,
            }
            sanitized_annotation_response = {
                "error": "Annotation fee calculation failed" if not success_two else None,
                "fee": annotation_fee,
            }
            
            return Response(
                {
                    "signal_response": sanitized_signal_response,
                    "annotation_response": sanitized_annotation_response,
                    "total_fee": signal_fee + annotation_fee,
                    "balance": balance,
                },
                status=400,
            )
        # Sanitize successful responses to only include safe fields
        # Extract only the fee fields to avoid exposing sensitive data
        signal_fee_success = response.get("fee", 0) if response and "fee" in response else 0
        annotation_fee_success = response_two.get("fee", 0) if response_two and "fee" in response_two else 0
        
        sanitized_signal_success = {
            "fee": signal_fee_success,
        }
        sanitized_annotation_success = {
            "fee": annotation_fee_success,
        }
        
        return Response(
            {
                "signal_response": sanitized_signal_success,
                "annotation_response": sanitized_annotation_success,
                "total_fee": response.get("fee", 0) + response_two.get("fee", 0),
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
    signal_text_encoded, signal_encode_success = whiteflag_encoder_helper(
        serializer.validated_data["signal_body"], sender_group, recipient_group
    )
    if not signal_encode_success:
        # Sanitize the response to only include safe fields
        sanitized_response = {
            "error": "Failed to encode signal",
            "step": "signal_encode"
        }
        return Response(
            {
                "signal_response": sanitized_response,
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
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "F",
        "text": serializer.validated_data["annotations"],
        "referenceIndicator": "3",
        "referencedMessage": signal.tx_hash,
    }
    annotation_text_encoded, annotation_encode_success = whiteflag_encoder_helper(
        annotations_signal, sender_group, recipient_group
    )
    if not annotation_encode_success:
        # Sanitize the annotation response to only include safe fields
        sanitized_annotation_response = {
            "error": "Failed to encode annotation",
            "step": "annotation_encode"
        }
        # Sanitize the signal response to only include safe fields
        sanitized_signal_response = {
            "error": "Signal sending failed" if signal_sent_response else "Signal failed",
            "signal_id": signal_sent_response.get("signal_id") if signal_sent_response else None,
            "synced": signal_sent_response.get("synced", False) if signal_sent_response else False,
        }
        
        return Response(
            {
                "signal_response": sanitized_signal_response,
                "annotation_response": sanitized_annotation_response,
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
        # Sanitize responses to only include safe fields
        sanitized_signal_response = {
            "error": "Signal sending failed" if signal_sent_response else "Signal failed",
            "signal_id": signal_sent_response.get("signal_id") if signal_sent_response else None,
            "synced": signal_sent_response.get("synced", False) if signal_sent_response else False,
        }
        sanitized_annotation_response = {
            "error": "Annotation sending failed" if annotation_sent_response else "Annotation failed",
            "signal_id": annotation_sent_response.get("signal_id") if annotation_sent_response else None,
            "synced": annotation_sent_response.get("synced", False) if annotation_sent_response else False,
        }
        
        return Response(
            {
                "signal_response": sanitized_signal_response,
                "annotation_response": sanitized_annotation_response,
            },
            status=400,
        )
    # Sanitize successful responses to only include safe fields
    # Extract only the specific fields we need to avoid exposing sensitive data
    signal_hash = signal_sent_response.get("hash") if signal_sent_response and "hash" in signal_sent_response else None
    signal_balance = signal_sent_response.get("balance") if signal_sent_response and "balance" in signal_sent_response else None
    signal_id = signal_sent_response.get("signal_id") if signal_sent_response and "signal_id" in signal_sent_response else None
    signal_synced = signal_sent_response.get("synced", True) if signal_sent_response else True
    
    annotation_hash = annotation_sent_response.get("hash") if annotation_sent_response and "hash" in annotation_sent_response else None
    annotation_balance = annotation_sent_response.get("balance") if annotation_sent_response and "balance" in annotation_sent_response else None
    annotation_id = annotation_sent_response.get("signal_id") if annotation_sent_response and "signal_id" in annotation_sent_response else None
    annotation_synced = annotation_sent_response.get("synced", True) if annotation_sent_response else True
    
    sanitized_signal_success = {
        "hash": signal_hash,
        "balance": signal_balance,
        "signal_id": signal_id,
        "synced": signal_synced,
    }
    sanitized_annotation_success = {
        "hash": annotation_hash,
        "balance": annotation_balance,
        "signal_id": annotation_id,
        "synced": annotation_synced,
    }
    
    return Response(
        {
            "signal_response": sanitized_signal_success,
            "annotation_response": sanitized_annotation_success,
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
    # Get user key once to avoid repeated database queries and potential exposure
    user_key = UserKeys.objects.get(user=request.user)
    user_mnemonic = user_key.mnemonic
    
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
            # Create payload with extracted mnemonic to minimize exposure risk
            payload = {
                "mnemonic": user_mnemonic,
                "content": form.cleaned_data["signal"],
            }
            fee_response, fee_success = record_signal_fee(payload)
            # Sanitize the fee response to only include safe fields
            # Extract only the fee field to avoid exposing sensitive data
            fee_amount = fee_response.get("fee", 0) if fee_response and "fee" in fee_response else 0
            sanitized_message = {
                "error": "Fee calculation failed" if not fee_success else None,
                "fee": fee_amount,
            }
            
            processed.append(
                {
                    "signal": signal,
                    "success": fee_success,
                    "message": sanitized_message,
                    "fee": fee_amount,
                }
            )
    return Response(
        {
            "signals": processed,
            "total_fee": sum(signal["fee"] for signal in processed),
            "balance": check_balance(user_key)["balance"],
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
        # Validate and sanitize signal data before form processing
        if not isinstance(signal, dict):
            # If signal is not a dict, create a safe representation
            signal_data = {
                "signal": str(signal)[:100] + "..." if len(str(signal)) > 100 else str(signal),
                "recipient_group": None,
            }
        else:
            # Extract only safe fields from the signal data
            signal_data = {
                "signal": signal.get("signal", ""),
                "recipient_group": signal.get("recipient_group", None),
            }
        
        form = SignalForm(signal_data)
        if not form.is_valid():
            # Use the already sanitized signal data
            sanitized_signal = signal_data
            processed.append(
                {
                    "signal": sanitized_signal,
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
            # Sanitize the response to only include safe fields
            sanitized_message = {
                "error": "Signal sending failed" if not signal_success else None,
                "hash": signal_sent_response.get("hash") if signal_success else None,
                "balance": signal_sent_response.get("balance"),
                "signal_id": signal_sent_response.get("signal_id"),
                "synced": signal_sent_response.get("synced", signal_success),
            }
            
            # Use the already sanitized signal data
            sanitized_signal_success = signal_data
            
            processed.append(
                {
                    "signal": sanitized_signal_success,
                    "success": signal_success,
                    "message": sanitized_message,
                }
            )
    return Response(
        processed,
        status=200,
    )


@silk_profile(name="get_fee_for_discontinue_signal")
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
            # Sanitize the error response to only include safe fields
            # Extract only the fee field to avoid exposing sensitive data
            fee_amount_error = response.get("fee", 0) if response and "fee" in response else 0
            sanitized_error_response = {
                "error": "Fee calculation failed",
                "fee": fee_amount_error,
            }
            return Response(
                {
                    "signal_response": sanitized_error_response,
                    "balance": balance,
                },
                status=400,
            )
        
        # Sanitize the successful response to only include safe fields
        # Extract only the fee field to avoid exposing sensitive data
        fee_amount_success = response.get("fee", 0) if response and "fee" in response else 0
        sanitized_success_response = {
            "fee": fee_amount_success,
        }
        
        return Response(
            {
                "signal_response": sanitized_success_response,
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


@silk_profile(name="discontinue_signal")
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
    signal_sent_response, signal_success = signal_send_helper(
        UserKeys.objects.get(user=request.user), discontinue_signal
    )
    if not signal_success:
        # Sanitize the error response to only include safe fields
        sanitized_error_response = {
            "error": "Signal sending failed",
            "signal_id": signal_sent_response.get("signal_id"),
            "synced": signal_sent_response.get("synced", False),
        }
        return Response(
            sanitized_error_response,
            status=400,
        )
    
    signal.active = False
    signal.save()
    
    # Sanitize the successful response to only include safe fields
    sanitized_success_response = {
        "hash": signal_sent_response.get("hash"),
        "balance": signal_sent_response.get("balance"),
        "signal_id": signal_sent_response.get("signal_id"),
        "synced": signal_sent_response.get("synced", True),
    }
    
    return Response(
        sanitized_success_response,
        status=200,
    )
