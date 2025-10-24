#!/bin/bash

# Generate Knox token for a new user
# Usage: ./get-user-token.sh <username>

if [ -z "$1" ]; then
    echo "Usage: ./get-user-token.sh <username>"
    echo "Example: ./get-user-token.sh testorg2025"
    exit 1
fi

USERNAME=$1

echo "🔑 Generating Knox token for user: $USERNAME"
echo "=============================================="
echo ""

POD=$(kubectl get pods -n fennel-api -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')

kubectl exec -n fennel-api $POD -- python manage.py shell -c "
from django.contrib.auth.models import User
from knox.models import AuthToken

try:
    user = User.objects.get(username='$USERNAME')
    instance, token = AuthToken.objects.create(user=user)
    print(f'✅ Token generated for: {user.username}')
    print(f'')
    print(f'Token: {token}')
    print(f'')
    print(f'Use this in API calls:')
    print(f'Authorization: Token {token}')
except User.DoesNotExist:
    print(f'❌ User \"{USERNAME}\" not found')
    print(f'')
    print('Available users:')
    for u in User.objects.all()[:10]:
        print(f'  - {u.username}')
"
