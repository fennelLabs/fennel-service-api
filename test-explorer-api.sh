#!/bin/bash
# Test WhiteFlag Explorer API endpoints

echo "🔍 Testing WhiteFlag Explorer API Endpoints..."
echo ""

API_BASE="${1:-http://localhost:8000}"

echo "Testing against: $API_BASE"
echo "=================================="
echo ""

# Test 1: List messages
echo "1️⃣ Testing GET /explorer-api/messages/"
curl -s "$API_BASE/explorer-api/messages/" | python3 -m json.tool | head -n 20
echo ""
echo "---"
echo ""

# Test 2: Network stats
echo "2️⃣ Testing GET /explorer-api/stats/"
curl -s "$API_BASE/explorer-api/stats/" | python3 -m json.tool
echo ""
echo "---"
echo ""

# Test 3: Search
echo "3️⃣ Testing GET /explorer-api/search/?q=test"
curl -s "$API_BASE/explorer-api/search/?q=test" | python3 -m json.tool | head -n 20
echo ""
echo "---"
echo ""

echo "✅ Basic tests complete!"
echo ""
echo "To test specific endpoints:"
echo "  - Message detail: curl $API_BASE/explorer-api/messages/1/"
echo "  - Account profile: curl $API_BASE/explorer-api/accounts/username/"
echo "  - Reference graph: curl $API_BASE/explorer-api/reference-graph/1/"
