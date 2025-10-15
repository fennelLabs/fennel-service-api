# How to Run API Integration Tests Against Azure

## Prerequisites
- Admin token (required for `is_test_message` flag)
- Azure API URL

## Run the Test

```bash
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api

# Set your credentials
export API_BASE_URL='https://your-service.azurewebsites.net'
export API_TOKEN='your-admin-token-here'

# Run the integration test
./api_integration_test.sh
```

## What the Test Does

1. **Test 1**: Encodes Infrastructure (I) message as Test (T) message
2. **Test 2**: Decodes the Infrastructure Test message and verifies:
   - messageCode = "T"
   - pseudoMessageCode = "I"
3. **Test 3**: Encodes Free Text (F) message with reference as Test (T) message
4. **Test 4**: Decodes the Free Text Test message and verifies:
   - messageCode = "T"
   - pseudoMessageCode = "F"
   - referenceIndicator = "4"
   - referencedMessage is preserved

## Expected Output

If all tests pass, you'll see:

```
✓ TEST 1 PASSED: Infrastructure message encoded as Test
✓ TEST 2 PASSED: Infrastructure Test message decoded correctly
✓ TEST 3 PASSED: Free Text with reference encoded as Test
✓ TEST 4 PASSED: Free Text Test message with reference decoded correctly

=========================================
✓ ALL INTEGRATION TESTS PASSED!
=========================================
```

## Getting an Admin Token

If you don't have an admin token, you can:

1. **Via Django Admin**: Login to your Django admin panel and copy your token
2. **Via API**: If you're a superuser, your existing token should work
3. **Via Django Shell**:
   ```python
   python manage.py shell
   from knox.models import AuthToken
   from django.contrib.auth import get_user_model
   User = get_user_model()
   user = User.objects.get(username='your-admin-username')
   token = AuthToken.objects.create(user)[1]
   print(token)
   ```

## Troubleshooting

### Error: 403 Forbidden
- You need an admin token (staff or superuser)
- Check that your user has admin privileges

### Error: Connection refused
- Verify the API_BASE_URL is correct
- Ensure the API is running and accessible

### Error: Invalid token
- Check that the token is correct and not expired
- Ensure the token belongs to an admin user
