#!/bin/bash
# Deploy WhiteFlag Explorer Backend

set -e

echo "🚀 Deploying WhiteFlag Explorer Backend..."
echo ""

# Configuration
ACR_NAME="fennelacr531"
IMAGE_NAME="fennel-service-api"
TAG="explorer-$(date +%Y%m%d-%H%M%S)"
NAMESPACE="fennel-api"
DEPLOYMENT_NAME="fennel-api"

# Step 1: Build Docker image
echo "Step 1: Building Docker image..."
cd /home/neurosx/DEVSPACE/fennel-deploy/fennel-service-api
docker build -t ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG} .
docker tag ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG} ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

echo "✅ Docker image built"
echo ""

# Step 2: Push to Azure Container Registry
echo "Step 2: Pushing to ACR..."
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:${TAG}
docker push ${ACR_NAME}.azurecr.io/${IMAGE_NAME}:latest

echo "✅ Pushed to ACR"
echo ""

# Step 3: Restart Kubernetes deployment
echo "Step 3: Restarting Kubernetes deployment..."
kubectl rollout restart deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE}

echo "Waiting for rollout to complete..."
kubectl rollout status deployment/${DEPLOYMENT_NAME} -n ${NAMESPACE} --timeout=5m

echo "✅ Deployment complete"
echo ""

# Step 4: Test explorer endpoints
echo "Step 4: Testing explorer endpoints..."
sleep 10  # Wait for pods to be fully ready

echo "Testing /explorer-api/stats/..."
kubectl run test-explorer --rm -i --restart=Never --image=curlimages/curl -n ${NAMESPACE} -- \
  curl -s http://fennel-api.${NAMESPACE}.svc.cluster.local:8000/explorer-api/stats/

echo ""
echo "✅ All steps complete!"
echo ""
echo "Next steps:"
echo "  1. Test externally: curl https://whiteflag.network/explorer-api/stats/"
echo "  2. Build Explorer frontend"
echo "  3. Deploy frontend to Kubernetes"
