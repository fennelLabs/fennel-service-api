# WhiteFlag Explorer App

This Django app provides public, read-only API endpoints for exploring WhiteFlag messages.

## Endpoints

All endpoints are public (no authentication required) and rate-limited to 100 requests/hour per IP.

### Messages
- `GET /explorer-api/messages/` - List all finalized messages
- `GET /explorer-api/messages/{id}/` - Get message details
- `GET /explorer-api/search/?q={query}` - Search messages

### Accounts
- `GET /explorer-api/accounts/{username}/` - Get public account profile

### Statistics
- `GET /explorer-api/stats/` - Get network statistics

### Reference Graph
- `GET /explorer-api/reference-graph/{id}/` - Get message reference chain

## Security

- All endpoints use `@permission_classes([AllowAny])` - no authentication required
- Rate limited to 100 requests/hour per IP address
- Only returns finalized messages (no pending transactions)
- Excludes sensitive user data

## Usage

These endpoints are designed to be consumed by the WhiteFlag Explorer frontend at `https://whiteflag.network/explorer`
