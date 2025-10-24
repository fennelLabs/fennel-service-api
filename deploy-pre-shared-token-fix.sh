#!/bin/bash

# Deploy Pre-Shared Token Authentication Fix
# Fixes: Full 32-byte token in A2(0) verification data (not truncated)
# Date: October 24, 2025
# Version: v1.0.23-auth-spec-fix-arm64

set -e

echo "======================================"
echo "Pre-Shared Token Authentication Fix"
echo "======================================"
echo ""
echo "Changes:"
echo "  - Fixed verification data: Full 32-byte token (64 hex chars)"
echo "  - Previously: Only 12 bytes (24 hex chars) ❌"
echo "  - Now: Full 32 bytes per Whiteflag spec ✅"
echo ""
echo "Backend commit: 4686f0a"
echo "Frontend commit: b2e5110"
echo ""

# Configuration
IMAGE_NAME="fennel-service-api"
TAG="v1.0.23-auth-spec-fix-arm64"
REGISTRY="fennelacr531.azurecr.io"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"

echo "Step 1: Building Docker image for ARM64..."
echo "Image: ${FULL_IMAGE}"
echo ""

docker buildx build \
  --platform linux/arm64 \
  -t "${FULL_IMAGE}" \
  --load \
  .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed!"
    exit 1
fi

echo ""
echo "✅ Docker build successful!"
echo ""
echo "Step 2: Logging into Azure Container Registry..."
az acr login --name fennelacr531

if [ $? -ne 0 ]; then
    echo "❌ ACR login failed!"
    exit 1
fi

echo ""
echo "✅ ACR login successful!"
echo ""
echo "Step 3: Pushing image to ACR..."

docker push "${FULL_IMAGE}"

if [ $? -ne 0 ]; then
    echo "❌ Docker push failed!"
    exit 1
fi

echo ""
echo "✅ Image pushed successfully!"
echo ""
echo "Step 4: Updating Kubernetes deployment..."

kubectl set image deployment/${DEPLOYMENT} \
  ${IMAGE_NAME}=${FULL_IMAGE} \
  -n ${NAMESPACE}

if [ $? -ne 0 ]; then
    echo "❌ Kubernetes deployment update failed!"
    exit 1
fi

echo ""
echo "✅ Deployment updated!"
echo ""
echo "Step 5: Monitoring rollout..."

kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=5m

if [ $? -ne 0 ]; then
    echo "❌ Rollout failed or timed out!"
    echo ""
    echo "Check pod status:"
    kubectl get pods -n ${NAMESPACE}
    echo ""
    echo "Check logs:"
    kubectl logs -l app=${IMAGE_NAME} -n ${NAMESPACE} --tail=50
    exit 1
fi

echo ""
echo "✅ Rollout complete!"
echo ""
echo "Step 6: Verifying deployment..."

echo ""
echo "Pods:"
kubectl get pods -n ${NAMESPACE} -l app=${IMAGE_NAME}

echo ""
echo "Deployment:"
kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE}

echo ""
echo "Service:"
kubectl get svc fennel-api-service -n ${NAMESPACE}

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Next Steps:"
echo "1. Test token generation:"
echo "   curl https://api.fennel.network/api/v1/whiteflag/generate_shared_token/"
echo ""
echo "2. Test authentication (with valid token):"
echo "   curl -X POST https://api.fennel.network/api/v1/whiteflag/authenticate_with_shared_token/ \\"
echo "     -H \"Authorization: Token YOUR_AUTH_TOKEN\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"sharedToken\": \"YOUR_UUID_TOKEN\"}'"
echo ""
echo "3. Verify A2(0) message on blockchain:"
echo "   - Check transaction hash"
echo "   - Verify VerificationData is 64 hex characters (32 bytes)"
echo ""
echo "4. Check logs for any errors:"
echo "   kubectl logs -f deployment/${DEPLOYMENT} -n ${NAMESPACE}"
echo ""
echo "Documentation:"
echo "  /home/neurosx/DEVSPACE/fennel-deploy/DOCUMENTATION/AUTHENTICATIONOCT182025/METHOD2ATTEMPT3/PRE_SHARED_TOKEN_IMPLEMENTATION.md"
echo ""
