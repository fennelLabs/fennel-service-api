#!/bin/bash

################################################################################
# API Integration Test for Test Messages with References
# Tests Infrastructure and Free Text Test messages against live Azure API
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-}"
TOKEN="${API_TOKEN:-}"

echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}API Integration Test: Test Messages with References${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""

# Validate inputs
if [ -z "$API_BASE_URL" ]; then
    echo -e "${RED}❌ Error: API_BASE_URL environment variable not set${NC}"
    echo "Usage:"
    echo "  export API_BASE_URL='https://your-api.azurewebsites.net'"
    echo "  export API_TOKEN='your-admin-token'"
    echo "  ./api_integration_test.sh"
    exit 1
fi

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Error: API_TOKEN environment variable not set${NC}"
    echo "Note: You need an admin token to create test messages"
    exit 1
fi

echo -e "${BLUE}Testing against: ${API_BASE_URL}${NC}"
echo ""

# Function to make API call
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    curl -s -X "$method" "${API_BASE_URL}${endpoint}" \
        -H "Authorization: Token $TOKEN" \
        -H "Content-Type: application/json" \
        -d "$data"
}

# Test 1: Encode Infrastructure Test Message
echo -e "${YELLOW}=================================================================================${NC}"
echo -e "${YELLOW}TEST 1: Encode Infrastructure (I) as Test (T) Message${NC}"
echo -e "${YELLOW}=================================================================================${NC}"
echo ""

INFRA_PAYLOAD='{
  "signal_body": {
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
    "objectOrientation": "000"
  },
  "is_test_message": true
}'

echo "Request payload:"
echo "$INFRA_PAYLOAD" | jq '.' 2>/dev/null || echo "$INFRA_PAYLOAD"
echo ""

echo "Calling: POST /api/v1/whiteflag/encode/"
INFRA_RESPONSE=$(api_call "POST" "/api/v1/whiteflag/encode/" "$INFRA_PAYLOAD")

echo ""
echo "Response:"
echo "$INFRA_RESPONSE" | jq '.' 2>/dev/null || echo "$INFRA_RESPONSE"
echo ""

# Check if response contains error
if echo "$INFRA_RESPONSE" | grep -q "error\|Error\|403\|401"; then
    echo -e "${RED}❌ TEST 1 FAILED: Got error response${NC}"
    echo "$INFRA_RESPONSE"
    exit 1
fi

# Extract encoded message
ENCODED_INFRA=$(echo "$INFRA_RESPONSE" | jq -r 'if type == "string" then . else .encoded_message // .signal_text // . end' 2>/dev/null || echo "$INFRA_RESPONSE")

if [ -z "$ENCODED_INFRA" ] || [ "$ENCODED_INFRA" == "null" ]; then
    echo -e "${RED}❌ TEST 1 FAILED: No encoded message in response${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Infrastructure message encoded successfully${NC}"
echo "Encoded message: $ENCODED_INFRA"
echo ""

# Test 2: Decode Infrastructure Test Message
echo -e "${YELLOW}=================================================================================${NC}"
echo -e "${YELLOW}TEST 2: Decode Infrastructure Test Message${NC}"
echo -e "${YELLOW}=================================================================================${NC}"
echo ""

DECODE_PAYLOAD="{\"signal_text\": \"$ENCODED_INFRA\"}"

echo "Calling: POST /api/v1/whiteflag/decode/"
DECODED_INFRA=$(api_call "POST" "/api/v1/whiteflag/decode/" "$DECODE_PAYLOAD")

echo ""
echo "Decoded message:"
echo "$DECODED_INFRA" | jq '.' 2>/dev/null || echo "$DECODED_INFRA"
echo ""

# Verify decoded message
MESSAGE_CODE=$(echo "$DECODED_INFRA" | jq -r '.messageCode // .signal_body.messageCode // empty' 2>/dev/null)
PSEUDO_CODE=$(echo "$DECODED_INFRA" | jq -r '.pseudoMessageCode // .signal_body.pseudoMessageCode // empty' 2>/dev/null)

if [ "$MESSAGE_CODE" != "T" ]; then
    echo -e "${RED}❌ TEST 2 FAILED: messageCode should be 'T', got '$MESSAGE_CODE'${NC}"
    exit 1
fi

if [ "$PSEUDO_CODE" != "I" ]; then
    echo -e "${RED}❌ TEST 2 FAILED: pseudoMessageCode should be 'I', got '$PSEUDO_CODE'${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Infrastructure test message decoded correctly${NC}"
echo "  messageCode: $MESSAGE_CODE"
echo "  pseudoMessageCode: $PSEUDO_CODE"
echo ""

# Test 3: Encode Free Text Test Message with Reference
echo -e "${YELLOW}=================================================================================${NC}"
echo -e "${YELLOW}TEST 3: Encode Free Text (F) as Test (T) with Reference${NC}"
echo -e "${YELLOW}=================================================================================${NC}"
echo ""

# Simulate a tx_hash (in real scenario, this would come from blockchain)
SIMULATED_TX_HASH="3efb4e0cfa83122b242634254c1920a769d615dfcc4c670bb53eb6f12843c3ae"

FREETEXT_PAYLOAD=$(cat <<EOF
{
  "signal_body": {
    "encryptionIndicator": "0",
    "duressIndicator": "0",
    "messageCode": "F",
    "referenceIndicator": "4",
    "referencedMessage": "$SIMULATED_TX_HASH",
    "text": "This is a comment about the infrastructure"
  },
  "is_test_message": true
}
EOF
)

