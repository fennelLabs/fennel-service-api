#!/bin/bash
set -e

API_URL="https://api.whiteflagprotocol.net"
TEST_USERNAME="signal_test_$(date +%s)"
TEST_PASSWORD="TestPass123!"

echo "=== Testing Authentication Message Storage Fix ==="
echo "Date: $(date)"
echo "Test Account: $TEST_USERNAME"
echo ""

# Step 1: Create account (public endpoint, no token needed)
echo "1. Creating test account..."
CREATE_RESPONSE=$(curl -s -X POST "${API_URL}/v1/fennel/create_account/" \
    -H "Content-Type: application/json" \
    -d "{\"username\": \"${TEST_USERNAME}\", \"password\": \"${TEST_PASSWORD}\"}")

echo "$CREATE_RESPONSE" | jq '.'
echo ""

# Check if account creation succeeded
if echo "$CREATE_RESPONSE" | jq -e '.token' > /dev/null 2>&1; then
    TEST_TOKEN=$(echo "$CREATE_RESPONSE" | jq -r '.token')
    echo "✅ Account created successfully"
    echo "   Token: ${TEST_TOKEN:0:30}..."
else
    echo "❌ Account creation failed"
    echo "$CREATE_RESPONSE"
    exit 1
fi
echo ""

# Step 2: Generate ECDH keypair
echo "2. Generating ECDH keypair..."
ECDH_RESPONSE=$(curl -s -X POST "${API_URL}/v1/whiteflag/generate_ecdh_keypair/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json")

PUBLIC_KEY=$(echo "$ECDH_RESPONSE" | jq -r '.public_key')
if [ "$PUBLIC_KEY" != "null" ] && [ -n "$PUBLIC_KEY" ]; then
    echo "✅ ECDH keypair generated"
    echo "   Public key: ${PUBLIC_KEY:0:30}..."
else
    echo "❌ ECDH keypair generation failed"
    echo "$ECDH_RESPONSE" | jq '.'
    exit 1
fi
echo ""

# Step 3: Publish K(0)0A message
echo "3. Publishing K(0)0A message (ECDH public key)..."
K0A_RESPONSE=$(curl -s -X POST "${API_URL}/v1/whiteflag/publish_ecdh_key/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"public_key\": \"$PUBLIC_KEY\"}")

echo "$K0A_RESPONSE" | jq '.'

K0A_TX=$(echo "$K0A_RESPONSE" | jq -r '.transaction_hash')
K0A_SIGNAL_ID=$(echo "$K0A_RESPONSE" | jq -r '.signal_id')

if [ "$K0A_SIGNAL_ID" != "null" ] && [ -n "$K0A_SIGNAL_ID" ]; then
    echo "✅ K(0)0A message published with signal_id: $K0A_SIGNAL_ID"
    echo "   TX Hash: $K0A_TX"
else
    echo "⚠️  K(0)0A published but no signal_id (old version?)"
    echo "   TX Hash: $K0A_TX"
fi
echo ""

# Step 4: Submit A(0) authentication
echo "4. Submitting A(0) self-authentication..."
A0_RESPONSE=$(curl -s -X POST "${API_URL}/v1/whiteflag/self_authenticate/" \
    -H "Authorization: Token $TEST_TOKEN" \
    -H "Content-Type: application/json")

echo "$A0_RESPONSE" | jq '.'

A0_TX=$(echo "$A0_RESPONSE" | jq -r '.transaction_hash')
A0_SIGNAL_ID=$(echo "$A0_RESPONSE" | jq -r '.signal_id')
A0_AUTH_ID=$(echo "$A0_RESPONSE" | jq -r '.authentication_id')

if [ "$A0_SIGNAL_ID" != "null" ] && [ -n "$A0_SIGNAL_ID" ]; then
    echo "✅ A(0) message published with signal_id: $A0_SIGNAL_ID"
    echo "   Auth ID: $A0_AUTH_ID"
    echo "   TX Hash: $A0_TX"
else
    echo "⚠️  A(0) published but no signal_id (old version?)"
    echo "   Auth ID: $A0_AUTH_ID"
    echo "   TX Hash: $A0_TX"
fi
echo ""

# Step 5: Wait a moment for database sync
echo "5. Waiting 5 seconds for database to sync..."
sleep 5
echo ""

# Step 6: Query signals via API
echo "6. Querying signals from Signal database..."
SIGNALS_RESPONSE=$(curl -s -X GET "${API_URL}/v1/signals/?sender__username=${TEST_USERNAME}" \
    -H "Authorization: Token $TEST_TOKEN")

echo "$SIGNALS_RESPONSE" | jq '.'
echo ""

SIGNAL_COUNT=$(echo "$SIGNALS_RESPONSE" | jq -r '.count // 0')
echo "   Found $SIGNAL_COUNT total signals"

# Check for K message
K_EXISTS=$(echo "$SIGNALS_RESPONSE" | jq -r '.results[]? | select(.message_code == "K") | .id' 2>/dev/null || echo "")
if [ -n "$K_EXISTS" ]; then
    echo "   ✅ K(0)0A message found in database (Signal ID: $K_EXISTS)"
else
    echo "   ❌ K(0)0A message NOT in database"
fi

# Check for A message
A_EXISTS=$(echo "$SIGNALS_RESPONSE" | jq -r '.results[]? | select(.message_code == "A") | .id' 2>/dev/null || echo "")
if [ -n "$A_EXISTS" ]; then
    echo "   ✅ A(0) message found in database (Signal ID: $A_EXISTS)"
else
    echo "   ❌ A(0) message NOT in database"
fi
echo ""

# Final summary
echo "=== VERIFICATION RESULT ==="
if [ -n "$K_EXISTS" ] && [ -n "$A_EXISTS" ]; then
    echo "🎉 SUCCESS! Both authentication messages stored in Signal database"
    echo ""
    echo "Details:"
    echo "  Test Account: $TEST_USERNAME"
    echo "  K(0)0A Signal: $K_EXISTS (TX: $K0A_TX)"
    echo "  A(0) Signal: $A_EXISTS (TX: $A0_TX)"
    echo "  Auth Record: $A0_AUTH_ID"
    echo ""
    echo "✅ Fix v1.0.23 is working correctly!"
    exit 0
else
    echo "❌ FAILED - Messages not in database"
    echo ""
    echo "Status:"
    echo "  K(0)0A in DB: $([ -n "$K_EXISTS" ] && echo 'YES' || echo 'NO')"
    echo "  A(0) in DB: $([ -n "$A_EXISTS" ] && echo 'YES' || echo 'NO')"
    echo ""
    echo "This may indicate:"
    echo "  - Old version still deployed"
    echo "  - Pods not updated yet"
    echo "  - Database sync delay"
    exit 1
fi
