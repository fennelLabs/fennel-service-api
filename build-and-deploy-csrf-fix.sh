#!/bin/bash

# Build and Deploy Fennel Service API with CSRF Fix
# Following the established local build strategy for ARM64

set -e

echo "🔧 Building and Deploying Fennel Service API with CSRF Fix"
echo "==========================================================="

# Colors for output
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
NEW_VERSION="v1.0.15-csrf-fix-arm64"
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"
BUILDER="arm64builder"

print_status "Using builder: $BUILDER"
print_status "Target platform: linux/arm64"
print_status "Image version: $NEW_VERSION"

# Step 1: Verify we're in the right directory
if [ ! -f "Dockerfile" ]; then
    print_error "Dockerfile not found. Please run this script from the fennel-service-api directory."
    exit 1
fi

if [ ! -f "fennel/settings.py" ]; then
    print_error "settings.py not found. Are you in the correct directory?"
    exit 1
fi

print_success "Directory verified"

# Step 2: Login to Azure Container Registry
print_status "Logging into Azure Container Registry..."
if az acr login --name $ACR_NAME; then
    print_success "Azure ACR authentication successful"
else
    print_error "Azure ACR authentication failed"
    exit 1
fi

# Step 3: Verify Docker buildx builder
print_status "Checking Docker buildx builder..."
if docker buildx inspect $BUILDER > /dev/null 2>&1; then
    print_success "Builder '$BUILDER' is available"
else
    print_error "Builder '$BUILDER' not found. Available builders:"
    docker buildx ls
    exit 1
fi

# Step 4: Build the Docker image for ARM64
print_status "Building Docker image for ARM64..."
print_warning "This may take several minutes on first build..."

if docker buildx build \
    --platform linux/arm64 \
    --builder $BUILDER \
    --tag $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION \
    --tag $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
    --push \
    .; then
    print_success "Docker image built and pushed successfully"
else
    print_error "Docker build failed"
    exit 1
fi

# Step 5: Verify the image was pushed
print_status "Verifying image in registry..."
if az acr repository show --name $ACR_NAME --image $IMAGE_NAME:$NEW_VERSION > /dev/null 2>&1; then
    print_success "Image verified in Azure Container Registry"
else
    print_warning "Could not verify image in registry (may still be processing)"
fi

# Step 6: Update the deployment
print_status "Updating Kubernetes deployment..."

# Check if we should update the deployment YAML
if [ -f "k8s/api-deployment.yaml" ]; then
    print_status "Backing up current deployment YAML..."
    cp k8s/api-deployment.yaml k8s/api-deployment.yaml.backup
    
    print_status "Updating deployment YAML with new image version..."
    sed -i "s|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:.*|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION}|g" k8s/api-deployment.yaml
    
    print_status "Applying updated deployment..."
    kubectl apply -f k8s/api-deployment.yaml
else
    print_warning "Deployment YAML not found, will use kubectl set image instead"
    kubectl set image deployment/$DEPLOYMENT -n $NAMESPACE \
        fennel-api=$ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION
fi

# Step 7: Restart the deployment
print_status "Restarting deployment to pick up new image..."
kubectl rollout restart deployment/$DEPLOYMENT -n $NAMESPACE

# Step 8: Wait for rollout to complete
print_status "Waiting for rollout to complete (timeout: 300s)..."
if kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s; then
    print_success "Deployment rollout completed"
else
    print_error "Deployment rollout failed or timed out"
    print_status "Checking pod status..."
    kubectl get pods -n $NAMESPACE -l app=fennel-api
    exit 1
fi

# Step 9: Verify pods are running
print_status "Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=fennel-api

# Step 10: Test CSRF configuration in new pods
print_status "Waiting for pods to fully start..."
sleep 10

POD=$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')
if [ -n "$POD" ]; then
    print_status "Testing CSRF configuration in pod: $POD"
    
    print_status "Environment variable check:"
    kubectl exec -n $NAMESPACE $POD -- printenv CSRF_TRUSTED_ORIGINS | head -c 200
    echo "..."
    
    print_status "Django settings check:"
    kubectl exec -n $NAMESPACE $POD -- python manage.py shell -c "from django.conf import settings; import json; print(json.dumps(settings.CSRF_TRUSTED_ORIGINS, indent=2))" 2>/dev/null || print_warning "Could not check Django settings (pod may still be starting)"
else
    print_warning "Could not find pod for testing"
fi

echo ""
print_success "🎉 Deployment Complete!"
echo ""
echo "📋 Summary:"
echo "  - Image: $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION"
echo "  - Namespace: $NAMESPACE"
echo "  - Deployment: $DEPLOYMENT"
echo ""
echo "🧪 Next Steps:"
echo "  1. Test admin login at: https://fennel.network/api/admin/"
echo "  2. Login credentials: admin / Fennel-Admin"
echo "  3. Verify CSRF error is resolved"
echo ""
echo "🔍 Useful Commands:"
echo "  • View logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT --tail=50"
echo "  • Check pods: kubectl get pods -n $NAMESPACE -l app=fennel-api"
echo "  • Describe pod: kubectl describe pod -n $NAMESPACE $POD"
echo ""
