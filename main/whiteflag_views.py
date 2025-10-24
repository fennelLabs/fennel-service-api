import json
import uuid
import hashlib
import os

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# from silk.profiling.profiler import silk_profile  # DISABLED: Silk removed from production

from django.http import Http404

from knox.auth import TokenAuthentication

import requests
from main.forms import WhiteflagDecodeForm
from main.models import APIGroup

from main.whiteflag_helpers import (
    generate_shared_secret,
    whiteflag_encoder_helper,
    decode,
    check_authentication_status,
)

@api_view(["GET"])
def fennel_cli_healthcheck(request):
    response = requests.get(
        f"{os.environ.get('FENNEL_CLI_IP', None)}/v1/hello_there/", timeout=5
    )
    if response.status_code == 200:
        return Response("Ok")
    raise Http404


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def whiteflag_authenticate(request):
    """
    Submits A(0) initial authentication message.
    
    Per Whiteflag spec 5.1.1: "Each account should be identified by sending 
    an A(0) initial authentication message, before sending any other message."
    
    Required Parameters:
        - verificationMethod: "1" for URL validation, "2" for shared token
        - verificationData: URL string (Method 1) or token string (Method 2)
    """
    verification_method = request.data.get("verificationMethod")
    verification_data = request.data.get("verificationData")
    
    if not verification_method or not verification_data:
        return Response(
            {
                "error": "Missing required fields",
                "required": ["verificationMethod", "verificationData"],
                "verificationMethod_options": ["1", "2"],
                "verificationMethod_description": "1=URL validation, 2=Shared token"
            },
            status=400
        )
    
    # Use the helper function to submit A(0)
    from main.whiteflag_helpers import submit_initial_authentication
    
    result, success = submit_initial_authentication(
        user=request.user,
        verification_method=verification_method,
        verification_data=verification_data
    )
    
    if success:
        return Response(result, 200)
    return Response(result, 400)