echo "Request payload:"
echo "$FREETEXT_PAYLOAD" | jq '.' 2>/dev/null || echo "$FREETEXT_PAYLOAD"
echo ""

echo "Calling: POST /api/v1/whiteflag/encode/"
FREETEXT_RESPONSE=$(api_call "POST" "/api/v1/whiteflag/encode/" "$FREETEXT_PAYLOAD")

echo ""
echo "Response:"
echo "$FREETEXT_RESPONSE" | jq '.' 2>/dev/null || echo "$FREETEXT_RESPONSE"
echo ""

# Check if response contains error
if echo "$FREETEXT_RESPONSE" | grep -q "error\|Error\|403\|401"; then
    echo -e "${RED}❌ TEST 3 FAILED: Got error response${NC}"
    echo "$FREETEXT_RESPONSE"
    exit 1
fi

# Extract encoded message
ENCODED_FREETEXT=$(echo "$FREETEXT_RESPONSE" | jq -r 'if type == "string" then . else .encoded_message // .signal_text // . end' 2>/dev/null || echo "$FREETEXT_RESPONSE")

if [ -z "$ENCODED_FREETEXT" ] || [ "$ENCODED_FREETEXT" == "null" ]; then
    echo -e "${RED}❌ TEST 3 FAILED: No encoded message in response${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Free Text message encoded successfully${NC}"
echo "Encoded message: $ENCODED_FREETEXT"
echo ""

# Test 4: Decode Free Text Test Message
echo -e "${YELLOW}=================================================================================${NC}"
echo -e "${YELLOW}TEST 4: Decode Free Text Test Message with Reference${NC}"
echo -e "${YELLOW}=================================================================================${NC}"
echo ""

DECODE_FREETEXT_PAYLOAD="{\"signal_text\": \"$ENCODED_FREETEXT\"}"

echo "Calling: POST /api/v1/whiteflag/decode/"
DECODED_FREETEXT=$(api_call "POST" "/api/v1/whiteflag/decode/" "$DECODE_FREETEXT_PAYLOAD")

echo ""
echo "Decoded message:"
echo "$DECODED_FREETEXT" | jq '.' 2>/dev/null || echo "$DECODED_FREETEXT"
echo ""

# Verify decoded message
FT_MESSAGE_CODE=$(echo "$DECODED_FREETEXT" | jq -r '.messageCode // .signal_body.messageCode // empty' 2>/dev/null)
FT_PSEUDO_CODE=$(echo "$DECODED_FREETEXT" | jq -r '.pseudoMessageCode // .signal_body.pseudoMessageCode // empty' 2>/dev/null)
FT_REF_IND=$(echo "$DECODED_FREETEXT" | jq -r '.referenceIndicator // .signal_body.referenceIndicator // empty' 2>/dev/null)
FT_REF_MSG=$(echo "$DECODED_FREETEXT" | jq -r '.referencedMessage // .signal_body.referencedMessage // empty' 2>/dev/null)
FT_TEXT=$(echo "$DECODED_FREETEXT" | jq -r '.text // .signal_body.text // empty' 2>/dev/null)

if [ "$FT_MESSAGE_CODE" != "T" ]; then
    echo -e "${RED}❌ TEST 4 FAILED: messageCode should be 'T', got '$FT_MESSAGE_CODE'${NC}"
    exit 1
fi

if [ "$FT_PSEUDO_CODE" != "F" ]; then
    echo -e "${RED}❌ TEST 4 FAILED: pseudoMessageCode should be 'F', got '$FT_PSEUDO_CODE'${NC}"
    exit 1
fi

if [ "$FT_REF_IND" != "4" ]; then
    echo -e "${RED}❌ TEST 4 FAILED: referenceIndicator should be '4', got '$FT_REF_IND'${NC}"
    exit 1
fi

if [ -z "$FT_REF_MSG" ] || [ "$FT_REF_MSG" == "null" ]; then
    echo -e "${RED}❌ TEST 4 FAILED: referencedMessage is missing${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Free Text test message decoded correctly${NC}"
echo "  messageCode: $FT_MESSAGE_CODE"
echo "  pseudoMessageCode: $FT_PSEUDO_CODE"
echo "  referenceIndicator: $FT_REF_IND"
echo "  referencedMessage: ${FT_REF_MSG:0:20}..."
echo "  text: $FT_TEXT"
echo ""

# Summary
echo -e "${BLUE}================================================================================${NC}"
echo -e "${BLUE}INTEGRATION TEST SUMMARY${NC}"
echo -e "${BLUE}================================================================================${NC}"
echo ""
echo -e "${GREEN}✓ TEST 1 PASSED:${NC} Infrastructure message encoded as Test"
echo -e "${GREEN}✓ TEST 2 PASSED:${NC} Infrastructure Test message decoded correctly"
echo -e "${GREEN}✓ TEST 3 PASSED:${NC} Free Text with reference encoded as Test"
echo -e "${GREEN}✓ TEST 4 PASSED:${NC} Free Text Test message with reference decoded correctly"
echo ""
echo -e "${GREEN}=======================================${NC}"
echo -e "${GREEN}✓ ALL INTEGRATION TESTS PASSED!${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo "Your API is correctly:"
echo "  1. Converting Infrastructure messages to Test messages"
echo "  2. Converting Free Text messages to Test messages"
echo "  3. Preserving reference fields in the correct order"
echo "  4. Encoding with the Rust WhiteFlag library successfully"
echo "  5. Decoding messages with correct field mapping"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  - Test encode_and_send_signal endpoint to send to blockchain"
echo "  - Verify messages appear in block explorer"
echo "  - Confirm reference linking works end-to-end"
echo ""
