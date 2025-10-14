#!/bin/bash

# Deploy the Annotation Test Message Fix
# Version: v1.0.6-annotation-test-fix
set -e

echo "🚀 Deploying Annotation Test Message Fix"
echo "========================================="

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
NEW_VERSION="v1.0.6-annotation-test-fix"
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
echo "What was fixed:"
echo "  - I+F message pairs now BOTH convert to test messages when checkbox is checked"
echo "  - Previously: Only I message was converted, F remained as regular message"
echo "  - Now: Both I (messageCode T, pseudoMessageCode I) and F (messageCode T, pseudoMessageCode F)"
echo ""
echo "Next steps:"
echo "  1. Create a test message with annotations (I+F pair)"
echo "  2. Verify BOTH messages show as test messages in explorer"
echo "  3. Check that F message references the I message correctly"
echo ""
