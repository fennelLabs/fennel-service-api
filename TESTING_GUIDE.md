# Manual Testing Guide: K(0)0A Blockchain Submission Fix

**Version:** v1.0.21-k0a-blockchain-fix-arm64  
**Date:** October 23, 2025  
**Purpose:** Verify that K(0)0A messages are now submitted to blockchain

---

## Quick Start: Automated Test

### Prerequisites

```bash
# Install jq for JSON parsing
sudo apt-get install jq

# Set your credentials
export TEST_USERNAME="your_username"
export TEST_PASSWORD="your_password"
export API_BASE_URL="https://api.whiteflag.network"  # Optional, defaults to this

# Optional: Timo API credentials for verification
export TIMO_USERNAME="timo_username"
export TIMO_PASSWORD="timo_password"
```

### Run the Test Script

```bash
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api
chmod +x test-k0a-blockchain-fix.sh
./test-k0a-blockchain-fix.sh
```

### Expected Output

```
═══════════════════════════════════════════════════════
  ECDH Method 2 Authentication - Complete Flow Test
═══════════════════════════════════════════════════════

✓ curl is installed
✓ jq is installed
✓ Credentials configured
✓ Authentication token obtained
✓ ECDH keypair generated successfully
✓ K(0)0A message published successfully
✓ Transaction hash returned: abc123...
✓ Block number: 335030
✓ A(0) authentication submitted successfully
✓ All tests completed successfully!
```

---

## Manual Testing: Step-by-Step

### Step 0: Get Authentication Token

```bash
# Login to get auth token
curl -X POST "https://api.whiteflag.network/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}' | jq

# Save the token
export TOKEN="your_token_here"
```

**Expected Response:**
```json
{
  "token": "abc123def456...",
  "user_id": 31,
  "username": "watcher"
}
```

---

### Step 1: Generate ECDH Keypair

```bash
curl -X POST "https://api.whiteflag.network/api/v1/ecdh/generate_keypair/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${TOKEN}" | jq
```

**Expected Response:**
```json
{
  "success": true,
  "private_key": "7b62277fc19c9b918157c7053e4c52f96778392ea983a9e575f5210e4409dd2c",
  "public_key": "7dd064a77fe3d0ab5c0ace159e39b1d1666c11f502a188105e557f5869c43242",
  "message": "ECDH keypair generated and stored."
}
```

**Validation:**
- ✓ `success` is `true`
- ✓ `public_key` is 64 hex characters (32 bytes)
- ✓ `private_key` is 64 hex characters (32 bytes)

**Save the public key:**
```bash
export PUBLIC_KEY="7dd064a77fe3d0ab5c0ace159e39b1d1666c11f502a188105e557f5869c43242"
```

---

### Step 2: Publish K(0)0A Message (CRITICAL TEST)

**This is where the bug was fixed!**

```bash
curl -X POST "https://api.whiteflag.network/api/v1/whiteflag/publish_ecdh_key/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${TOKEN}" \
  -d "{\"public_key\":\"${PUBLIC_KEY}\"}" | jq
```

**Expected Response (FIXED VERSION):**
```json
{
  "success": true,
  "encoded_message": "57463130304333000000000000000000000000000000000000...",
  "transaction_hash": "1a2b3c4d5e6f7890abcdef1234567890abcdef1234567890abcdef1234567890",
  "block_number": 335030,
  "block_hash": "0x9876543210fedcba0987654321fedcba0987654321fedcba0987654321fedcba",
  "message_code": "K",
  "reference_code": "0",
  "crypto_data_type": "0A",
  "public_key": "7dd064a77fe3d0ab5c0ace159e39b1d1666c11f502a188105e557f5869c43242",
  "message": "✅ K(0)0A message published successfully to blockchain"
}
```

**OLD RESPONSE (BUG PRESENT):**
```json
{
  "success": true,
  "encoded_message": "57463130304333000000000000000000000000000000000000...",
  "message_code": "K",
  "reference_code": "0",
  "crypto_data_type": "0A",
  "public_key": "7dd064a77fe3d0ab5c0ace159e39b1d1666c11f502a188105e557f5869c43242",
  "message": "ECDH public key published successfully"
}
```

**CRITICAL VALIDATION:**

| Field | Old (Bug) | New (Fixed) | Status |
|-------|-----------|-------------|--------|
| `transaction_hash` | ❌ Missing | ✅ Present | **REQUIRED** |
| `block_number` | ❌ Missing | ✅ Present | **REQUIRED** |
| `block_hash` | ❌ Missing | ✅ Present | **REQUIRED** |
| `encoded_message` | ✅ Present | ✅ Present | Present in both |

