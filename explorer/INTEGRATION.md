# Explorer App Integration Guide

## What Was Created

A new Django app `explorer/` with public, read-only API endpoints:

```
fennel-service-api/
└── explorer/                      ✨ NEW
    ├── __init__.py
    ├── apps.py
    ├── views.py                   # All explorer endpoints
    ├── urls.py                    # URL routing
    └── README.md                  # Documentation
```

## Integration Steps

### Step 1: Register the Explorer App

Add to `settings.py`:

```python
# fennelapi/settings.py

INSTALLED_APPS = [
    # ... existing apps ...
    'main',
    'explorer',  # ← ADD THIS
]
```

### Step 2: Include Explorer URLs

Add to your root `urls.py`:

```python
# fennelapi/urls.py

from django.urls import path, include

urlpatterns = [
    # ... existing URLs ...
    path('api/', include('main.urls')),  # Existing authenticated endpoints
    path('explorer-api/', include('explorer.urls')),  # ← ADD THIS (new public endpoints)
]
```

### Step 3: Test Locally

```bash
# Start Django dev server
python manage.py runserver

# Test endpoints (no auth required!)
curl http://localhost:8000/explorer-api/messages/
curl http://localhost:8000/explorer-api/stats/
curl "http://localhost:8000/explorer-api/search/?q=test"
```

### Step 4: Deploy to Kubernetes

```bash
# Rebuild Django image
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api
docker build -t fennelacr531.azurecr.io/fennel-service-api:latest .
docker push fennelacr531.azurecr.io/fennel-service-api:latest

# Restart pods to pick up new code
kubectl rollout restart deployment/whiteflag-api -n fennel-production
kubectl rollout status deployment/whiteflag-api -n fennel-production
```

### Step 5: Test in Production

```bash
# Test public endpoints
curl https://whiteflag.network/explorer-api/messages/
curl https://whiteflag.network/explorer-api/stats/
curl "https://whiteflag.network/explorer-api/search/?q=emergency"
```

## API Endpoints

### Public Explorer Endpoints (No Auth Required)
```
GET /explorer-api/messages/                      # List messages
GET /explorer-api/messages/{id}/                 # Message detail
GET /explorer-api/accounts/{username}/           # Account profile
GET /explorer-api/stats/                         # Network stats
GET /explorer-api/search/?q={query}              # Search
GET /explorer-api/reference-graph/{id}/          # Reference chain
```

### Existing Authenticated Endpoints (Unchanged)
```
POST /api/whiteflag/send_signal/                 # Send message (auth required)
GET  /api/messages/get_messages/                 # Get messages (auth required)
POST /api/crypto/dh/whiteflag/encrypt/           # Encrypt (auth required)
... all other existing endpoints
```

## Security Features

✅ **Rate Limited:** 100 requests/hour per IP
✅ **Read-Only:** Only GET methods allowed
✅ **Finalized Only:** Only shows finalized blockchain messages
✅ **No Sensitive Data:** Excludes private user information
✅ **Public Access:** No authentication required

## What's Different from Main App?

| Feature | Main App (`main/`) | Explorer App (`explorer/`) |
|---------|-------------------|---------------------------|
| **Authentication** | Required | None (public) |
| **Permissions** | `IsAuthenticated` | `AllowAny` |
| **Methods** | GET, POST, PUT, DELETE | GET only |
| **Data Access** | User's own data | All public data |
| **Rate Limiting** | Per user | Per IP address |
| **URL Prefix** | `/api/` | `/explorer-api/` |

## Next Steps

1. ✅ Explorer app created
2. ⏳ Add to `INSTALLED_APPS` in settings.py
3. ⏳ Add to root urls.py
4. ⏳ Test locally
5. ⏳ Deploy to production
6. ⏳ Build Explorer frontend to consume these APIs

## Benefits of Separate App

✅ **Clear separation** - Main app vs Explorer app
✅ **Different security** - Authenticated vs public
✅ **Independent scaling** - Can cache explorer responses
✅ **Easier testing** - Test explorer endpoints separately
✅ **Better organization** - Django best practices
