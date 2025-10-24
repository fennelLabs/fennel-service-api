#!/bin/bash
# Test Script: K(0)0A Blockchain Submission Fix
# Tests the complete ECDH Method 2 authentication flow
# Version: v1.0.21-k0a-blockchain-fix-arm64

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="${API_BASE_URL:-https://api.whiteflag.network}"
TIMO_API_URL="https://api.whiteflagprotocol.net"
USERNAME="${TEST_USERNAME}"
PASSWORD="${TEST_PASSWORD}"

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_requirements() {
    print_header "Checking Requirements"
    
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        exit 1
    fi
    print_success "curl is installed"
    
    if ! command -v jq &> /dev/null; then
        print_error "jq is not installed (required for JSON parsing)"
        echo "Install with: sudo apt-get install jq"
        exit 1
    fi
    print_success "jq is installed"
    
    if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ]; then
        print_error "Username or password not set"
        echo "Export TEST_USERNAME and TEST_PASSWORD environment variables"
        exit 1
    fi
    print_success "Credentials configured"
}

get_auth_token() {
    print_header "Step 0: Authenticating User"
    
    local response=$(curl -s -X POST "${API_BASE_URL}/api/v1/auth/login/" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${USERNAME}\",\"password\":\"${PASSWORD}\"}")
    
    TOKEN=$(echo "$response" | jq -r '.token // .auth_token // empty')
    
    if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
        print_error "Failed to get authentication token"
        echo "Response: $response"
        exit 1
    fi
    
    print_success "Authentication token obtained"
    print_info "Token: ${TOKEN:0:20}..."
}