@api_view(["GET", "POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def whiteflag_authentication_status(request):
    """
    Check if user has active A(0) authentication.
    
    Returns authentication status and details. Supports multiple authentications.
    Returns the most recent active authentication if multiple exist.
    """
    from main.models import WhiteflagAuthentication
    
    # Get most recent active authentication
    # Optimize with select_related to prevent N+1 queries
    auth = WhiteflagAuthentication.objects.select_related('user').filter(
        user=request.user,
        is_active=True
    ).order_by('-timestamp').first()
    
    if auth:
        # Count total authentications for this user
        auth_count = WhiteflagAuthentication.objects.filter(
            user=request.user
        ).count()
        
        return Response({
            "isAuthenticated": True,
            "verificationMethod": auth.verification_method,
            "verificationData": auth.verification_data,
            "ecdhPublicKey": auth.ecdh_public_key,
            "timestamp": auth.timestamp.isoformat(),
            "authenticationId": auth.id,
            "authenticationCount": auth_count
        }, status=200)
    else:
        return Response({
            "isAuthenticated": False,
            "authenticationCount": WhiteflagAuthentication.objects.filter(
                user=request.user
            ).count()
        }, status=200)


@api_view(["POST"])
def whiteflag_discontinue_authentication(request):
    payload = json.dumps(
        {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "4",
            "referencedMessage": request.data["referencedMessage"],
            "verificationMethod": request.data["verificationMethod"],
            "verificationData": request.data["verificationData"],
        }
    )
    result = whiteflag_encoder_helper(payload)
    if result[1]:
        return Response(result[0], 200)
    return Response(result[0], 400)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def whiteflag_encode(request):
    """
    Encodes and submits a Whiteflag message.
    
    Per Whiteflag spec 5.1.1: "Any message sent by an account before that 
    account has sent an A(0) message, may be considered unauthenticated 
    by recipients."
    
    This endpoint enforces A(0) authentication before allowing other message types.
    """
    message_code = request.data.get("messageCode")
    
    # Allow authentication messages (A) to pass through without checking
    # Other messages require A(0) to have been sent first
    if message_code and message_code != "A":
        if not check_authentication_status(request.user):
            return Response(
                {
                    "error": "Authentication required",
                    "message": "Per Whiteflag spec 5.1.1, you must send an A(0) initial authentication message before sending other message types.",
                    "fix": "Call POST /api/v1/whiteflag/authenticate/ with verificationMethod and verificationData, or include auth_url/auth_token when creating your account.",
                    "authenticated": False
                },
                status=403
            )
    
    result, success = whiteflag_encoder_helper(request.data)
    if success:
        return Response(result, 200)
    return Response(result, 400)


# @silk_profile(name="whiteflag_generate_shared_secret_key")  # DISABLED: Silk removed
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def whiteflag_generate_shared_secret_key(request, group_id=None):
    if group_id is None:
        return Response({"error": "group_id is required"})
    our_group = request.user.api_group_users.first()
    their_group = APIGroup.objects.get(id=group_id)
    shared_secret, success = generate_shared_secret(our_group, their_group)
    if success:
        return Response({"success": True, "shared_secret": shared_secret})
    return Response({"success": False, "error": shared_secret["error"]})


# @silk_profile(name="whiteflag_decode")  # DISABLED: Silk removed
@api_view(["POST"])
def whiteflag_decode(request):
    form = WhiteflagDecodeForm(request.POST)
    if not form.is_valid():
        return Response({"error": form.errors.items()})
    payload = json.dumps(form.cleaned_data["message"])
    sender_group = (
        APIGroup.objects.get(name=form.cleaned_data["sender_group"])
        if form.cleaned_data["sender_group"]
        else None
    )
    recipient_group = request.user.api_group_users.first()
    return Response(decode(payload, sender_group, recipient_group))


@api_view(["POST"])
def whiteflag_announce_public_key(request):
    payload = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "K",
        "referenceIndicator": "0",
        "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
        "cryptoDataType": "1",
        "cryptoData": request.data["public_key"],
    }
    result = whiteflag_encoder_helper(payload)
    if result[1]:
        return Response(result[0], 200)
    return Response(result[0], 400)


@api_view(["GET"])
def whiteflag_generate_shared_token(request):
    """
    Generate a random shared secret token (UUID).
    
    This token should be securely shared with the counterparty through
    an external channel (email, secure messaging, etc.) before authentication.
    """
    response = {
        "sharedToken": str(uuid.uuid4()),
    }
    return Response(response)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def authenticate_oneclick(request):
    """
    ONE-CLICK AUTHENTICATION - Whiteflag Method 2A (Pre-Shared Token)
    
    Complete authentication flow in a single button press:
    1. Generate pre-shared secret (UUID)
    2. Derive 32-byte token with HKDF-SHA256 (secret + address + salt)
    3. Post A2(0) authentication message with derived token
    4. Generate ECDH keypair (if not exists)
    5. Post K(0)0A message with ECDH public key
    
    Per Whiteflag spec section 5.2.3:
    - Token length: 32 bytes (256 bits)
    - Salt: 0x420abc48f5d69328c457d61725d3fd7af2883cad8460976167e375b9f2c14081
    - Info: Binary blockchain address
    
    Returns:
        - shared_secret: UUID token (SAVE THIS SECURELY!)
        - ecdh_public_key: Your ECDH public key (64 hex chars)
        - a_transaction_hash: A2(0) message transaction hash
        - k_transaction_hash: K(0)0A message transaction hash
        - authentication_id: Database record ID
    """
    from main.models import UserKeys, WhiteflagAuthentication, Signal
    
    try:
        # Step 1: Generate pre-shared secret (UUID)
        shared_secret = str(uuid.uuid4())
        
        # Get user's keys and address
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.address:
            return Response({
                "error": "No blockchain address found",
                "message": "Create blockchain account first",
                "fix": "Call POST /api/v1/fennel/create_account/"
            }, status=404)
        
        blockchain_address = user_keys.address
        
        # Step 2: Derive 32-byte token with HKDF-SHA256
        from substrateinterface import Keypair
        binary_address = Keypair(ss58_address=blockchain_address).public_key
        context_hex = binary_address.hex()
        
        payload = {
            "secret": shared_secret,
            "context": context_hex
        }
        
        derive_response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_token",
            json=payload,
            timeout=10
        )
        
        if derive_response.status_code != 200:
            return Response({
                "error": "Failed to derive authentication token",
                "details": derive_response.text
            }, status=500)
        
        derive_result = derive_response.json()
        
        if not derive_result.get("success"):
            return Response({
                "error": "Token derivation failed",
                "details": derive_result.get("error")
            }, status=500)
        
        auth_token = derive_result["derived_token"]
        
        # Step 3: Post A2(0) authentication message
        a_message_payload = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",
            "referencedMessage": "0" * 64,
            "verificationMethod": "2",
            "verificationData": auth_token  # Full 32-byte token (64 hex chars)
        }
        
        encoded_a_message, encode_success = whiteflag_encoder_helper(a_message_payload)
        
        if not encode_success:
            return Response({
                "error": "Failed to encode A2(0) message",
                "details": encoded_a_message
            }, status=400)
        
        subservice_payload = {
            "mnemonic": user_keys.mnemonic,
            "content": encoded_a_message,
        }
        
        blockchain_response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
            data=subservice_payload,
            timeout=30,
        )
        
        if blockchain_response.status_code != 200:
            return Response({
                "error": "Failed to submit A2(0) to blockchain",
                "details": blockchain_response.text,
                "shared_secret": shared_secret,
                "note": "Token derived successfully but blockchain submission failed"
            }, status=500)
        
        a_response_data = blockchain_response.json()
        a_tx_hash = a_response_data.get("txHash", "")
        if a_tx_hash.startswith("0x"):
            a_tx_hash = a_tx_hash[2:]
        a_block_number = a_response_data.get("blockNumber")
        
        # Step 4: Generate ECDH keypair (if not exists)
        ecdh_public_key = user_keys.public_diffie_hellman_key
        ecdh_generated = False
        
        if not ecdh_public_key:
            ecdh_response = requests.post(
                f"{os.environ.get('FENNEL_CLI_IP')}/v1/generate_ecdh_keypair",
                timeout=10
            )
            
            if ecdh_response.status_code == 200:
                ecdh_result = ecdh_response.json()
                if ecdh_result.get("success"):
                    user_keys.private_diffie_hellman_key = ecdh_result["private_key"]
                    user_keys.public_diffie_hellman_key = ecdh_result["public_key"]
                    user_keys.save()
                    ecdh_public_key = ecdh_result["public_key"]
                    ecdh_generated = True
        
        # Step 5: Post K(0)0A message with ECDH public key
        k_tx_hash = None
        k_block_number = None
        k_warning = None
        
        if ecdh_public_key:
            k_message_payload = {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "K",
                "referenceIndicator": "0",
                "referencedMessage": "0" * 64,
                "cryptoDataType": "0A",
                "cryptoData": ecdh_public_key,
            }
            
            encoded_k_message, k_encode_success = whiteflag_encoder_helper(k_message_payload)
            
            if k_encode_success:
                k_blockchain_response = requests.post(
                    f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
                    data={"mnemonic": user_keys.mnemonic, "content": encoded_k_message},
                    timeout=30,
                )
                
                if k_blockchain_response.status_code == 200:
                    k_response_data = k_blockchain_response.json()
                    k_tx_hash = k_response_data.get("txHash", "")
                    if k_tx_hash.startswith("0x"):
                        k_tx_hash = k_tx_hash[2:]
                    k_block_number = k_response_data.get("blockNumber")
                else:
                    k_warning = "A2(0) sent successfully but K(0)0A submission failed"
            else:
                k_warning = f"A2(0) sent but K(0)0A encoding failed: {encoded_k_message}"
        else:
            k_warning = "ECDH keypair generation failed"
        
        # Store authentication record
        auth_record = WhiteflagAuthentication.objects.create(
            user=request.user,
            verification_method="2",
            verification_data=auth_token,
            ecdh_public_key=ecdh_public_key,
            transaction_hash=a_tx_hash,
            is_active=True
        )
        
        # Store Signal records
        Signal.objects.create(
            signal_text=encoded_a_message,
            sender=request.user,
            tx_hash=a_tx_hash,
            block_number=a_block_number,
            message_code="A",
            synced=True,
            finalized=True
        )
        
        if k_tx_hash:
            Signal.objects.create(
                signal_text=encoded_k_message,
                sender=request.user,
                tx_hash=k_tx_hash,
                block_number=k_block_number,
                message_code="K",
                synced=True,
                finalized=True
            )
        
        response_data = {
            "success": True,
            "authentication_id": auth_record.id,
            "shared_secret": shared_secret,
            "ecdh_public_key": ecdh_public_key,
            "ecdh_generated": ecdh_generated,
            "a_transaction_hash": a_tx_hash,
            "k_transaction_hash": k_tx_hash,
            "blockchain_address": blockchain_address,
            "message": "✅ Authentication complete! A2(0) and K(0)0A messages posted to blockchain.",
            "warning": "⚠️ SAVE YOUR SHARED SECRET SECURELY! You'll need it to verify messages."
        }
        
        if k_warning:
            response_data["k_warning"] = k_warning
        
        return Response(response_data, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user",
            "message": "Create blockchain account first",
            "fix": "Call POST /api/v1/fennel/create_account/"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during one-click authentication",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def authenticate_with_shared_token(request):
    """
    Authenticate using Method 2A: Pre-Shared Token.
    
    Complete authentication flow:
    1. Derives authentication token from shared secret using HKDF
    2. Sends A2(0) authentication message to blockchain
    3. Automatically sends K(0)0A message (if user has ECDH key)
    4. Stores authentication record
    
    Request:
        - sharedToken: Pre-shared secret (UUID)
        - address: (Optional) Uses user's address if not provided
    
    Returns:
        - success: Boolean
        - authentication_id: WhiteflagAuthentication record ID
        - a_transaction_hash: Blockchain TX hash of A2(0) message
        - k_transaction_hash: Blockchain TX hash of K(0)0A message (if sent)
        - derived_token: Authentication token used (for reference)
        - shared_secret: The shared token (for user to save securely)
    """
    from main.models import UserKeys, WhiteflagAuthentication, Signal
    
    shared_token = request.data.get("sharedToken", "").strip()
    address_override = request.data.get("address", "").strip()
    
    if not shared_token:
        return Response({
            "error": "Missing required parameter: sharedToken"
        }, status=400)
    
    try:
        # Get user's keys and address
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.address:
            return Response({
                "error": "No blockchain address found",
                "message": "Create blockchain account first"
            }, status=404)
        
        # Use provided address or default to user's address
        blockchain_address = address_override or user_keys.address
        
        # Step 1: Derive authentication token using HKDF via fennel-cli
        from substrateinterface import Keypair
        binary_address = Keypair(ss58_address=blockchain_address).public_key
        context_hex = binary_address.hex()
        
        payload = {
            "secret": shared_token,
            "context": context_hex
        }
        
        derive_response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_token",
            json=payload,
            timeout=10
        )
        
        if derive_response.status_code != 200:
            return Response({
                "error": "Failed to derive authentication token",
                "details": derive_response.text
            }, status=500)
        
        derive_result = derive_response.json()
        
        if not derive_result.get("success"):
            return Response({
                "error": "Token derivation failed",
                "details": derive_result.get("error")
            }, status=500)
        
        auth_token = derive_result["derived_token"]
        
        # Step 2: Send A2(0) authentication message
        # Per Whiteflag spec section 5.2.3: derived token must be 32 bytes (256 bits)
        # Per Whiteflag spec section 4.3.4.3: VerificationData field must contain the verification token
        # The full 32-byte token is sent (64 hex characters)
        
        a_message_payload = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",
            "referencedMessage": "0" * 64,
            "verificationMethod": "2",  # Method 2: Shared Token
            "verificationData": auth_token  # Full 32-byte token (64 hex chars)
        }
        
        encoded_a_message, encode_success = whiteflag_encoder_helper(a_message_payload)
        
        if not encode_success:
            return Response({
                "error": "Failed to encode A2(0) message",
                "details": encoded_a_message
            }, status=400)
        
        # Submit A message to blockchain
        subservice_payload = {
            "mnemonic": user_keys.mnemonic,
            "content": encoded_a_message,
        }
        
        blockchain_response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
            data=subservice_payload,
            timeout=30,
        )
        
        if blockchain_response.status_code != 200:
            return Response({
                "error": "Failed to submit A2(0) to blockchain",
                "details": blockchain_response.text,
                "encoded_message": encoded_a_message,
                "derived_token": auth_token,
                "note": "Token derived successfully but blockchain submission failed"
            }, status=500)
        
        a_response_data = blockchain_response.json()
        a_tx_hash = a_response_data.get("txHash", "")
        if a_tx_hash.startswith("0x"):
            a_tx_hash = a_tx_hash[2:]
        a_block_number = a_response_data.get("blockNumber")
        
        # Step 3: Automatically send K(0)0A message (if user has ECDH key)
        k_tx_hash = None
        k_block_number = None
        k_warning = None
        
        if user_keys.public_diffie_hellman_key:
            k_message_payload = {
                "prefix": "WF",
                "version": "1",
                "encryptionIndicator": "0",
                "duressIndicator": "0",
                "messageCode": "K",
                "referenceIndicator": "0",
                "referencedMessage": "0" * 64,
                "cryptoDataType": "0A",  # ECDHPubKey
                "cryptoData": user_keys.public_diffie_hellman_key,
            }
            
            encoded_k_message, k_encode_success = whiteflag_encoder_helper(k_message_payload)
            
            if k_encode_success:
                k_blockchain_response = requests.post(
                    f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
                    data={"mnemonic": user_keys.mnemonic, "content": encoded_k_message},
                    timeout=30,
                )
                
                if k_blockchain_response.status_code == 200:
                    k_response_data = k_blockchain_response.json()
                    k_tx_hash = k_response_data.get("txHash", "")
                    if k_tx_hash.startswith("0x"):
                        k_tx_hash = k_tx_hash[2:]
                    k_block_number = k_response_data.get("blockNumber")
                else:
                    k_warning = "A2(0) sent successfully but K(0)0A submission failed"
            else:
                k_warning = f"A2(0) sent but K(0)0A encoding failed: {encoded_k_message}"
        else:
            k_warning = "No ECDH public key found. Generate ECDH keypair to enable encryption."
        
        # Step 4: Store authentication record
        auth_record = WhiteflagAuthentication.objects.create(
            user=request.user,
            verification_method="2",
            verification_data=auth_token,
            ecdh_public_key=user_keys.public_diffie_hellman_key,
            transaction_hash=a_tx_hash,
            is_active=True
        )
        
        # Step 5: Store messages in Signal database
        Signal.objects.create(
            signal_text=encoded_a_message,
            sender=request.user,
            tx_hash=a_tx_hash,
            block_number=a_block_number,
            message_code="A",
            synced=True,
            finalized=True
        )
        
        if k_tx_hash:
            Signal.objects.create(
                signal_text=encoded_k_message,
                sender=request.user,
                tx_hash=k_tx_hash,
                block_number=k_block_number,
                message_code="K",
                synced=True,
                finalized=True
            )
        
        response_data = {
            "success": True,
            "authentication_id": auth_record.id,
            "verification_method": "2 (Pre-Shared Token)",
            "a_transaction_hash": a_tx_hash,
            "k_transaction_hash": k_tx_hash,
            "derived_token": auth_token,
            "shared_secret": shared_token,  # Return for user to save
            "blockchain_address": blockchain_address,
            "message": "Authentication successful! A2(0) message sent to blockchain.",
            "note": "IMPORTANT: Save your shared secret in a secure location. You will need it to verify messages."
        }
        
        if k_warning:
            response_data["warning"] = k_warning
        
        return Response(response_data, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user",
            "message": "Create blockchain account first"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during authentication",
            "details": str(e)
        }, status=500)


