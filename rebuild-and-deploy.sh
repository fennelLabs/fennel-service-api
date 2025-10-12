#!/bin/bash

# Rebuild and deploy the fennel-service-api with CSRF fix
set -e

echo "🔧 Rebuilding Fennel Service API with CSRF fix"
echo "================================================"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
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

# Configuration
ACR_NAME="fennelacr531"
IMAGE_NAME="fennel-service-api"
NEW_VERSION="v1.0.15-csrf-fix-arm64"
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"

# Step 1: Login to Azure Container Registry
print_status "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Build the Docker image for ARM64
print_status "Building Docker image for ARM64..."
docker build --platform linux/arm64 \
    -t $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION \
    -t $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
    .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed"
    exit 1
fi

print_success "Docker image built successfully"

# Step 3: Push to ACR
print_status "Pushing image to Azure Container Registry..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME:latest

print_success "Image pushed to ACR"

# Step 4: Update the deployment YAML
print_status "Updating deployment YAML..."
cd k8s
cp api-deployment.yaml api-deployment.yaml.backup
sed -i "s|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:.*|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION}|g" api-deployment.yaml
cd ..

print_success "Deployment YAML updated"

# Step 5: Apply the deployment
print_status "Applying updated deployment..."
kubectl apply -f k8s/api-deployment.yaml

# Step 6: Restart the deployment to pick up new image
print_status "Restarting deployment..."
kubectl rollout restart deployment/$DEPLOYMENT -n $NAMESPACE

# Step 7: Wait for rollout to complete
print_status "Waiting for rollout to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

# Step 8: Verify pods are running
print_status "Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=fennel-api

# Step 9: Test CSRF settings in new pod
print_status "Testing CSRF configuration in new pods..."
sleep 5  # Give pods a moment to fully start

POD=$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')
print_status "Testing pod: $POD"

kubectl exec -n $NAMESPACE $POD -- python manage.py shell -c "from django.conf import settings; print('CSRF_TRUSTED_ORIGINS:', settings.CSRF_TRUSTED_ORIGINS)" || true

echo ""
print_success "🎉 Deployment complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Test the admin login at: https://fennel.network/api/admin/"
echo "2. Monitor pod logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT"
echo ""
