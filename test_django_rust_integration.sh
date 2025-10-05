#!/bin/bash

# Test script to verify Django -> Rust internal communication
# Tests all the endpoint paths we just fixed

echo "======================================"
echo "Django → Rust Integration Test"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BASE_URL="https://fennel.network/api/v1"
AUTH_TOKEN=""

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local auth_required="$5"
    
    echo "Testing: $name"
    echo "Endpoint: $method $endpoint"
    
    if [ "$auth_required" = "true" ]; then
        if [ -z "$AUTH_TOKEN" ]; then
            echo -e "${YELLOW}⚠ Skipping (requires authentication)${NC}"
            echo ""
            return
        fi
        AUTH_HEADER="-H \"Authorization: Token $AUTH_TOKEN\""
    else
        AUTH_HEADER=""
    fi
    
    if [ "$method" = "POST" ]; then
        response=$(curl -X POST "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            $AUTH_HEADER \
            -d "$data" \
            -s -w "\n%{http_code}" 2>&1)
    else
        response=$(curl -X GET "$BASE_URL$endpoint" \
            $AUTH_HEADER \
            -s -w "\n%{http_code}" 2>&1)
    fi
    
    # Split response and status code
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "Status: $http_code"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ Success${NC}"
        echo "Response: $(echo "$body" | head -c 200)..."
    elif [ "$http_code" = "401" ] || [ "$http_code" = "403" ]; then
        echo -e "${YELLOW}⚠ Authentication Required${NC}"
    elif [ "$http_code" = "500" ]; then
        echo -e "${RED}✗ Server Error (Django → Rust communication may have failed)${NC}"
        echo "Response: $body"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "Response: $(echo "$body" | head -c 200)"
    fi
    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Authentication (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Would you like to test with authentication? (y/n)"
read -r use_auth

if [ "$use_auth" = "y" ]; then
    echo "Enter your username:"
    read -r username
    echo "Enter your password:"
    read -rs password
    
    echo ""
    echo "Attempting login..."
    
    login_response=$(curl -X POST "$BASE_URL/auth/login/" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$username\",\"password\":\"$password\"}" \
        -s -w "\n%{http_code}" 2>&1)
    
    http_code=$(echo "$login_response" | tail -n1)
    body=$(echo "$login_response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        AUTH_TOKEN=$(echo "$body" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
        echo -e "${GREEN}✓ Login successful${NC}"
        echo "Token: ${AUTH_TOKEN:0:20}..."
    else
        echo -e "${RED}✗ Login failed${NC}"
        echo "Continuing with unauthenticated tests only..."
    fi
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Testing Crypto Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "(These internally call Rust /v1/generate_encryption_channel, /v1/accept_encryption_channel, etc.)"
echo ""

# Test 1: Generate Diffie-Hellman Keypair
# Django endpoint: /v1/crypto/dh/generate_keypair/
# Internally calls Rust: /v1/generate_encryption_channel
test_endpoint \
    "Generate DH Keypair" \
    "POST" \
    "/crypto/dh/generate_keypair/" \
    "{}" \
    "true"

# Test 2: Get Shared Secret
# Django endpoint: /v1/crypto/dh/get_shared_secret/
# Internally calls Rust: /v1/accept_encryption_channel
test_endpoint \
    "Get Shared Secret" \
    "POST" \
    "/crypto/dh/get_shared_secret/" \
    '{"private_key":"test_private","public_key":"test_public"}' \
    "true"

# Test 3: Encrypt Message
# Django endpoint: /v1/crypto/dh/dm/encrypt_message/
# Internally calls Rust: /v1/dh_encrypt
test_endpoint \
    "DH Encrypt Message" \
    "POST" \
    "/crypto/dh/dm/encrypt_message/" \
    '{"message":"test message","shared_secret":"test_secret"}' \
    "true"

# Test 4: Decrypt Message
# Django endpoint: /v1/crypto/dh/dm/decrypt_message/
# Internally calls Rust: /v1/dh_decrypt
test_endpoint \
    "DH Decrypt Message" \
    "POST" \
    "/crypto/dh/dm/decrypt_message/" \
    '{"message":"test_encrypted","shared_secret":"test_secret"}' \
    "true"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Testing Group Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "(These internally call Rust /v1/generate_encryption_channel)"
echo ""

# Test 5: Generate Group Keypair
# Django endpoint: /v1/group/generate_keypair/
# Internally calls Rust: /v1/generate_encryption_channel
test_endpoint \
    "Generate Group Keypair" \
    "POST" \
    "/group/generate_keypair/" \
    '{"group_id":1}' \
    "true"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Testing Whiteflag Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "(These use helper functions that internally call Rust endpoints)"
echo ""

# Test 6: Whiteflag Encode (calls subservice, not fennel-cli)
test_endpoint \
    "Whiteflag Encode" \
    "POST" \
    "/whiteflag/encode/" \
    '{"prefix":"WF","version":"1","encryptionIndicator":"0","duressIndicator":"0","messageCode":"T","referenceIndicator":"0","referencedMessage":"0000000000000000000000000000000000000000000000000000000000000000"}' \
    "false"

# Test 7: Whiteflag Healthcheck (tests fennel-cli connectivity)
test_endpoint \
    "Whiteflag Healthcheck" \
    "GET" \
    "/whiteflag/healthcheck/" \
    "" \
    "false"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✓ Green checkmarks = Endpoint working correctly"
echo "✗ Red X marks = Django → Rust communication failed"
echo "⚠ Yellow warnings = Authentication or other issues"
echo ""
echo "If you see 500 errors, it likely means:"
echo "1. Django couldn't reach the Rust service"
echo "2. Rust returned an error due to invalid test data"
echo "3. The endpoint path is still incorrect"
echo ""
echo "For authenticated tests, you'll need to provide valid:"
echo "- Keypairs (from previous generate_keypair call)"
echo "- Shared secrets (from previous operations)"
echo "- Group IDs (from your database)"
echo ""