@api_view(["GET"])
def user_auth_status(request):
    """
    Enhanced authentication status endpoint with balance and blockchain info.
    
    Returns:
        - balance: User's token balance
        - has_sent_a0: Boolean indicating if user has any A(0) message
        - authentication_count: Total number of A(0) messages
        - blockchain_address: User's blockchain address
        - ecdh_public_key: Most recent ECDH public key (if any)
    """
    from main.models import WhiteflagAuthentication, UserKeys
    from main.fennel_views import check_balance
    
    try:
        # Get user's blockchain keys and balance
        user_keys = UserKeys.objects.get(user=request.user)
        balance_info = check_balance(user_keys)
        balance = balance_info.get("balance", 0)
        blockchain_address = user_keys.address or ""
    except UserKeys.DoesNotExist:
        balance = 0
        blockchain_address = ""
    
    # Get authentication info
    authentications = WhiteflagAuthentication.objects.filter(user=request.user)
    auth_count = authentications.count()
    has_sent_a0 = auth_count > 0
    
    # Get most recent ECDH public key
    recent_auth = authentications.filter(
        ecdh_public_key__isnull=False
    ).order_by('-timestamp').first()
    
    ecdh_public_key = recent_auth.ecdh_public_key if recent_auth else None
    
    return Response({
        "balance": balance,
        "has_sent_a0": has_sent_a0,
        "authentication_count": auth_count,
        "blockchain_address": blockchain_address,
        "ecdh_public_key": ecdh_public_key
    }, status=200)


