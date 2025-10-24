#!/bin/bash
# Test script to verify authentication messages are stored in Signal database
# Run this after deploying v1.0.23-auth-signal-fix-arm64

set -e

API_URL="https://api.whiteflagprotocol.net"
TOKEN=""  # Add your auth token here

echo "=== Testing Authentication Message Storage Fix ==="
echo "Date: $(date)"
echo ""

# Check if token is set
if [ -z "$TOKEN" ]; then
    echo "❌ ERROR: Please set your auth token in this script"
    echo "   Edit this file and add your token to the TOKEN variable"
    exit 1
fi

# Test account creation
echo "1. Creating test account..."
TEST_USERNAME="signal_test_$(date +%s)"
RESPONSE=$(curl -s -X POST "${API_URL}/v1/create_account/" \
    -H "Authorization: Token $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${TEST_USERNAME}\", \"password\": \"TestPass123!\"}")

echo "   Response: $RESPONSE"
echo ""

# Get test account token
echo "2. Getting auth token for test account..."
LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/v1/login/" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${TEST_USERNAME}\", \"password\": \"TestPass123!\"}")

TEST_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.token')
echo "   Token: ${TEST_TOKEN:0:20}..."
echo ""

# Generate ECDH keypair
echo "3. Generating ECDH keypair..."
ECDH_RESPONSE=$(curl -s -X POST "${API_URL}/v1/generate_ecdh_keypair/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json")

PUBLIC_KEY=$(echo $ECDH_RESPONSE | jq -r '.public_key')
echo "   Public key: ${PUBLIC_KEY:0:20}..."
echo ""

# Publish K(0)0A message
echo "4. Publishing K(0)0A message..."
K0A_RESPONSE=$(curl -s -X POST "${API_URL}/v1/publish_ecdh_key/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"public_key\": \"$PUBLIC_KEY\"}")

K0A_TX=$(echo $K0A_RESPONSE | jq -r '.transaction_hash')
K0A_SIGNAL_ID=$(echo $K0A_RESPONSE | jq -r '.signal_id')
echo "   TX Hash: $K0A_TX"
echo "   Signal ID: $K0A_SIGNAL_ID"
echo ""

# Check if Signal ID exists (NEW BEHAVIOR)
if [ "$K0A_SIGNAL_ID" != "null" ] && [ -n "$K0A_SIGNAL_ID" ]; then
    echo "   ✅ SUCCESS: K(0)0A message has signal_id in response!"
else
    echo "   ⚠️  WARNING: K(0)0A message has no signal_id (may be old version)"
fi
echo ""

# Submit A(0) authentication
echo "5. Submitting A(0) authentication..."
A0_RESPONSE=$(curl -s -X POST "${API_URL}/v1/self_authenticate/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json")

A0_TX=$(echo $A0_RESPONSE | jq -r '.transaction_hash')
A0_SIGNAL_ID=$(echo $A0_RESPONSE | jq -r '.signal_id')
A0_AUTH_ID=$(echo $A0_RESPONSE | jq -r '.authentication_id')
echo "   TX Hash: $A0_TX"
echo "   Signal ID: $A0_SIGNAL_ID"
echo "   Auth ID: $A0_AUTH_ID"
echo ""

# Check if Signal ID exists (NEW BEHAVIOR)
if [ "$A0_SIGNAL_ID" != "null" ] && [ -n "$A0_SIGNAL_ID" ]; then
    echo "   ✅ SUCCESS: A(0) message has signal_id in response!"
else
    echo "   ⚠️  WARNING: A(0) message has no signal_id (may be old version)"
fi
echo ""

# Query signals via API
echo "6. Querying signals via API..."
SIGNALS_RESPONSE=$(curl -s -X GET "${API_URL}/v1/signals/?sender__username=${TEST_USERNAME}" \
    -H "Authorization: Token $TEST_TOKEN")

SIGNAL_COUNT=$(echo $SIGNALS_RESPONSE | jq -r '.count // .length // 0')
echo "   Found $SIGNAL_COUNT signals"

# Check for K message
K_EXISTS=$(echo $SIGNALS_RESPONSE | jq -r '.results[] | select(.message_code == "K") | .id' || echo "")
if [ -n "$K_EXISTS" ]; then
    echo "   ✅ SUCCESS: K(0)0A message found in Signal database!"
    echo "      Signal ID: $K_EXISTS"
else
    echo "   ❌ FAIL: K(0)0A message NOT in Signal database"
fi

# Check for A message
A_EXISTS=$(echo $SIGNALS_RESPONSE | jq -r '.results[] | select(.message_code == "A") | .id' || echo "")
if [ -n "$A_EXISTS" ]; then
    echo "   ✅ SUCCESS: A(0) message found in Signal database!"
    echo "      Signal ID: $A_EXISTS"
else
    echo "   ❌ FAIL: A(0) message NOT in Signal database"
fi
echo ""

# Summary
echo "=== SUMMARY ==="
if [ -n "$K_EXISTS" ] && [ -n "$A_EXISTS" ]; then
    echo "✅ FIX VERIFIED: Both authentication messages stored in Signal database"
    echo "   - K(0)0A message: Signal ID $K_EXISTS"
    echo "   - A(0) message: Signal ID $A_EXISTS"
    echo ""
    echo "   Test account: $TEST_USERNAME"
    echo "   You can now query these via the API or Explorer"
    exit 0
else
    echo "❌ FIX NOT WORKING: Authentication messages missing from Signal database"
    echo "   - K(0)0A found: $([ -n \"$K_EXISTS\" ] && echo 'YES' || echo 'NO')"
    echo "   - A(0) found: $([ -n \"$A_EXISTS\" ] && echo 'YES' || echo 'NO')"
    echo ""
    echo "   Check deployment version and pod logs"
    exit 1
fi