test_step1_generate_keypair() {
    print_header "Step 1: Generate ECDH Keypair"
    
    local response=$(curl -s -X POST "${API_BASE_URL}/api/v1/ecdh/generate_keypair/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Token ${TOKEN}")
    
    echo "$response" | jq '.' || echo "$response"
    
    local success=$(echo "$response" | jq -r '.success // empty')
    PRIVATE_KEY=$(echo "$response" | jq -r '.private_key // empty')
    PUBLIC_KEY=$(echo "$response" | jq -r '.public_key // empty')
    
    if [ "$success" == "true" ] && [ -n "$PUBLIC_KEY" ] && [ -n "$PRIVATE_KEY" ]; then
        print_success "ECDH keypair generated successfully"
        print_info "Public Key: ${PUBLIC_KEY}"
        
        # Validate key length
        if [ ${#PUBLIC_KEY} -eq 64 ]; then
            print_success "Public key has correct length (64 hex chars = 32 bytes)"
        else
            print_error "Public key has incorrect length: ${#PUBLIC_KEY} (expected 64)"
            exit 1
        fi
    else
        print_error "Failed to generate ECDH keypair"
        exit 1
    fi
}

test_step2_publish_key() {
    print_header "Step 2: Publish K(0)0A Message to Blockchain"
    
    print_info "This is the CRITICAL FIX - K(0)0A should now be submitted to blockchain"
    
    local response=$(curl -s -X POST "${API_BASE_URL}/api/v1/whiteflag/publish_ecdh_key/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Token ${TOKEN}" \
        -d "{\"public_key\":\"${PUBLIC_KEY}\"}")
    
    echo "$response" | jq '.' || echo "$response"
    
    local success=$(echo "$response" | jq -r '.success // empty')
    K0A_TX_HASH=$(echo "$response" | jq -r '.transaction_hash // empty')
    K0A_BLOCK_NUMBER=$(echo "$response" | jq -r '.block_number // empty')
    K0A_ENCODED=$(echo "$response" | jq -r '.encoded_message // empty')
    
    if [ "$success" == "true" ]; then
        print_success "K(0)0A message published successfully"
        
        if [ -n "$K0A_TX_HASH" ] && [ "$K0A_TX_HASH" != "null" ]; then
            print_success "Transaction hash returned: ${K0A_TX_HASH:0:20}..."
            print_success "Block number: ${K0A_BLOCK_NUMBER}"
            print_info "Encoded message: ${K0A_ENCODED:0:60}..."
        else
            print_error "⚠️  No transaction hash returned - message may not be on blockchain!"
            print_error "This indicates the OLD BUG is still present"
            exit 1
        fi
    else
        print_error "Failed to publish K(0)0A message"
        exit 1
    fi
    
    # Wait for blockchain confirmation
    print_info "Waiting 10 seconds for blockchain confirmation..."
    sleep 10
}

test_step3_authenticate() {
    print_header "Step 3: Submit A(0) Authentication"
    
    local response=$(curl -s -X POST "${API_BASE_URL}/api/v1/whiteflag/self_authenticate/" \
        -H "Content-Type: application/json" \
        -H "Authorization: Token ${TOKEN}" \
        -d "{\"organization_name\":\"Test Org\"}")
    
    echo "$response" | jq '.' || echo "$response"
    
    local success=$(echo "$response" | jq -r '.success // empty')
    A0_TX_HASH=$(echo "$response" | jq -r '.transaction_hash // empty')
    A0_BLOCK_NUMBER=$(echo "$response" | jq -r '.block_number // empty')
    
    if [ "$success" == "true" ] && [ -n "$A0_TX_HASH" ]; then
        print_success "A(0) authentication submitted successfully"
        print_success "Transaction hash: ${A0_TX_HASH:0:20}..."
        print_success "Block number: ${A0_BLOCK_NUMBER}"
    else
        print_error "Failed to submit A(0) authentication"
        exit 1
    fi
    
    # Wait for blockchain confirmation
    print_info "Waiting 10 seconds for blockchain confirmation..."
    sleep 10
}

verify_with_timo_api() {
    print_header "Step 4: Verify with Timo API (Whiteflag Reference Implementation)"
    
    print_info "Note: Timo API requires authentication credentials"
    print_info "You may need to configure TIMO_USERNAME and TIMO_PASSWORD"
    
    if [ -z "$TIMO_USERNAME" ] || [ -z "$TIMO_PASSWORD" ]; then
        print_info "Skipping Timo API verification (credentials not configured)"
        return
    fi
    
    # Get user's originator address
    local user_response=$(curl -s -X GET "${API_BASE_URL}/api/v1/user/keys/" \
        -H "Authorization: Token ${TOKEN}")
    
    ORIGINATOR_ADDRESS=$(echo "$user_response" | jq -r '.address // empty')
    
    if [ -z "$ORIGINATOR_ADDRESS" ]; then
        print_error "Could not get originator address"
        return
    fi
    
    print_info "Originator Address: ${ORIGINATOR_ADDRESS}"
    
    # Query Timo API for K(0)0A messages
    print_info "Checking for K(0)0A message..."
    local k0a_response=$(curl -s -u "${TIMO_USERNAME}:${TIMO_PASSWORD}" \
        "${TIMO_API_URL}/messages?originatorAddress=${ORIGINATOR_ADDRESS}&messageCode=K")
    
    local k0a_count=$(echo "$k0a_response" | jq 'length // 0')
    
    if [ "$k0a_count" -gt 0 ]; then
        print_success "Found ${k0a_count} K message(s) from originator"
        echo "$k0a_response" | jq '.[0] | {transactionHash, blockNumber, messageCode, cryptoDataType}'
    else
        print_error "No K(0)0A messages found in Timo API"
        print_error "This indicates the message was not submitted to blockchain"
    fi
    
    # Query Timo API for A(0) messages
    print_info "Checking for A(0) message..."
    local a0_response=$(curl -s -u "${TIMO_USERNAME}:${TIMO_PASSWORD}" \
        "${TIMO_API_URL}/messages?originatorAddress=${ORIGINATOR_ADDRESS}&messageCode=A")
    
    local a0_count=$(echo "$a0_response" | jq 'length // 0')
    
    if [ "$a0_count" -gt 0 ]; then
        print_success "Found ${a0_count} A message(s) from originator"
        echo "$a0_response" | jq '.[0] | {transactionHash, blockNumber, messageCode, verificationMethod}'
    else
        print_error "No A(0) messages found in Timo API"
    fi
    
    # Check Timo API logs for verification errors
    print_info "Check Timo API logs for: 'Unknown originator authentication token'"
    print_info "If this error appears, the K(0)0A message is missing from blockchain"
}

verify_blockchain_explorer() {
    print_header "Step 5: Verify on Blockchain Explorer"
    
    print_info "You can manually verify the messages on the blockchain:"
    echo ""
    echo "K(0)0A Message:"
    echo "  Transaction Hash: ${K0A_TX_HASH}"
    echo "  Block Number: ${K0A_BLOCK_NUMBER}"
    echo ""
    echo "A(0) Message:"
    echo "  Transaction Hash: ${A0_TX_HASH}"
    echo "  Block Number: ${A0_BLOCK_NUMBER}"
    echo ""
    print_info "Query blockchain scanner:"
    echo "  curl \"https://api.whiteflagprotocol.net/blockchains/fennel-solonet/scan?from=${K0A_BLOCK_NUMBER}&to=${A0_BLOCK_NUMBER}\""
}

summary() {
    print_header "Test Summary"
    
    echo "Test Results:"
    echo "  Step 1 - Generate Keypair: ${GREEN}✓ PASS${NC}"
    echo "  Step 2 - Publish K(0)0A:   ${GREEN}✓ PASS (TX: ${K0A_TX_HASH:0:12}...)${NC}"
    echo "  Step 3 - Submit A(0):      ${GREEN}✓ PASS (TX: ${A0_TX_HASH:0:12}...)${NC}"
    echo ""
    echo "Critical Fix Verification:"
    if [ -n "$K0A_TX_HASH" ] && [ "$K0A_TX_HASH" != "null" ]; then
        echo -e "  ${GREEN}✓ K(0)0A message HAS transaction hash${NC}"
        echo -e "  ${GREEN}✓ K(0)0A message WAS submitted to blockchain${NC}"
        echo -e "  ${GREEN}✓ Bug fix is WORKING correctly${NC}"
    else
        echo -e "  ${RED}✗ K(0)0A message MISSING transaction hash${NC}"
        echo -e "  ${RED}✗ Bug is STILL present${NC}"
    fi
    echo ""
    echo "Next Steps:"
    echo "  1. Verify messages appear in Timo API"
    echo "  2. Check for 'Unknown originator authentication token' errors"
    echo "  3. Test with frontend authentication wizard"
}

# Main execution
main() {
    print_header "ECDH Method 2 Authentication - Complete Flow Test"
    echo "Testing backend fix: K(0)0A blockchain submission"
    echo "Target: ${API_BASE_URL}"
    echo ""
    
    check_requirements
    get_auth_token
    test_step1_generate_keypair
    test_step2_publish_key
    test_step3_authenticate
    verify_with_timo_api
    verify_blockchain_explorer
    summary
    
    print_success "All tests completed successfully!"
}

# Run main function
main