@api_view(["POST"])
def publish_ecdh_key(request):
    """
    Publish ECDH public key via K(0)0A message.
    
    Per Whiteflag spec 5.2.2: Public keys are announced via crypto messages
    with crypto data type 0A (ECDHPubKey).
    
    Request body:
        - public_key: Curve25519 public key (64 hex characters = 32 bytes)
    
    Returns:
        - success: Boolean
        - transaction_hash: Blockchain transaction hash
        - message_code: "K"
        - reference_code: "0"
        - crypto_data_type: "0A"
    """
    from main.models import WhiteflagAuthentication
    
    public_key = request.data.get("public_key", "").strip()
    
    # Validate public key format (64 hex chars for Curve25519)
    if not public_key:
        return Response({
            "error": "Missing public_key parameter"
        }, status=400)
    
    if len(public_key) != 64:
        return Response({
            "error": f"Invalid public key length: expected 64 hex chars, got {len(public_key)}",
            "hint": "Curve25519 public keys are 32 bytes (64 hex characters)"
        }, status=400)
    
    try:
        # Validate it's valid hex
        int(public_key, 16)
    except ValueError:
        return Response({
            "error": "Invalid public key format: must be hexadecimal"
        }, status=400)
    
    # Create K(0)0A message
    # Message code K = Cryptographic message
    # Reference code 0 = No reference (initial key announcement)
    # Crypto data type 0A = ECDHPubKey (per spec table 16)
    payload = {
        "prefix": "WF",
        "version": "1",
        "encryptionIndicator": "0",
        "duressIndicator": "0",
        "messageCode": "K",
        "referenceIndicator": "0",
        "referencedMessage": "0" * 64,
        "cryptoDataType": "0A",  # ECDHPubKey
        "cryptoData": public_key,
    }
    
    # Encode the K(0)0A message
    encoded_message, success = whiteflag_encoder_helper(payload)
    
    if not success:
        return Response({
            "error": "Failed to encode ECDH key message",
            "details": encoded_message
        }, status=400)
    
    # Submit to blockchain via subservice (following the flow: API → Subservice → Node)
    from main.models import UserKeys
    import os
    import requests
    
    try:
        user_keys = UserKeys.objects.get(user=request.user)
        
        subservice_payload = {
            "mnemonic": user_keys.mnemonic,
            "content": encoded_message,
        }
        
        blockchain_response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
            data=subservice_payload,
            timeout=30,
        )
        
        if blockchain_response.status_code != 200:
            return Response({
                "error": "Failed to submit K(0)0A message to blockchain",
                "details": blockchain_response.text,
                "encoded_message": encoded_message,
                "note": "Message encoded but not submitted. Store this for manual submission."
            }, status=500)
        
        response_data = blockchain_response.json()
        tx_hash = response_data.get("txHash", "")
        if tx_hash and tx_hash.startswith("0x"):
            tx_hash = tx_hash[2:]
        
        block_number = response_data.get("blockNumber")
        block_hash = response_data.get("blockHash")
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user"
        }, status=404)
    except requests.exceptions.Timeout:
        return Response({
            "error": "Blockchain submission timed out",
            "encoded_message": encoded_message,
            "note": "Message encoded but submission timed out. Try again or submit manually."
        }, status=500)
    except Exception as e:
        return Response({
            "error": "Exception during blockchain submission",
            "details": str(e),
            "encoded_message": encoded_message
        }, status=500)
    
    # Store public key with most recent authentication record
    # or create a note that this key was published
    recent_auth = WhiteflagAuthentication.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-timestamp').first()
    
    if recent_auth and not recent_auth.ecdh_public_key:
        recent_auth.ecdh_public_key = public_key
        recent_auth.save()
    
    # FIX: Store K(0)0A message in Signal database for indexing/querying
    # Previously this message was only submitted to blockchain but not stored locally
    from main.models import Signal
    signal = Signal.objects.create(
        signal_text=encoded_message,
        sender=request.user,
        tx_hash=tx_hash,
        block_number=block_number,
        block_hash=block_hash,
        message_code="K",
        synced=True,
        finalized=True,  # Assuming message was successfully included in block
    )
    
    return Response({
        "success": True,
        "signal_id": signal.id,
        "encoded_message": encoded_message,
        "transaction_hash": tx_hash,
        "block_number": block_number,
        "block_hash": block_hash,
        "message_code": "K",
        "reference_code": "0",
        "crypto_data_type": "0A",
        "public_key": public_key,
        "message": "✅ K(0)0A message published successfully to blockchain"
    }, status=200)


# ============================================================================
# TOKEN REQUEST SYSTEM
# Allows users to request tokens from admins (is_staff=True/is_superuser=True)
# ============================================================================

# @silk_profile(name="request_tokens")  # DISABLED: Silk removed
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def request_tokens(request):
    """
    User submits a request for tokens to authenticate.
    Creates a TokenRequest that admins can view and fulfill.
    
    POST data:
    - requested_amount (optional, default=10.0)
    - reason (optional)
    
    Returns:
    - request_id: ID of created token request
    - status: 'pending'
    - message: Confirmation message
    """
    from main.models import TokenRequest, UserKeys
    from decimal import Decimal
    
    # Get user's blockchain address
    try:
        user_keys = UserKeys.objects.get(user=request.user)
        blockchain_address = user_keys.address
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No blockchain account found",
            "fix": "Please create a blockchain account first"
        }, status=400)
    
    # Check if user already has a pending request
    existing_pending = TokenRequest.objects.filter(
        user=request.user,
        status='pending'
    ).first()
    
    if existing_pending:
        return Response({
            "error": "You already have a pending token request",
            "request_id": existing_pending.id,
            "requested_at": existing_pending.requested_at.isoformat(),
            "message": "Please wait for an admin to fulfill your existing request"
        }, status=400)
    
    # Get optional parameters
    requested_amount = request.data.get('requested_amount', 10.0)
    reason = request.data.get('reason', '')
    
    try:
        requested_amount = Decimal(str(requested_amount))
        if requested_amount <= 0:
            return Response({
                "error": "Invalid requested_amount",
                "message": "Amount must be greater than 0"
            }, status=400)
    except (ValueError, TypeError):
        return Response({
            "error": "Invalid requested_amount",
            "message": "Must be a valid number"
        }, status=400)
    
    # Create token request
    token_request = TokenRequest.objects.create(
        user=request.user,
        blockchain_address=blockchain_address,
        requested_amount=requested_amount,
        reason=reason,
        status='pending'
    )
    
    return Response({
        "success": True,
        "request_id": token_request.id,
        "requested_amount": str(token_request.requested_amount),
        "blockchain_address": blockchain_address,
        "status": "pending",
        "message": "Token request submitted successfully. An admin will review your request shortly."
    }, status=201)


# @silk_profile(name="list_token_requests_admin")  # DISABLED: Silk removed
@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def list_token_requests_admin(request):
    """
    List all token requests (admin only: is_staff or is_superuser).
    
    Query params:
    - status: Filter by status (pending/fulfilled/rejected), default=all
    - limit: Max results, default=50
    
    Returns list of token requests with user info.
    """
    from main.models import TokenRequest
    
    # Check admin permissions
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            "error": "Permission denied",
            "message": "Only administrators can view token requests"
        }, status=403)
    
    # Get query parameters
    status_filter = request.query_params.get('status', None)
    limit = int(request.query_params.get('limit', 50))
    
    # Build query
    queryset = TokenRequest.objects.select_related('user', 'fulfilled_by')
    
    if status_filter and status_filter in ['pending', 'fulfilled', 'rejected']:
        queryset = queryset.filter(status=status_filter)
    
    requests_list = queryset[:limit]
    
    # Format response
    data = []
    for tr in requests_list:
        data.append({
            "id": tr.id,
            "user": {
                "id": tr.user.id,
                "username": tr.user.username,
                "email": tr.user.email,
            },
            "blockchain_address": tr.blockchain_address,
            "requested_amount": str(tr.requested_amount),
            "reason": tr.reason,
            "status": tr.status,
            "requested_at": tr.requested_at.isoformat(),
            "fulfilled_at": tr.fulfilled_at.isoformat() if tr.fulfilled_at else None,
            "fulfilled_by": {
                "id": tr.fulfilled_by.id,
                "username": tr.fulfilled_by.username
            } if tr.fulfilled_by else None,
            "transaction_hash": tr.transaction_hash,
            "admin_notes": tr.admin_notes
        })
    
    return Response({
        "count": len(data),
        "requests": data
    }, status=200)


