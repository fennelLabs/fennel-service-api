#!/bin/bash

# Deploy the Test Message Checkbox Feature
# Version: v1.0.3-test-checkbox
set -e

echo "🚀 Deploying Test Message Checkbox Feature"
echo "==========================================="

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
ACR_NAME="fennelacr531"
IMAGE_NAME="fennel-service-api"
NEW_VERSION="v1.0.3-test-checkbox"
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"

# Step 1: Login to Azure Container Registry
print_status "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

if [ $? -ne 0 ]; then
    print_error "Failed to login to ACR"
    exit 1
fi

print_success "Logged into ACR"

# Step 2: Build the Docker image for ARM64
print_status "Building Docker image for ARM64..."
print_status "Image: $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION"

docker build --platform linux/arm64 \
    -t $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION \
    -t $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
    .

if [ $? -ne 0 ]; then
    print_error "Docker build failed"
    exit 1
fi

print_success "Docker image built successfully"

# Step 3: Push to Azure Container Registry
print_status "Pushing image to ACR..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION

if [ $? -ne 0 ]; then
    print_error "Failed to push versioned image"
    exit 1
fi

print_success "Pushed $NEW_VERSION"

print_status "Pushing latest tag..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:latest

if [ $? -ne 0 ]; then
    print_error "Failed to push latest tag"
    exit 1
fi

print_success "Pushed latest tag"

# Step 4: Update Kubernetes deployment
print_status "Updating Kubernetes deployment..."
kubectl set image deployment/$DEPLOYMENT \
    fennel-api=$ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION \
    -n $NAMESPACE

if [ $? -ne 0 ]; then
    print_error "Failed to update deployment"
    exit 1
fi

print_success "Deployment updated"

# Step 5: Wait for rollout
print_status "Waiting for rollout to complete (timeout: 5 minutes)..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=5m

if [ $? -ne 0 ]; then
    print_error "Rollout failed or timed out"
    print_warning "Check pod status with: kubectl get pods -n $NAMESPACE"
    print_warning "Check logs with: kubectl logs -n $NAMESPACE -l app=fennel-api --tail=50"
    exit 1
fi

print_success "Rollout completed successfully"

# Step 6: Verify deployment
print_status "Verifying deployment..."
REPLICAS=$(kubectl get deployment/$DEPLOYMENT -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
DESIRED=$(kubectl get deployment/$DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.replicas}')

echo ""
print_status "Ready replicas: $REPLICAS/$DESIRED"

if [ "$REPLICAS" == "$DESIRED" ]; then
    print_success "All replicas are ready"
else
    print_warning "Not all replicas are ready yet"
fi

# Step 7: Show deployment info
echo ""
echo "================================================"
print_success "Deployment Complete!"
echo "================================================"
echo ""
echo "📦 Version: $NEW_VERSION"
echo "🌐 API URL: https://whiteflag.network/api/v1/"
echo "📊 Namespace: $NAMESPACE"
echo "🔄 Replicas: $REPLICAS/$DESIRED"
echo ""
echo "✨ New Feature: Test Message Checkbox"
echo "   - Add 'is_test_message: true' to API requests"
echo "   - Converts any message to Test (T) type"
echo "   - Sets pseudoMessageCode to original messageCode"
echo ""
echo "📝 Endpoints supporting test checkbox:"
echo "   - POST /api/v1/encode_and_send_signal/"
echo "   - POST /api/v1/get_fee_for_send_signal_with_annotations/"
echo "   - POST /api/v1/send_signal_with_annotations/"
echo ""
echo "🧪 Test with:"
echo '   curl -X POST https://whiteflag.network/api/v1/encode_and_send_signal/ \'
echo '     -H "Content-Type: application/json" \'
echo '     -H "Authorization: Bearer YOUR_TOKEN" \'
echo '     -d '"'"'{"signal_body": {"messageCode": "F", "text": "Test message"}, "is_test_message": true}'"'"
echo ""
echo "📊 Monitor pods:"
echo "   kubectl get pods -n $NAMESPACE -l app=fennel-api"
echo ""
echo "📋 View logs:"
echo "   kubectl logs -n $NAMESPACE -l app=fennel-api --tail=50 -f"
echo ""
