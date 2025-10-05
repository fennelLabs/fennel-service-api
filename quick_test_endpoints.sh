#!/bin/bash

# Quick test to verify Django → Rust crypto endpoint fixes
# This tests the endpoint paths we just updated

echo "======================================"
echo "Quick Django → Rust Endpoint Test"
echo "======================================"
echo ""

BASE_URL="https://fennel.network/api/v1"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Creating a test account..."
USERNAME="test_user_$(date +%s)"
PASSWORD="TestPass123!"

register_response=$(curl -X POST "$BASE_URL/auth/register/" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"email\":\"${USERNAME}@test.com\"}" \
    -s -w "\n%{http_code}")

http_code=$(echo "$register_response" | tail -n1)
body=$(echo "$register_response" | head -n-1)

if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
    AUTH_TOKEN=$(echo "$body" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Test account created${NC}"
    echo "Token: ${AUTH_TOKEN:0:30}..."
    echo ""
else
    echo -e "${RED}✗ Failed to create test account${NC}"
    echo "Response: $body"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 1: Generate DH Keypair"
echo "Django: /v1/crypto/dh/generate_keypair/"
echo "Rust:   /v1/generate_encryption_channel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response=$(curl -X POST "$BASE_URL/crypto/dh/generate_keypair/" \
    -H "Authorization: Token $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -s -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "Status: $http_code"
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS - Django → Rust communication working!${NC}"
    echo "Response: $(echo "$body" | head -c 150)..."
    
    # Extract keys for next tests
    PUBLIC_KEY=$(echo "$body" | grep -o '"public_key":"[^"]*"' | cut -d'"' -f4)
    SECRET_KEY=$(echo "$body" | grep -o '"secret_key":"[^"]*"' | cut -d'"' -f4)
    echo ""
elif [ "$http_code" = "500" ]; then
    echo -e "${RED}✗ FAILED - Django → Rust communication broken${NC}"
    echo "This suggests the endpoint path is still incorrect"
    echo "Response: $body"
    echo ""
else
    echo -e "${YELLOW}⚠ Unexpected status code${NC}"
    echo "Response: $body"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 2: Get Shared Secret"
echo "Django: /v1/crypto/dh/get_shared_secret/"
echo "Rust:   /v1/accept_encryption_channel"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$SECRET_KEY" ] && [ -n "$PUBLIC_KEY" ]; then
    response=$(curl -X POST "$BASE_URL/crypto/dh/get_shared_secret/" \
        -H "Authorization: Token $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"private_key\":\"$SECRET_KEY\",\"public_key\":\"$PUBLIC_KEY\"}" \
        -s -w "\n%{http_code}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "Status: $http_code"
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ SUCCESS - Django → Rust communication working!${NC}"
        echo "Response: $(echo "$body" | head -c 150)..."
        
        SHARED_SECRET=$(echo "$body" | grep -o '"shared_secret":"[^"]*"' | cut -d'"' -f4)
        echo ""
    elif [ "$http_code" = "500" ]; then
        echo -e "${RED}✗ FAILED - Django → Rust communication broken${NC}"
        echo "Response: $body"
        echo ""
    else
        echo -e "${YELLOW}⚠ Unexpected status code (may be due to invalid key format)${NC}"
        echo "Response: $(echo "$body" | head -c 200)"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠ Skipping (no keys from previous test)${NC}"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 3: DH Encrypt"
echo "Django: /v1/crypto/dh/dm/encrypt_message/"
echo "Rust:   /v1/dh_encrypt"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -n "$SHARED_SECRET" ]; then
    response=$(curl -X POST "$BASE_URL/crypto/dh/dm/encrypt_message/" \
        -H "Authorization: Token $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"Hello World\",\"shared_secret\":\"$SHARED_SECRET\"}" \
        -s -w "\n%{http_code}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    echo "Status: $http_code"
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ SUCCESS - Django → Rust communication working!${NC}"
        echo "Response: $(echo "$body" | head -c 150)..."
        echo ""
    elif [ "$http_code" = "500" ]; then
        echo -e "${RED}✗ FAILED - Django → Rust communication broken${NC}"
        echo "Response: $body"
        echo ""
    else
        echo -e "${YELLOW}⚠ Unexpected status code${NC}"
        echo "Response: $(echo "$body" | head -c 200)"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠ Skipping (no shared secret from previous test)${NC}"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test 4: Whiteflag Healthcheck"
echo "Django: /v1/whiteflag/healthcheck/"
echo "Rust:   fennel-cli service connectivity"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

response=$(curl -X GET "$BASE_URL/whiteflag/healthcheck/" \
    -s -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

echo "Status: $http_code"
if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓ SUCCESS - fennel-cli service is reachable${NC}"
    echo "Response: $body"
    echo ""
elif [ "$http_code" = "500" ]; then
    echo -e "${RED}✗ FAILED - Cannot reach fennel-cli service${NC}"
    echo "Response: $body"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "If all tests show ✓ SUCCESS with 200 status codes:"
echo "  → Your endpoint path fixes are working correctly!"
echo ""
echo "If you see 500 errors:"
echo "  → Django couldn't reach Rust service, or"
echo "  → Endpoint paths may still be incorrect, or"
echo "  → Rust service rejected the request data"
echo ""
echo "If you see 400 errors:"
echo "  → Request data format is incorrect (expected for some tests)"
echo "  → But it means Django reached Rust successfully!"
echo ""