# @silk_profile(name="fulfill_token_request")  # DISABLED: Silk removed
@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def fulfill_token_request(request):
    """
    Admin fulfills a token request by sending tokens and marking request as fulfilled.
    
    POST data:
    - request_id: ID of TokenRequest to fulfill
    - action: 'fulfill' or 'reject'
    - admin_notes: Optional notes about the action
    
    If action='fulfill', also sends tokens to user's address.
    
    Returns success confirmation.
    """
    from main.models import TokenRequest
    from django.utils import timezone
    import requests
    import os
    
    # Check admin permissions
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({
            "error": "Permission denied",
            "message": "Only administrators can fulfill token requests"
        }, status=403)
    
    # Get parameters
    request_id = request.data.get('request_id')
    action = request.data.get('action')  # 'fulfill' or 'reject'
    admin_notes = request.data.get('admin_notes', '')
    
    if not request_id:
        return Response({"error": "request_id is required"}, status=400)
    
    if action not in ['fulfill', 'reject']:
        return Response({"error": "action must be 'fulfill' or 'reject'"}, status=400)
    
    # Get token request
    try:
        token_request = TokenRequest.objects.select_related('user').get(id=request_id)
    except TokenRequest.DoesNotExist:
        return Response({"error": "Token request not found"}, status=404)
    
    # Check if already processed
    if token_request.status != 'pending':
        return Response({
            "error": "Token request already processed",
            "status": token_request.status,
            "fulfilled_at": token_request.fulfilled_at.isoformat() if token_request.fulfilled_at else None
        }, status=400)
    
    # Process action
    if action == 'reject':
        token_request.status = 'rejected'
        token_request.fulfilled_by = request.user
        token_request.fulfilled_at = timezone.now()
        token_request.admin_notes = admin_notes
        token_request.save()
        
        return Response({
            "success": True,
            "action": "rejected",
            "request_id": token_request.id,
            "user": token_request.user.username,
            "message": "Token request rejected"
        }, status=200)
    
    # action == 'fulfill': Send tokens via fennel-cli
    try:
        fennel_response = requests.post(
            f"{os.environ.get('FENNEL_SUBSERVICE_IP', 'http://localhost:9031')}/v1/transfer_token",
            json={
                "dest": token_request.blockchain_address,
                "amount": float(token_request.requested_amount)
            },
            timeout=30
        )
        
        if fennel_response.status_code == 200:
            result = fennel_response.json()
            tx_hash = result.get("tx_hash")
            
            # Mark request as fulfilled
            token_request.status = 'fulfilled'
            token_request.fulfilled_by = request.user
            token_request.fulfilled_at = timezone.now()
            token_request.transaction_hash = tx_hash
            token_request.admin_notes = admin_notes
            token_request.save()
            
            return Response({
                "success": True,
                "action": "fulfilled",
                "request_id": token_request.id,
                "user": token_request.user.username,
                "amount_sent": str(token_request.requested_amount),
                "transaction_hash": tx_hash,
                "message": f"Sent {token_request.requested_amount} tokens to {token_request.user.username}"
            }, status=200)
        else:
            return Response({
                "error": "Failed to send tokens",
                "details": fennel_response.text,
                "message": "Token transfer failed. Request remains pending."
            }, status=500)
            
    except Exception as e:
        return Response({
            "error": "Exception sending tokens",
            "details": str(e),
            "message": "Token transfer failed. Request remains pending."
        }, status=500)


# ============================================================================
# ECDH AUTHENTICATION ENDPOINTS
# ECDH-based Method 2 authentication per Whiteflag spec 5.2.2 & 5.2.3
# ============================================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_ecdh_keypair(request):
    """
    Generate X25519 ECDH keypair for Whiteflag Method 2 authentication.
    
    Per Whiteflag spec 5.2.2: Generates a keypair that can be used for
    ECDH key agreement to derive shared secrets.
    
    Returns:
        - success: Boolean
        - private_key: 64 hex chars (32 bytes) - KEEP PRIVATE
        - public_key: 64 hex chars (32 bytes) - Publish via K(0)0A
    """
    from main.models import UserKeys
    
    try:
        # Call fennel-cli to generate ECDH keypair
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/generate_ecdh_keypair",
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to generate ECDH keypair",
                "details": response.text
            }, status=500)
        
        result = response.json()
        
        if not result.get("success"):
            return Response({
                "error": "ECDH keypair generation failed",
                "details": result.get("error")
            }, status=500)
        
        # Store keys in UserKeys model
        user_keys, created = UserKeys.objects.get_or_create(user=request.user)
        user_keys.private_diffie_hellman_key = result["private_key"]
        user_keys.public_diffie_hellman_key = result["public_key"]
        user_keys.save()
        
        return Response({
            "success": True,
            "private_key": result["private_key"],
            "public_key": result["public_key"],
            "stored": True,
            "message": "ECDH keypair generated and stored. Publish your public key via K(0)0A message."
        }, status=200)
        
    except Exception as e:
        return Response({
            "error": "Exception generating ECDH keypair",
            "details": str(e)
        }, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_my_ecdh_public_key(request):
    """
    Retrieve user's ECDH public key.
    
    Returns the X25519 public key that can be published via K(0)0A message.
    """
    from main.models import UserKeys
    
    try:
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.public_diffie_hellman_key:
            return Response({
                "error": "No ECDH keypair generated yet",
                "message": "Call /generate_ecdh_keypair first"
            }, status=404)
        
        return Response({
            "success": True,
            "public_key": user_keys.public_diffie_hellman_key,
            "message": "Publish this key via K(0)0A message to enable ECDH authentication"
        }, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user",
            "message": "Call /generate_ecdh_keypair first"
        }, status=404)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def derive_auth_from_ecdh(request):
    """
    Derive Whiteflag Method 2 authentication token from ECDH shared secret.
    
    Per Whiteflag spec 5.2.3: Uses ECDH to negotiate shared secret, then
    derives authentication token using HKDF-SHA256.
    
    Request body:
        - their_public_key: Recipient's X25519 public key (64 hex chars)
        - context: Blockchain address as hex (optional, defaults to user ID)
    
    Returns:
        - success: Boolean
        - shared_secret: ECDH negotiated secret (for reference)
        - derived_token: HKDF-derived authentication token (post to blockchain)
    """
    from main.models import UserKeys
    
    their_public_key = request.data.get("their_public_key", "").strip()
    context = request.data.get("context", "").strip()
    
    # Validate their public key
    if not their_public_key:
        return Response({
            "error": "Missing their_public_key parameter",
            "hint": "Provide recipient's X25519 public key (64 hex chars)"
        }, status=400)
    
    if len(their_public_key) != 64:
        return Response({
            "error": f"Invalid public key length: {len(their_public_key)}",
            "expected": "64 hex characters (32 bytes)"
        }, status=400)
    
    try:
        # Get user's private ECDH key
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "No ECDH private key found",
                "message": "Generate ECDH keypair first via /generate_ecdh_keypair"
            }, status=404)
        
        # Use user ID as context if not provided (formatted as 64-char hex)
        if not context:
            context = format(request.user.id, '064x')
        
        # Call fennel-cli to derive auth token from ECDH
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": their_public_key,
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to derive auth token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        
        if not result.get("success"):
            return Response({
                "error": "Auth token derivation failed",
                "details": result.get("error")
            }, status=500)
        
        return Response({
            "success": True,
            "shared_secret": result["shared_secret"],
            "derived_token": result["derived_token"],
            "message": "Authentication token derived from ECDH. Use this token in A(2) message.",
            "note": "The derived_token (not shared_secret) is posted publicly on blockchain"
        }, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user",
            "message": "Generate ECDH keypair first via /generate_ecdh_keypair"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception deriving auth token",
            "details": str(e)
        }, status=500)


