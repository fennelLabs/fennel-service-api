#!/bin/bash

echo "🏗️  Creating Granular Taint Zones on validator2b4"
echo "==============================================="

NODE_NAME="aks-validator2b4-88375575-vmss000000"

echo "📋 Current taints:"
kubectl describe node $NODE_NAME | grep -A 2 "Taints:"

echo ""
echo "🔧 Removing broad 'dedicated' taint..."
kubectl taint nodes $NODE_NAME dedicated=validator2:NoSchedule- || echo "Taint already removed or not found"

echo ""
echo "🎯 Adding granular taints..."

# Zone 1: Blockchain workloads (validators, consensus)
kubectl taint nodes $NODE_NAME zone=blockchain:NoSchedule

# Zone 2: API workloads (fennel-service-api, related services)  
kubectl taint nodes $NODE_NAME zone=api:NoSchedule

# Zone 3: High-memory workloads (databases, caches)
kubectl taint nodes $NODE_NAME zone=database:NoSchedule

echo ""
echo "✅ New taint configuration:"
kubectl describe node $NODE_NAME | grep -A 5 "Taints:"

echo ""
echo "📋 Usage Instructions:"
echo "For blockchain pods: Add toleration for zone=blockchain"
echo "For API pods: Add toleration for zone=api" 
echo "For database pods: Add toleration for zone=database"
echo ""
echo "🎯 This allows fine-grained control while maintaining isolation!"
