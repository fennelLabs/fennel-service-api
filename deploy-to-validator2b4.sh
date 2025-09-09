#!/bin/bash

echo "🚀 Deploying Fennel Service API to validator2b4 node"
echo "=================================================="

# Build Docker image
echo "📦 Building Docker image..."
docker build -t fennel-service-api:latest .

# Tag for local registry (if using kind/minikube) or push to registry
echo "🏷️  Tagging image..."
docker tag fennel-service-api:latest localhost:5000/fennel-service-api:latest 2>/dev/null || echo "No local registry, using local image"

# Deploy to Kubernetes
echo "☸️  Deploying to Kubernetes..."

# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create ConfigMap and Secrets
kubectl apply -f k8s/configmap.yaml

# Deploy PostgreSQL
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f k8s/postgres.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n fennel-api --timeout=300s

# Deploy API
echo "🌐 Deploying Fennel API..."
kubectl apply -f k8s/api-deployment-simple.yaml

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
kubectl wait --for=condition=ready pod -l app=fennel-api -n fennel-api --timeout=600s

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Check deployment status:"
echo "  kubectl get pods -n fennel-api -o wide"
echo ""
echo "🔍 Check logs:"
echo "  kubectl logs -n fennel-api -l app=fennel-api -f"
echo ""
echo "🌐 Get LoadBalancer IP:"
echo "  kubectl get service fennel-api-loadbalancer -n fennel-api"
echo ""
echo "🧪 Test API (once LoadBalancer IP is ready):"
echo "  curl http://<EXTERNAL-IP>:1234/admin/"
