#!/bin/bash

# Deploy Backend with Test F Message Support
# Version: v1.0.15-debug-encoder
set -e

echo "🚀 Deploying Backend with Test F Message Support"
echo "================================================="

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
NEW_VERSION="v1.0.15-debug-encoder"
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
print_warning "This may take several minutes..."

docker buildx build \
    --platform linux/arm64 \
    -t ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION} \
    -f Dockerfile \
    --push \
    .

if [ $? -ne 0 ]; then
    print_error "Docker build failed"
    exit 1
fi

print_success "Docker image built and pushed: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION}"

# Step 3: Update the Kubernetes deployment
print_status "Updating Kubernetes deployment..."

kubectl set image deployment/${DEPLOYMENT} \
    fennel-api=${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION} \
    -n ${NAMESPACE}

if [ $? -ne 0 ]; then
    print_error "Failed to update deployment"
    exit 1
fi

print_success "Deployment updated"

# Step 4: Wait for rollout to complete
print_status "Waiting for rollout to complete..."

kubectl rollout status deployment/${DEPLOYMENT} -n ${NAMESPACE} --timeout=300s

if [ $? -ne 0 ]; then
    print_error "Rollout failed or timed out"
    exit 1
fi

print_success "Rollout completed successfully"

# Step 5: Verify deployment
print_status "Verifying deployment..."

READY_REPLICAS=$(kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.status.readyReplicas}')
DESIRED_REPLICAS=$(kubectl get deployment ${DEPLOYMENT} -n ${NAMESPACE} -o jsonpath='{.spec.replicas}')

echo ""
echo "Deployment Status:"
echo "  Desired Replicas: $DESIRED_REPLICAS"
echo "  Ready Replicas:   $READY_REPLICAS"

if [ "$READY_REPLICAS" == "$DESIRED_REPLICAS" ]; then
    print_success "All replicas are ready!"
else
    print_warning "Not all replicas are ready yet"
fi

# Step 6: Show recent logs
print_status "Recent logs from new pod:"
kubectl logs -n ${NAMESPACE} deployment/${DEPLOYMENT} --tail=20

echo ""
print_success "Deployment completed!"
echo ""
echo "Summary:"
echo "  Version deployed: ${NEW_VERSION}"
echo "  Namespace: ${NAMESPACE}"
echo "  Deployment: ${DEPLOYMENT}"
echo ""
echo "What's New:"
echo "  ✅ Test F message conversion re-enabled"
echo "  ✅ Both I and F messages convert to test when checkbox checked"
echo "  ✅ Works correctly with fixed whiteflag-rust encoder"
echo ""
echo "Complete Test Message Flow:"
echo "  1. User checks test checkbox in whiteflag app"
echo "  2. Backend converts I message: messageCode T, pseudoMessageCode I"
echo "  3. Backend converts F message: messageCode T, pseudoMessageCode F"
echo "  4. Both messages sent to blockchain with correct structure"
echo "  5. Explorer displays both as test messages with dual badges"
echo ""
echo "Next steps:"
echo "  1. Create a test I+F message pair with annotations"
echo "  2. Verify BOTH messages show as test in explorer:"
echo "     - I message: '🧪 TEST (I)'"
echo "     - F message: '🧪 TEST (F)'"
echo "  3. Verify F message correctly references I message"
echo ""
