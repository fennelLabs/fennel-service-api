#!/bin/bash

# Deploy A(0) Auto-Authentication Feature to Azure AKS
# Per Whiteflag spec 5.1.1: Initial authentication implementation
set -e

echo "🔐 Deploying A(0) Auto-Authentication Feature"
echo "=============================================="

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
NEW_VERSION="v1.0.16-a0-auth-arm64"
NAMESPACE="fennel-api"
DEPLOYMENT="fennel-api"

# Pre-deployment checks
print_status "Running pre-deployment checks..."

# Check if migration file exists
if [ ! -f "main/migrations/0040_whiteflagauthentication.py" ]; then
    print_error "Migration file 0040_whiteflagauthentication.py not found!"
    exit 1
fi

# Check if updated code files exist
for file in "main/models.py" "main/whiteflag_helpers.py" "main/whiteflag_views.py" "main/fennel_views.py" "main/admin.py"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found!"
        exit 1
    fi
    if ! grep -q "WhiteflagAuthentication" "$file" 2>/dev/null && [ "$file" != "main/fennel_views.py" ]; then
        print_warning "File $file may not contain WhiteflagAuthentication updates"
    fi
done

print_success "Pre-deployment checks passed"

# Step 1: Login to Azure Container Registry
print_status "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

if [ $? -ne 0 ]; then
    print_error "Failed to login to ACR"
    exit 1
fi

# Step 1: Login to Azure Container Registry
print_status "Logging into Azure Container Registry..."
az acr login --name $ACR_NAME

# Step 2: Build and push ARM64 image using buildx (following local build strategy)
print_status "Building and pushing ARM64 image with A(0) authentication..."
print_status "Using builder: arm64builder"
docker buildx build \
    --platform linux/arm64 \
    --builder arm64builder \
    --tag $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION \
    --tag $ACR_NAME.azurecr.io/$IMAGE_NAME:latest \
    --push \
    .

if [ $? -ne 0 ]; then
    print_error "Docker build and push failed"
    exit 1
fi

print_success "Docker image built and pushed successfully"

# Step 3: Apply migration in existing pod (before deploying new image)
print_status "Applying database migration 0040_whiteflagauthentication..."
POD=$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')

if [ -z "$POD" ]; then
    print_error "No running pod found in namespace $NAMESPACE"
    exit 1
fi

print_status "Running migration in pod: $POD"

kubectl exec -n $NAMESPACE $POD -- python manage.py migrate main --noinput

if [ $? -ne 0 ]; then
    print_error "Migration failed!"
    print_warning "You may need to apply the migration manually"
    echo ""
    echo "To apply manually, run:"
    echo "  kubectl exec -n $NAMESPACE $POD -- python manage.py migrate main"
    exit 1
fi

print_success "Database migration applied successfully"

# Step 5: Apply database migration
print_status "Applying database migration 0040_whiteflagauthentication..."
POD=$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')
print_status "Using pod: $POD"

# Show current migration status
print_status "Current migration status:"
kubectl exec -n $NAMESPACE $POD -- python manage.py showmigrations main | tail -5

# Step 6: Update the deployment YAML
print_status "Updating deployment YAML..."
cd k8s
cp api-deployment.yaml api-deployment.yaml.backup-pre-a0-auth
sed -i "s|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:.*|image: ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${NEW_VERSION}|g" api-deployment.yaml
cd ..

print_success "Deployment YAML updated"

# Step 7: Apply the deployment
print_status "Applying updated deployment..."
kubectl apply -f k8s/api-deployment.yaml

# Step 8: Restart the deployment to pick up new image
print_status "Restarting deployment..."
kubectl rollout restart deployment/$DEPLOYMENT -n $NAMESPACE

# Step 9: Wait for rollout to complete
print_status "Waiting for rollout to complete..."
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE --timeout=300s

if [ $? -ne 0 ]; then
    print_error "Rollout failed or timed out"
    print_warning "Check pod status with: kubectl get pods -n $NAMESPACE"
    exit 1
fi

# Step 10: Verify pods are running
print_status "Checking pod status..."
kubectl get pods -n $NAMESPACE -l app=fennel-api

# Step 11: Verify WhiteflagAuthentication model in Django
print_status "Verifying WhiteflagAuthentication model..."
sleep 5  # Give pods a moment to fully start

NEW_POD=$(kubectl get pods -n $NAMESPACE -l app=fennel-api -o jsonpath='{.items[0].metadata.name}')
print_status "Testing new pod: $NEW_POD"

kubectl exec -n $NAMESPACE $NEW_POD -- python manage.py shell -c "
from main.models import WhiteflagAuthentication
print('✅ WhiteflagAuthentication model loaded successfully')
print('Model fields:', [f.name for f in WhiteflagAuthentication._meta.get_fields()])
" || print_warning "Could not verify model in pod"

echo ""
print_success "🎉 A(0) Authentication Feature Deployed Successfully!"
echo ""
echo "📋 Deployment Summary:"
echo "  • Docker Image: $ACR_NAME.azurecr.io/$IMAGE_NAME:$NEW_VERSION"
echo "  • Migration Applied: 0038_whiteflagauthentication"
echo "  • Namespace: $NAMESPACE"
echo "  • Deployment: $DEPLOYMENT"
echo ""
echo "🧪 Testing Instructions:"
echo ""
echo "1. Test account creation WITHOUT authentication:"
echo "   curl -X POST https://fennel.network/api/v1/fennel/create_account/ \\"
echo "     -H 'Authorization: Token YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json'"
echo ""
echo "2. Test account creation WITH authentication (Method 1 - URL):"
echo "   curl -X POST https://fennel.network/api/v1/fennel/create_account/ \\"
echo "     -H 'Authorization: Token YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"auth_url\": \"https://organization.int/whiteflag\"}'"
echo ""
echo "3. Test message submission before A(0) (should return 403):"
echo "   curl -X POST https://fennel.network/api/v1/whiteflag/encode/ \\"
echo "     -H 'Authorization: Token YOUR_TOKEN' \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"messageCode\": \"F\", ...}'"
echo ""
echo "4. Verify in Django Admin:"
echo "   https://fennel.network/api/admin/main/whiteflagauthentication/"
echo ""
echo "📊 Monitoring Commands:"
echo "  • View logs: kubectl logs -n $NAMESPACE deployment/$DEPLOYMENT -f"
echo "  • Check pods: kubectl get pods -n $NAMESPACE"
echo "  • Check migration: kubectl exec -n $NAMESPACE $NEW_POD -- python manage.py showmigrations main"
echo ""
echo "📚 Full documentation:"
echo "  /fennel-deploy/DOCUMENTATION/AUTHENTICATIONOCT182025/AOmessage/Attempt1101825.md"
echo ""