**If `transaction_hash` is missing, the bug is STILL PRESENT!**

**Save the transaction details:**
```bash
export K0A_TX_HASH="your_tx_hash"
export K0A_BLOCK_NUMBER="335030"
```

---

### Step 3: Submit A(0) Authentication

```bash
curl -X POST "https://api.whiteflag.network/api/v1/whiteflag/self_authenticate/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token ${TOKEN}" \
  -d '{"organization_name":"Test Organization"}' | jq
```

**Expected Response:**
```json
{
  "success": true,
  "authentication_id": 45,
  "authentication_type": "self_ecdh_universal",
  "transaction_hash": "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210",
  "encoded_message": "574631302080000000000000000000000000000000000000...",
  "block_number": 335031,
  "block_hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
  "verifiable_by": "anyone_with_ecdh_keys",
  "message": "✅ Self-authenticated! A(0) message submitted to blockchain."
}
```

**Validation:**
- ✓ `success` is `true`
- ✓ `transaction_hash` is present
- ✓ `block_number` is K0A_BLOCK_NUMBER + 1 or greater

---

### Step 4: Verify on Blockchain

#### Option A: Query Blockchain Scanner

```bash
# Scan blocks around your messages
curl "https://api.whiteflagprotocol.net/blockchains/fennel-solonet/scan?from=${K0A_BLOCK_NUMBER}&to=$((K0A_BLOCK_NUMBER + 5))" \
  -u username:password | jq
```

**Expected:** Should show both K and A messages

#### Option B: Query Specific Transaction

```bash
# Get K(0)0A message by transaction hash
curl "https://api.whiteflagprotocol.net/messages?transactionHash=${K0A_TX_HASH}" \
  -u username:password | jq
```

**Expected Response:**
```json
[
  {
    "MetaHeader": {
      "blockchain": "fennel-solonet",
      "blockNumber": 335030,
      "transactionHash": "1a2b3c4d5e6f7890abcdef1234567890...",
      "originatorAddress": "5Cie9KHQ4qJqfvQCjL7c4QzdHnYPSAWxDyuBiaD8SvTXtU8j"
    },
    "MessageHeader": {
      "MessageCode": "K",
      "ReferenceIndicator": "0"
    },
    "MessageBody": {
      "CryptoDataType": "0A",
      "CryptoData": "7dd064a77fe3d0ab5c0ace159e39b1d1666c11f502a188105e557f5869c43242"
    }
  }
]
```

#### Option C: Query by Originator Address

First, get your originator address:

```bash
curl "https://api.whiteflag.network/api/v1/user/keys/" \
  -H "Authorization: Token ${TOKEN}" | jq '.address'

export ORIGINATOR_ADDRESS="5Cie9KHQ4qJqfvQCjL7c4QzdHnYPSAWxDyuBiaD8SvTXtU8j"
```

Then query Timo API:

```bash
# Find all K messages from your address
curl "https://api.whiteflagprotocol.net/messages?originatorAddress=${ORIGINATOR_ADDRESS}&messageCode=K" \
  -u username:password | jq

# Find all A messages from your address
curl "https://api.whiteflagprotocol.net/messages?originatorAddress=${ORIGINATOR_ADDRESS}&messageCode=A" \
  -u username:password | jq
```

---

### Step 5: Check Timo API Logs (If Available)

If you have access to the Timo API server logs:

```bash
# SSH into Timo API server
ssh user@api.whiteflagprotocol.net

# Check logs for your transaction
journalctl -u whiteflag-api --since "5 minutes ago" | grep -i "authenticate\|K(0)0A"
```

**Before Fix (ERROR):**
```
[DEBUG] authenticate: Unknown originator authentication token in A2(0) message
```

**After Fix (SUCCESS):**
```
[DEBUG] receive: Successfully processed incoming K(0)0A message
[DEBUG] receive: Successfully processed incoming A2(0) message
[DEBUG] authenticate: Authentication verified for originator
```

---

## Frontend Testing: Authentication Wizard

### Test via Web UI

1. **Navigate to:** https://whiteflag.network
2. **Login** with your credentials
3. **Click:** "Authenticate" button in header
4. **Complete Step 1:** Generate ECDH Keypair
   - Should show success with public key display
   
5. **Complete Step 2:** Publish Public Key
   - **OLD BUG:** Shows success message (but no blockchain proof)
   - **FIXED:** Shows success with transaction hash and block number
   
6. **Complete Step 3:** Submit Authentication
   - Should show success with transaction hash and block number

### Frontend Validation Checklist

After Step 2, check the browser console (F12 → Console):