# ============================================================================
# SELF-ECDH AUTHENTICATION WITH UNIVERSAL VERIFICATION
# Universal authentication that anyone can verify
# ============================================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def self_authenticate(request):
    """
    Self-authenticate using ECDH Method 2.
    Creates universal authentication that ANYONE with ECDH keys can verify.
    
    This is the elegant solution:
    - Authentication: Self-ECDH (one-time, universal)
    - Encryption: P2P ECDH (on-demand, private)
    
    Returns:
        - success: Boolean
        - authentication_id: ID of WhiteflagAuthentication record
        - transaction_hash: Blockchain TX hash
        - verifiable_by: "anyone" - universal verification
    """
    from main.models import UserKeys, WhiteflagAuthentication
    
    try:
        user_keys = UserKeys.objects.get(user=request.user)
        
        # Ensure user has ECDH keypair
        if not user_keys.private_diffie_hellman_key or not user_keys.public_diffie_hellman_key:
            return Response({
                "error": "No ECDH keypair found",
                "message": "Generate ECDH keypair first via /generate_ecdh_keypair"
            }, status=400)
        
        # Derive self-ECDH token
        # Using own public key as counterpart creates universal verifiability
        # Context must be hex-encoded string (matching old derive_auth_token pattern)
        if user_keys.address:
            # Convert address string to hex (same as old Method 2 auth)
            context = user_keys.address.encode('utf-8').hex()
        else:
            # Fallback to user ID as 32-byte hex
            context = format(request.user.id, '064x')
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": user_keys.public_diffie_hellman_key,  # Self!
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to derive self-authentication token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        
        if not result.get("success"):
            return Response({
                "error": "Self-authentication token derivation failed",
                "details": result.get("error")
            }, status=500)
        
        auth_token = result["derived_token"]
        
        # Submit A(0) authentication message using proper Whiteflag encoding
        from main.whiteflag_helpers import whiteflag_encoder_helper
        
        # Build A(0) message payload per Whiteflag spec
        payload = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",  # Initial authentication
            "referencedMessage": "0" * 64,  # No reference for A(0)
            "verificationMethod": "2",  # Method 2: Shared token (ECDH-derived)
            "verificationData": auth_token,
        }
        
        # Encode the A(0) authentication message
        encoded_message, success = whiteflag_encoder_helper(payload)
        
        if not success:
            return Response({
                "error": "Failed to encode authentication message",
                "details": encoded_message
            }, status=500)
        
        # Submit to blockchain via subservice (following the flow: API → Subservice → Node)
        try:
            subservice_payload = {
                "mnemonic": user_keys.mnemonic,
                "content": encoded_message,
            }
            
            blockchain_response = requests.post(
                f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
                data=subservice_payload,
                timeout=30,
            )
            
            if blockchain_response.status_code != 200:
                return Response({
                    "error": "Failed to submit authentication to blockchain",
                    "details": blockchain_response.text,
                    "encoded_message": encoded_message,
                    "note": "Message encoded but not submitted. Store this for manual submission."
                }, status=500)
            
            response_data = blockchain_response.json()
            tx_hash = response_data.get("txHash", "")
            if tx_hash.startswith("0x"):
                tx_hash = tx_hash[2:]
            
        except requests.exceptions.Timeout:
            return Response({
                "error": "Blockchain submission timed out",
                "encoded_message": encoded_message,
                "note": "Message encoded but submission timed out. Try again or submit manually."
            }, status=500)
        except Exception as e:
            return Response({
                "error": "Exception during blockchain submission",
                "details": str(e),
                "encoded_message": encoded_message
            }, status=500)
        
        # Store authentication record with blockchain data
        auth_record = WhiteflagAuthentication.objects.create(
            user=request.user,
            verification_method="2",
            verification_data=auth_token,
            ecdh_public_key=user_keys.public_diffie_hellman_key,
            ecdh_counterpart="self",  # Special marker for self-authentication
            ecdh_counterpart_key=user_keys.public_diffie_hellman_key,
            transaction_hash=tx_hash,
            is_active=True
        )
        
        # FIX: Store A(0) message in Signal database for indexing/querying
        # Previously this message was only submitted to blockchain but not stored locally
        from main.models import Signal
        signal = Signal.objects.create(
            signal_text=encoded_message,
            sender=request.user,
            tx_hash=tx_hash,
            block_number=response_data.get("blockNumber"),
            block_hash=response_data.get("blockHash"),
            message_code="A",
            synced=True,
            finalized=True,  # Assuming message was successfully included in block
        )
        
        return Response({
            "success": True,
            "authentication_id": auth_record.id,
            "signal_id": signal.id,
            "authentication_type": "self_ecdh_universal",
            "transaction_hash": tx_hash,
            "encoded_message": encoded_message,
            "block_number": response_data.get("blockNumber"),
            "block_hash": response_data.get("blockHash"),
            "verifiable_by": "anyone_with_ecdh_keys",
            "message": "✅ Self-authenticated! A(0) message submitted to blockchain.",
            "note": "Your authentication is now verifiable by anyone with ECDH keys."
        }, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during self-authentication",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_user_universal(request):
    """
    Universally verify ANY user's self-authentication.
    
    This works because self-authentication uses the user's own public key,
    allowing anyone to verify by computing the same ECDH shared secret.
    
    Body:
    {
        "target_username": "user_to_verify"
    }
    """
    from main.models import UserKeys, WhiteflagAuthentication
    from django.contrib.auth.models import User
    
    target_username = request.data.get("target_username")
    
    if not target_username:
        return Response({
            "error": "Missing target_username"
        }, status=400)
    
    try:
        # Get target user's authentication
        target_user = User.objects.get(username=target_username)
        target_auth = WhiteflagAuthentication.objects.filter(
            user=target_user,
            verification_method="2",
            ecdh_counterpart="self",  # Only self-authenticated users
            is_active=True
        ).first()
        
        if not target_auth:
            return Response({
                "error": "Target user has no self-authentication",
                "hint": "They may have used counterpart-based authentication"
            }, status=404)
        
        target_keys = UserKeys.objects.get(user=target_user)
        
        if not target_keys.public_diffie_hellman_key:
            return Response({
                "error": "Target user has no published ECDH key"
            }, status=404)
        
        # Get your ECDH private key
        user_keys = UserKeys.objects.get(user=request.user)
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "You need an ECDH keypair to verify others"
            }, status=400)
        
        # Compute shared secret using target's public key twice
        # (replicating their self-authentication)
        context = target_keys.address or format(target_user.id, '064x')
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": target_keys.public_diffie_hellman_key,
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to compute verification token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        computed_token = result["derived_token"]
        
        # Verify against stored token
        verification_passed = computed_token == target_auth.verification_data
        
        return Response({
            "success": True,
            "target_username": target_username,
            "verification_passed": verification_passed,
            "authentication_type": "self_ecdh_universal",
            "message": "✅ Universal verification successful!" if verification_passed else "❌ Verification failed",
            "note": "Self-authentication enables universal verification"
        }, status=200)
        
    except User.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "Missing keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during verification",
            "details": str(e)
        }, status=500)


# ============================================================================
# ON-DEMAND P2P ENCRYPTION
# Establish private encrypted channels when needed
# ============================================================================

@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def establish_private_channel(request):
    """
    Establish encrypted communication channel with another user.
    
    This is separate from authentication:
    - Authentication: Self-ECDH (universal, public)
    - Encryption: P2P ECDH (private, on-demand)
    
    Body:
    {
        "target_username": "user_to_communicate_with"
    }
    """
    from main.models import UserKeys
    from django.contrib.auth.models import User
    
    target_username = request.data.get("target_username")
    
    if not target_username:
        return Response({
            "error": "Missing target_username"
        }, status=400)
    
    try:
        # Get target user's keys
        target_user = User.objects.get(username=target_username)
        target_keys = UserKeys.objects.get(user=target_user)
        
        if not target_keys.public_diffie_hellman_key:
            return Response({
                "error": "Target user has no published ECDH key"
            }, status=404)
        
        # Get your keys
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "You need an ECDH keypair"
            }, status=400)
        
        # Compute shared secret for encryption (different from authentication!)
        # Use a different context/salt for encryption vs authentication
        encryption_context = f"encryption:{user_keys.address}:{target_keys.address}"
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": target_keys.public_diffie_hellman_key,
            "context": encryption_context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to derive encryption key",
                "details": response.text
            }, status=500)
        
        result = response.json()
        encryption_key = result["derived_token"]
        
        return Response({
            "success": True,
            "target_username": target_username,
            "encryption_key": encryption_key,
            "channel_established": True,
            "message": f"🔐 Private channel established with {target_username}",
            "note": "Use this encryption key for E() encrypted messages"
        }, status=200)
        
    except User.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "Missing keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception establishing private channel",
            "details": str(e)
        }, status=500)


# ============================================================================
# LEGACY: PEER-TO-PEER ECDH AUTHENTICATION ENDPOINTS
# Note: Self-authentication is now preferred for universal verification
# These remain for backward compatibility or specific use cases
# ============================================================================

