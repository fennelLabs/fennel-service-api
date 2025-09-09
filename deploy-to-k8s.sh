#!/bin/bash

# Fennel Service API Deployment Script for Azure Kubernetes
# This script deploys the Fennel API service to connect with your existing blockchain

set -e

echo "🚀 Deploying Fennel Service API to Azure Kubernetes"
echo "================================================="
echo

# Check if kubectl is available and configured
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed or not in PATH"
    exit 1
fi

# Check cluster connection
echo "🔍 Checking Kubernetes cluster connection..."
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
fi

# Verify Fennel blockchain is running
echo "🔍 Verifying Fennel blockchain components..."
if ! kubectl get pods -n fennel-production | grep -q "Running"; then
    echo "❌ Fennel blockchain pods are not running in fennel-production namespace"
    echo "Please ensure your blockchain deployment is healthy before deploying the API"
    exit 1
fi

echo "✅ Fennel blockchain is running"

# Apply Kubernetes manifests
echo "📦 Deploying Fennel API components..."

echo "  → Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "  → Creating configuration and secrets..."
kubectl apply -f k8s/configmap.yaml

echo "  → Deploying PostgreSQL database..."
kubectl apply -f k8s/postgres.yaml

echo "  → Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n fennel-api --timeout=300s

echo "  → Deploying Fennel API service..."
kubectl apply -f k8s/api-deployment.yaml

echo "  → Waiting for API deployment to be ready..."
kubectl wait --for=condition=available deployment/fennel-api -n fennel-api --timeout=600s

echo "  → Creating ingress (optional)..."
kubectl apply -f k8s/ingress.yaml

echo
echo "🎉 Fennel Service API deployed successfully!"
echo
echo "📋 Deployment Summary:"
echo "======================"
echo "✅ Namespace: fennel-api"
echo "✅ PostgreSQL Database: Running with persistent storage"
echo "✅ API Service: 2 replicas with load balancer"
echo "✅ Connected to blockchain: fennel-production namespace"
echo

# Get service information
echo "🌐 Service Endpoints:"
echo "===================="
kubectl get services -n fennel-api

echo
echo "📊 Pod Status:"
echo "=============="
kubectl get pods -n fennel-api

echo
echo "🔗 Getting LoadBalancer IP (may take a few minutes)..."
kubectl get service fennel-api-loadbalancer -n fennel-api -w --timeout=300s &
LB_PID=$!

echo
echo "💡 Next Steps:"
echo "=============="
echo "1. Wait for LoadBalancer IP to be assigned"
echo "2. Update DNS records to point api.fennellabs.com to the LoadBalancer IP"
echo "3. Test API endpoints:"
echo "   - Health check: curl http://[LOADBALANCER-IP]:1234/admin/"
echo "   - API docs: http://[LOADBALANCER-IP]:1234/docs/"
echo
echo "4. Monitor logs:"
echo "   kubectl logs -f deployment/fennel-api -n fennel-api"
echo
echo "5. Monitor blockchain connectivity:"
echo "   kubectl logs -f deployment/fennel-api -n fennel-api | grep -i 'blockchain\\|rpc\\|connection'"

# Kill the background watch process
sleep 10
kill $LB_PID 2>/dev/null || true

echo
echo "✅ Deployment completed successfully!"