**OLD VERSION (Bug Present):**
```javascript
{
  success: true,
  encoded_message: "5746313030433300...",
  message: "ECDH public key published successfully"
  // ❌ No transaction_hash
  // ❌ No block_number
}
```

**NEW VERSION (Fixed):**
```javascript
{
  success: true,
  encoded_message: "5746313030433300...",
  transaction_hash: "1a2b3c4d5e6f...",  // ✅ Present
  block_number: 335030,                  // ✅ Present
  block_hash: "0x987654321...",          // ✅ Present
  message: "✅ K(0)0A message published successfully to blockchain"
}
```

---

## Troubleshooting

### Problem: No `transaction_hash` in Step 2 response

**Diagnosis:** The bug fix was not deployed correctly

**Solution:**
```bash
# Check deployed version
kubectl get deployment/fennel-api -n fennel-api -o jsonpath='{.spec.template.spec.containers[0].image}'

# Should show: fennelacr531.azurecr.io/fennel-service-api:v1.0.21-k0a-blockchain-fix-arm64

# If not, redeploy:
kubectl set image deployment/fennel-api \
  fennel-api=fennelacr531.azurecr.io/fennel-service-api:v1.0.21-k0a-blockchain-fix-arm64 \
  -n fennel-api
```

### Problem: "Unknown originator authentication token" in Timo API

**Diagnosis:** K(0)0A message was not found on blockchain

**Check:**
1. Did Step 2 return a `transaction_hash`?
2. Is the transaction hash valid on blockchain?
3. Query Timo API for K messages from your address

**Solution:** Re-test the complete flow with the fixed backend

### Problem: Blockchain submission timeout

**Error Response:**
```json
{
  "error": "Blockchain submission timed out",
  "encoded_message": "574631303043330...",
  "note": "Message encoded but submission timed out. Try again or submit manually."
}
```

**Diagnosis:** Subservice or blockchain node is slow/unavailable

**Solutions:**
1. Wait and retry in a few minutes
2. Check subservice status: `kubectl get pods -n fennel-api -l app=subservice`
3. Check blockchain node connectivity
4. Manual submission using the `encoded_message` value

---

## Success Criteria

✅ **Test PASSES if:**
1. Step 1: Keypair generated with 64-char hex keys
2. Step 2: Response includes `transaction_hash`, `block_number`, `block_hash`
3. Step 3: Authentication submitted successfully with `transaction_hash`
4. Timo API finds both K(0)0A and A(0) messages
5. No "Unknown originator authentication token" errors in Timo logs

❌ **Test FAILS if:**
1. Step 2: Response missing `transaction_hash`
2. Step 2: Response only contains `encoded_message` but no blockchain proof
3. Timo API cannot find K(0)0A message
4. Timo API logs show "Unknown originator authentication token"

---

## Quick Reference: Key Differences

### Old Code (Bug Present)

```python
# publish_ecdh_key() - OLD
encoded_message, success = whiteflag_encoder_helper(payload)
return Response({
    "success": True,
    "encoded_message": encoded_message,  # ❌ Only encoded, not submitted!
})
```

### New Code (Fixed)

```python
# publish_ecdh_key() - FIXED
encoded_message, success = whiteflag_encoder_helper(payload)

# ✅ Submit to blockchain
blockchain_response = requests.post(
    f"{os.environ.get('FENNEL_SUBSERVICE_IP')}/send_new_signal_with_blockchain_data",
    data={"mnemonic": user_keys.mnemonic, "content": encoded_message}
)

# ✅ Return blockchain proof
return Response({
    "success": True,
    "encoded_message": encoded_message,
    "transaction_hash": tx_hash,        # ✅ Blockchain proof
    "block_number": block_number,       # ✅ Block confirmation
    "block_hash": block_hash            # ✅ Block verification
})
```

---

## Additional Resources

- **Whiteflag Protocol Spec:** https://standard.whiteflagprotocol.org/
- **ECDH Authentication (Method 2):** Section 5.1.6
- **Crypto Messages (K type):** Section 5.2.2
- **Timo API Documentation:** https://github.com/WhiteflagProtocol/whiteflag-api
- **Bug Fix Documentation:** `/DOCUMENTATION/AUTHENTICATIONOCT182025/ECDHattempt2/DEPLOYMENTNOTES/bugfix2.md`

---

**Questions or Issues?**

If tests fail or you encounter unexpected behavior:
1. Check the deployment version
2. Review pod logs: `kubectl logs -n fennel-api deployment/fennel-api`
3. Verify subservice is running: `kubectl get pods -n fennel-api`
4. Check this documentation: `bugfix2.md`
