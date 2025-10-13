#!/bin/bash
# Quick rebuild and deploy with explorer endpoints

set -e

echo "🔨 Rebuilding Django API with Explorer endpoints..."
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api

# Build fresh image
docker build --no-cache -t fennelacr531.azurecr.io/fennel-service-api:latest .

echo "📤 Pushing to ACR..."
docker push fennelacr531.azurecr.io/fennel-service-api:latest

echo "🔄 Restarting deployment..."
kubectl rollout restart deployment/fennel-api -n fennel-api
kubectl rollout status deployment/fennel-api -n fennel-api --timeout=5m

echo "✅ Deployment complete!"
echo ""
echo "Test with:"
echo "  curl https://whiteflag.network/explorer-api/stats/"
