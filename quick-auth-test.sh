#!/bin/bash

# Quick A(0) Authentication Test
# Tests the authentication endpoint with a new test user

echo "🧪 Quick A(0) Authentication Test"
echo "=================================="
echo ""

# Configuration
API_URL="https://fennel.network/api/v1"
TOKEN="73fcb92b321e28dcd21dde260425f307eceb1c01c43db7f85104aec0b0348f8c"

echo "Step 1: Check current authentication status"
echo "--------------------------------------------"
curl -s "$API_URL/whiteflag/authenticate/" \
  -H "Authorization: Token $TOKEN" \
  | jq '.' || echo "Already authenticated or error"

echo ""
echo ""

echo "Step 2: Try to authenticate (will fail if already authenticated)"
echo "----------------------------------------------------------------"
curl -s -X POST "$API_URL/whiteflag/authenticate/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "verificationMethod": "1",
    "verificationData": "https://example.org/whiteflag-auth.json"
  }' | jq '.'

echo ""
echo ""

echo "Step 3: Check authentication in database"
echo "-----------------------------------------"
POD=$(kubectl get pods -n fennel-api -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n fennel-api $POD -- python manage.py shell -c "
from main.models import WhiteflagAuthentication
from django.contrib.auth.models import User

print('=== All Authentications ===')
for auth in WhiteflagAuthentication.objects.all():
    print(f'User: {auth.user.username}')
    print(f'  Method: {auth.verification_method}')
    print(f'  Data: {auth.verification_data[:50]}...')
    print(f'  Active: {auth.is_active}')
    print(f'  Created: {auth.timestamp}')
    print()
"

echo ""
echo "✅ Test complete!"