@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def discover_users_with_ecdh(request):
    """
    Find users who have published ECDH public keys.
    
    Returns list of users available for peer-to-peer authentication.
    """
    from main.models import UserKeys
    from django.contrib.auth.models import User
    
    try:
        users_with_ecdh = []
        
        for user in User.objects.exclude(id=request.user.id):
            try:
                user_keys = UserKeys.objects.get(user=user)
                if user_keys.public_diffie_hellman_key:
                    users_with_ecdh.append({
                        "username": user.username,
                        "public_key": user_keys.public_diffie_hellman_key,
                        "blockchain_address": user_keys.address,
                    })
            except UserKeys.DoesNotExist:
                continue
        
        return Response({
            "success": True,
            "available_counterparts": users_with_ecdh,
            "total_count": len(users_with_ecdh),
            "message": "Users with published ECDH keys available for authentication"
        }, status=200)
        
    except Exception as e:
        return Response({
            "error": "Exception discovering users",
            "details": str(e)
        }, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_user_ecdh_info(request, username):
    """
    Get specific user's ECDH information for authentication.
    """
    from main.models import UserKeys
    from django.contrib.auth.models import User
    
    try:
        user = User.objects.get(username=username)
        user_keys = UserKeys.objects.get(user=user)
        
        if not user_keys.public_diffie_hellman_key:
            return Response({
                "error": "User has no published ECDH key"
            }, status=404)
        
        return Response({
            "success": True,
            "username": user.username,
            "public_key": user_keys.public_diffie_hellman_key,
            "blockchain_address": user_keys.address,
            "available_for_authentication": True
        }, status=200)
        
    except User.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "User has no ECDH keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception retrieving user info",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def authenticate_with_user(request):
    """
    Authenticate using ECDH with another user as counterpart.
    
    Body:
    {
        "counterpart_username": "other_user",
        "counterpart_public_key": "abc123..."  # Optional: will fetch if not provided
    }
    """
    from main.models import UserKeys, WhiteflagAuthentication
    from django.contrib.auth.models import User
    
    counterpart_username = request.data.get("counterpart_username")
    
    if not counterpart_username:
        return Response({
            "error": "Missing counterpart_username"
        }, status=400)
    
    try:
        # Get counterpart user
        counterpart_user = User.objects.get(username=counterpart_username)
        counterpart_keys = UserKeys.objects.get(user=counterpart_user)
        
        # Get counterpart's public key
        counterpart_public_key = request.data.get("counterpart_public_key")
        if not counterpart_public_key:
            counterpart_public_key = counterpart_keys.public_diffie_hellman_key
        
        if not counterpart_public_key:
            return Response({
                "error": "Counterpart has no published ECDH key"
            }, status=400)
        
        # Get user's ECDH keys
        user_keys = UserKeys.objects.get(user=request.user)
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "User has no ECDH keypair",
                "message": "Generate keypair first via /generate_ecdh_keypair"
            }, status=400)
        
        # Derive token using ECDH with counterpart
        context = user_keys.address or format(request.user.id, '064x')
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": counterpart_public_key,
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to derive auth token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        
        if not result.get("success"):
            return Response({
                "error": "Auth token derivation failed",
                "details": result.get("error")
            }, status=500)
        
        auth_token = result["derived_token"]
        
        # Submit A(0) authentication message using proper Whiteflag encoding
        from main.whiteflag_helpers import whiteflag_encoder_helper
        
        # Build A(0) message payload per Whiteflag spec
        payload = {
            "prefix": "WF",
            "version": "1",
            "encryptionIndicator": "0",
            "duressIndicator": "0",
            "messageCode": "A",
            "referenceIndicator": "0",  # Initial authentication
            "referencedMessage": "0" * 64,  # No reference for A(0)
            "verificationMethod": "2",  # Method 2: Shared token (ECDH-derived)
            "verificationData": auth_token,
        }
        
        # Encode and submit to blockchain
        result_data, success = whiteflag_encoder_helper(payload)
        
        if not success:
            return Response({
                "error": "Failed to submit authentication",
                "details": result_data
            }, status=500)
        
        # Store authentication record with P2P info
        auth_record = WhiteflagAuthentication.objects.create(
            user=request.user,
            verification_method="2",
            verification_data=auth_token,
            ecdh_public_key=user_keys.public_diffie_hellman_key,
            ecdh_counterpart=counterpart_username,
            ecdh_counterpart_key=counterpart_public_key,
            transaction_hash=result_data.get("transaction_hash"),
            is_active=True
        )
        
        return Response({
            "success": True,
            "authentication_id": auth_record.id,
            "counterpart": counterpart_username,
            "transaction_hash": result_data.get("transaction_hash"),
            "encoded_message": result_data.get("encoded_message"),
            "verifiable_by": [counterpart_username],
            "message": f"Authenticated with {counterpart_username}. They can verify your token."
        }, status=200)
        
    except User.DoesNotExist:
        return Response({
            "error": "Counterpart user not found"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "User or counterpart has no keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during authentication",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_user_authentication(request):
    """
    Verify another user's authentication token using ECDH.
    
    This checks if the user authenticated with YOU as their counterpart.
    Use verify_any_user for universal verification regardless of counterpart.
    
    Body:
    {
        "target_username": "user_to_verify",
        "target_authentication_id": 123
    }
    """
    from main.models import UserKeys, WhiteflagAuthentication
    from django.contrib.auth.models import User
    
    target_username = request.data.get("target_username")
    target_auth_id = request.data.get("target_authentication_id")
    
    if not target_username or not target_auth_id:
        return Response({
            "error": "Missing target_username or target_authentication_id"
        }, status=400)
    
    try:
        # Get target authentication - must have YOU as counterpart
        target_auth = WhiteflagAuthentication.objects.get(
            id=target_auth_id,
            user__username=target_username,
            ecdh_counterpart=request.user.username,
            is_active=True
        )
        
        # Get user's private key
        user_keys = UserKeys.objects.get(user=request.user)
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "You need an ECDH keypair to verify others"
            }, status=400)
        
        # Get target user's info
        target_user = target_auth.user
        target_keys = UserKeys.objects.get(user=target_user)
        
        # Compute shared secret with target user
        context = target_keys.address or format(target_user.id, '064x')
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": target_auth.ecdh_public_key,
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to compute verification token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        computed_token = result["derived_token"]
        
        # Verify
        verification_passed = computed_token == target_auth.verification_data
        
        return Response({
            "success": True,
            "target_username": target_username,
            "verification_passed": verification_passed,
            "verification_type": "counterpart",
            "message": "Verification successful - you were their counterpart" if verification_passed else "Token mismatch"
        }, status=200)
        
    except WhiteflagAuthentication.DoesNotExist:
        return Response({
            "error": "Authentication not found or you were not their counterpart",
            "hint": "Use verify_any_user endpoint for universal verification"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "Missing keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during verification",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def verify_any_user(request):
    """
    Check if you can establish a cryptographic relationship with any user.
    
    IMPORTANT: This does NOT verify their authentication if you weren't their counterpart!
    
    What this does:
    - Computes YOUR shared secret with target user
    - Checks if you were their counterpart (only then tokens match)
    - Shows that you CAN establish ECDH with them (but that's different from verification)
    
    True verification ONLY works if you were their chosen counterpart.
    
    Body:
    {
        "target_username": "user_to_verify"
    }
    """
    from main.models import UserKeys, WhiteflagAuthentication
    from django.contrib.auth.models import User
    
    target_username = request.data.get("target_username")
    
    if not target_username:
        return Response({
            "error": "Missing target_username"
        }, status=400)
    
    try:
        # Get target user's authentication
        target_user = User.objects.get(username=target_username)
        target_auth = WhiteflagAuthentication.objects.filter(
            user=target_user,
            verification_method="2",
            is_active=True
        ).first()
        
        if not target_auth:
            return Response({
                "error": "Target user has no active Method 2 authentication"
            }, status=404)
        
        target_keys = UserKeys.objects.get(user=target_user)
        
        if not target_keys.public_diffie_hellman_key:
            return Response({
                "error": "Target user has no published ECDH key"
            }, status=404)
        
        # Get your ECDH private key
        user_keys = UserKeys.objects.get(user=request.user)
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "You need an ECDH keypair"
            }, status=400)
        
        # Compute shared secret between YOU and TARGET
        # (regardless of who the target chose as their counterpart)
        context = target_keys.address or format(target_user.id, '064x')
        
        payload = {
            "my_private_key": user_keys.private_diffie_hellman_key,
            "their_public_key": target_keys.public_diffie_hellman_key,
            "context": context
        }
        
        response = requests.post(
            f"{os.environ.get('FENNEL_CLI_IP')}/v1/derive_auth_from_ecdh",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            return Response({
                "error": "Failed to compute token",
                "details": response.text
            }, status=500)
        
        result = response.json()
        your_computed_token = result["derived_token"]
        their_stored_token = target_auth.verification_data
        
        # Check if you were their counterpart
        you_are_counterpart = target_auth.ecdh_counterpart == request.user.username
        tokens_match = your_computed_token == their_stored_token
        
        return Response({
            "success": True,
            "target_username": target_username,
            "their_chosen_counterpart": target_auth.ecdh_counterpart,
            "you_are_counterpart": you_are_counterpart,
            "can_verify_authentication": tokens_match,
            "can_establish_ecdh": True,  # You can always compute a shared secret
            "message": (
                "✅ VERIFICATION SUCCESSFUL - You were their counterpart and tokens match" if tokens_match and you_are_counterpart
                else "❌ CANNOT VERIFY - You weren't their counterpart. You can establish ECDH but cannot verify their authentication."
            ),
            "explanation": (
                "True verification only works with the chosen counterpart. "
                "You can compute a shared secret with anyone, but that's different from verifying their authentication token."
            )
        }, status=200)
        
    except User.DoesNotExist:
        return Response({
            "error": "User not found"
        }, status=404)
    except UserKeys.DoesNotExist:
        return Response({
            "error": "Missing keys"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception during verification",
            "details": str(e)
        }, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_verifiable_users(request):
    """
    Get list of users whose authentication you can verify.
    
    IMPORTANT: You can only TRULY VERIFY users who chose YOU as their counterpart.
    
    This endpoint shows:
    1. Users who chose you as counterpart → TRUE VERIFICATION possible ✅
    2. Other users with ECDH keys → Can establish relationship, but NOT verify ⚠️
    """
    from main.models import UserKeys, WhiteflagAuthentication
    
    try:
        user_keys = UserKeys.objects.get(user=request.user)
        
        if not user_keys.private_diffie_hellman_key:
            return Response({
                "error": "You need an ECDH keypair to verify others"
            }, status=400)
        
        verifiable_users = []
        
        # Get ALL users with Method 2 authentication (universal verification)
        all_authentications = WhiteflagAuthentication.objects.filter(
            verification_method="2",
            is_active=True
        ).exclude(user=request.user).select_related('user')
        
        for auth in all_authentications:
            target_user = auth.user
            try:
                target_keys = UserKeys.objects.get(user=target_user)
                
                # Check if they have ECDH keys
                if target_keys.public_diffie_hellman_key:
                    is_counterpart = auth.ecdh_counterpart == request.user.username
                    verifiable_users.append({
                        "username": target_user.username,
                        "authentication_id": auth.id,
                        "public_key": target_keys.public_diffie_hellman_key,
                        "blockchain_address": target_keys.address,
                        "authenticated_at": auth.timestamp.isoformat(),
                        "can_truly_verify": is_counterpart,  # ✅ Only if you're counterpart
                        "can_establish_ecdh": True,          # ✅ Always (if keys exist)
                        "counterpart_in_their_auth": auth.ecdh_counterpart,
                        "you_are_counterpart": is_counterpart,
                        "verification_type": "counterpart" if is_counterpart else "ecdh_capable"
                    })
            except UserKeys.DoesNotExist:
                continue
        
        # Separate into truly verifiable vs just ECDH capable
        truly_verifiable = [u for u in verifiable_users if u["can_truly_verify"]]
        ecdh_capable = [u for u in verifiable_users if not u["can_truly_verify"]]
        
        return Response({
            "success": True,
            "truly_verifiable": truly_verifiable,
            "truly_verifiable_count": len(truly_verifiable),
            "ecdh_capable_users": ecdh_capable,
            "ecdh_capable_count": len(ecdh_capable),
            "total_count": len(verifiable_users),
            "message": (
                f"You can TRULY VERIFY {len(truly_verifiable)} users who chose you as counterpart. "
                f"You can ESTABLISH ECDH with {len(ecdh_capable)} other users (but not verify their auth)."
            )
        }, status=200)
        
    except UserKeys.DoesNotExist:
        return Response({
            "error": "No keys found for user"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception retrieving verifiable users",
            "details": str(e)
        }, status=500)


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def send_confirmation(request):
    """
    Send A(6) confirmation message to verify another user's authentication.
    
    Body:
    {
        "target_username": "user_to_confirm",
        "target_authentication_id": 123
    }
    """
    from main.models import WhiteflagAuthentication, Confirmation
    
    target_username = request.data.get("target_username")
    target_auth_id = request.data.get("target_authentication_id")
    
    if not target_username or not target_auth_id:
        return Response({
            "error": "Missing target_username or target_authentication_id"
        }, status=400)
    
    try:
        # Get target authentication
        target_auth = WhiteflagAuthentication.objects.get(
            id=target_auth_id,
            user__username=target_username,
            ecdh_counterpart=request.user.username,
            is_active=True
        )
        
        # Verify first (reuse verification logic)
        verify_response = verify_user_authentication(request)
        if verify_response.status_code != 200 or not verify_response.data.get("verification_passed"):
            return Response({
                "error": "Cannot confirm - verification failed"
            }, status=400)
        
        # TODO: Send A(6) confirmation message to blockchain
        # For now, just store the confirmation record
        
        confirmation = Confirmation.objects.create(
            confirmer=request.user,
            target_user=target_auth.user,
            target_authentication=target_auth,
            confirmation_type="6",
            transaction_hash="",  # TODO: Fill after blockchain submission
            is_active=True
        )
        
        return Response({
            "success": True,
            "confirmation_id": confirmation.id,
            "target_username": target_username,
            "message": f"Confirmation sent to {target_username}"
        }, status=200)
        
    except WhiteflagAuthentication.DoesNotExist:
        return Response({
            "error": "Authentication not found or not verifiable by you"
        }, status=404)
    except Exception as e:
        return Response({
            "error": "Exception sending confirmation",
            "details": str(e)
        }, status=500)


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_confirmations_received(request):
    """
    Get confirmations received for your authentications.
    """
    from main.models import Confirmation
    
    try:
        confirmations = Confirmation.objects.filter(
            target_user=request.user,
            is_active=True
        ).select_related('confirmer', 'target_authentication')
        
        confirmation_list = []
        for conf in confirmations:
            confirmation_list.append({
                "confirmer_username": conf.confirmer.username,
                "authentication_id": conf.target_authentication.id,
                "confirmation_type": conf.confirmation_type,
                "transaction_hash": conf.transaction_hash,
                "confirmed_at": conf.timestamp.isoformat(),
                "message": f"Confirmed by {conf.confirmer.username}"
            })
        
        return Response({
            "success": True,
            "confirmations_received": confirmation_list,
            "total_count": len(confirmation_list),
            "message": "Confirmations you have received"
        }, status=200)
        
    except Exception as e:
        return Response({
            "error": "Exception retrieving confirmations",
            "details": str(e)
        }, status=500)
