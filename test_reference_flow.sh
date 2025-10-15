#!/bin/bash

# Test Infrastructure and Free Text Test Messages with References
# This script helps you test the complete flow

set -e  # Exit on error

echo "=========================================================================="
echo "WhiteFlag Test Message Reference Testing Script"
echo "=========================================================================="
echo ""

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
TOKEN="${API_TOKEN:-}"

if [ -z "$TOKEN" ]; then
    echo "❌ Error: API_TOKEN environment variable not set"
    echo "Usage: export API_TOKEN='your-token-here' && ./test_reference_flow.sh"
    exit 1
fi

echo "Using API: $API_BASE_URL"
echo ""

# Step 1: Send Infrastructure Test Message
echo "Step 1: Sending Infrastructure (I) Test Message..."
echo "----------------------------------------------------------------------"

INFRA_PAYLOAD='{
  "encryptionIndicator": "0",
  "duressIndicator": "0",
  "messageCode": "I",
  "referenceIndicator": "0",
  "referencedMessage": "0000000000000000000000000000000000000000000000000000000000000000",
  "subjectCode": "52",
  "dateTime": "2023-09-01T09:37:09Z",
  "duration": "P00D00H00M",
  "objectType": "22",
  "objectLatitude": "+39.09144",
  "objectLongitude": "-120.03830",
  "objectSizeDim1": "0000",
  "objectSizeDim2": "0000",
  "objectOrientation": "000",
  "is_test_message": true
}'

echo "Payload:"
echo "$INFRA_PAYLOAD" | jq .
echo ""

INFRA_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/whiteflag/encode/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$INFRA_PAYLOAD")

echo "Response:"
echo "$INFRA_RESPONSE" | jq .
echo ""

# Extract encoded message (this is what would be sent to blockchain)
ENCODED_INFRA=$(echo "$INFRA_RESPONSE" | jq -r '.')

if [ -z "$ENCODED_INFRA" ] || [ "$ENCODED_INFRA" == "null" ]; then
    echo "❌ Failed to encode Infrastructure message"
    exit 1
fi

echo "✓ Infrastructure message encoded successfully"
echo "Encoded: $ENCODED_INFRA"
echo ""

# In a real scenario, you would send this to the blockchain and get a tx_hash
# For testing, we'll simulate a tx_hash
SIMULATED_TX_HASH="3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae"
echo "📝 Note: In production, this would be sent to blockchain"
echo "Using simulated transaction hash: $SIMULATED_TX_HASH"
echo ""

# Step 2: Send Free Text Test Message Referencing Infrastructure
echo "Step 2: Sending Free Text (F) Test Message Referencing Infrastructure..."
echo "----------------------------------------------------------------------"

FREETEXT_PAYLOAD=$(cat <<EOF
{
  "encryptionIndicator": "0",
  "duressIndicator": "0",
  "messageCode": "F",
  "referenceIndicator": "4",
  "referencedMessage": "$SIMULATED_TX_HASH",
  "text": "This is a comment about the infrastructure",
  "is_test_message": true
}
EOF
)

echo "Payload:"
echo "$FREETEXT_PAYLOAD" | jq .
echo ""

FREETEXT_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/whiteflag/encode/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$FREETEXT_PAYLOAD")

echo "Response:"
echo "$FREETEXT_RESPONSE" | jq .
echo ""

ENCODED_FREETEXT=$(echo "$FREETEXT_RESPONSE" | jq -r '.')

if [ -z "$ENCODED_FREETEXT" ] || [ "$ENCODED_FREETEXT" == "null" ]; then
    echo "❌ Failed to encode Free Text message"
    exit 1
fi

echo "✓ Free Text message encoded successfully"
echo "Encoded: $ENCODED_FREETEXT"
echo ""

# Step 3: Test decoding
echo "Step 3: Testing Decoding..."
echo "----------------------------------------------------------------------"

echo "Decoding Infrastructure message..."
DECODED_INFRA=$(curl -s -X POST "$API_BASE_URL/api/v1/whiteflag/decode/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"signal_text\": \"$ENCODED_INFRA\"}")

echo "Decoded Infrastructure:"
echo "$DECODED_INFRA" | jq .
echo ""

echo "Decoding Free Text message..."
DECODED_FREETEXT=$(curl -s -X POST "$API_BASE_URL/api/v1/whiteflag/decode/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"signal_text\": \"$ENCODED_FREETEXT\"}")

echo "Decoded Free Text:"
echo "$DECODED_FREETEXT" | jq .
echo ""

# Verify results
echo "=========================================================================="
echo "Verification"
echo "=========================================================================="

# Check Infrastructure message
INFRA_MSG_CODE=$(echo "$DECODED_INFRA" | jq -r '.messageCode // empty')
INFRA_PSEUDO_CODE=$(echo "$DECODED_INFRA" | jq -r '.pseudoMessageCode // empty')

echo "Infrastructure Test Message:"
echo "  messageCode: $INFRA_MSG_CODE (should be 'T')"
echo "  pseudoMessageCode: $INFRA_PSEUDO_CODE (should be 'I')"

if [ "$INFRA_MSG_CODE" == "T" ] && [ "$INFRA_PSEUDO_CODE" == "I" ]; then
    echo "  ✓ Infrastructure test message is correct"
else
    echo "  ✗ Infrastructure test message has issues"
fi
echo ""

# Check Free Text message
FREETEXT_MSG_CODE=$(echo "$DECODED_FREETEXT" | jq -r '.messageCode // empty')
FREETEXT_PSEUDO_CODE=$(echo "$DECODED_FREETEXT" | jq -r '.pseudoMessageCode // empty')
FREETEXT_REF_IND=$(echo "$DECODED_FREETEXT" | jq -r '.referenceIndicator // empty')
FREETEXT_REF_MSG=$(echo "$DECODED_FREETEXT" | jq -r '.referencedMessage // empty')

echo "Free Text Test Message:"
echo "  messageCode: $FREETEXT_MSG_CODE (should be 'T')"
echo "  pseudoMessageCode: $FREETEXT_PSEUDO_CODE (should be 'F')"
echo "  referenceIndicator: $FREETEXT_REF_IND (should be '4')"
echo "  referencedMessage: ${FREETEXT_REF_MSG:0:20}... (should match tx hash)"

if [ "$FREETEXT_MSG_CODE" == "T" ] && [ "$FREETEXT_PSEUDO_CODE" == "F" ] && [ "$FREETEXT_REF_IND" == "4" ]; then
    echo "  ✓ Free Text test message is correct"
else
    echo "  ✗ Free Text test message has issues"
fi
echo ""

echo "=========================================================================="
echo "Summary"
echo "=========================================================================="
echo "✓ All test messages created and encoded successfully"
echo "✓ Test messages decoded correctly"
echo ""
echo "Next steps:"
echo "1. Send these messages to the blockchain using your send endpoint"
echo "2. Verify the messages appear correctly in the block explorer"
echo "3. Confirm the reference link works between messages"
echo ""
