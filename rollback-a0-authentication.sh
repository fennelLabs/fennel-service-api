#!/bin/bash

# Rollback A(0) Auto-Authentication Feature
# Use this script if the deployment causes issues
set -e

echo "⚠️  Rolling Back A(0) Auto-Authentication Feature"
echo "=================================================="

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
PREVIOUS_VERSION="v1.0.15-csrf-fix-arm64"  # Update this to your previous version
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"

print_warning "This will rollback to version: $PREVIOUS_VERSION"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    print_status "Rollback cancelled"
    exit 0
fi

# Option 1: Rollback to previous image (keeps migration)
print_status "Rolling back to previous image version..."

cd k8s
if [ -f "api-deployment.yaml.backup-pre-a0-auth" ]; then
    print_status "Restoring previous deployment YAML..."
    cp api-deployment.yaml.backup-pre-a0-auth api-deployment.yaml
else
    print_status "Updating deployment YAML to previous version..."
    sed -i "s|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:.*|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${PREVIOUS_VERSION}|g" api-deployment.yaml
fi
cd ..

# Apply the rollback
print_status "Applying rollback deployment..."
kubectl apply -f k8s/api-deployment.yaml

# Restart the deployment
print_status "Restarting deployment..."
kubectl rollout restart deployment/$DEPLOYMENT -n $NAMESPACE

# Wait for rollout to complete
print_status "Waiting for rollout to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

print_success "Rollback to previous image complete"

echo ""
print_warning "⚠️  Note: The database migration (0038_whiteflagauthentication) is still applied."
print_warning "The WhiteflagAuthentication table still exists but the code won't use it."
echo ""
echo "If you need to fully rollback including the migration, run:"
echo ""
echo "  POD=\$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')"
echo "  kubectl exec -n $NAMESPACE \$POD -- python manage.py migrate main 0037"
echo ""
print_warning "⚠️  WARNING: Rolling back the migration will delete all WhiteflagAuthentication records!"
echo ""

# Verify pods are running
print_status "Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=fennel-api

echo ""
print_success "🔄 Rollback Complete"
echo ""
echo "📊 Monitoring Commands:"
echo "  • View logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT -f"
echo "  • Check pods: kubectl get pods -n $NAMESPACE"
echo ""
