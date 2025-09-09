#!/bin/bash

# Pre-deployment validation for Fennel Service API
echo "🔍 Fennel Service API Pre-Deployment Validation"
echo "==============================================="

# Check 1: Verify blockchain connectivity
echo "1. Checking Fennel blockchain services..."
echo "   Validators:"
kubectl get pods -n fennel-production | grep validator | awk '{print "   " $1 ": " $3}'

echo "   Bootnodes:"
kubectl get pods -n fennel-production | grep bootnode | awk '{print "   " $1 ": " $3}'

echo "   Archive:"
kubectl get pods -n fennel-production | grep archive | awk '{print "   " $1 ": " $3}'

# Check 2: Test RPC connectivity
echo
echo "2. Testing blockchain RPC connectivity..."
if kubectl exec -n fennel-production fennel-validator-0-b4ps-v2-0 -c node -- curl -s -H "Content-Type: application/json" -d '{"id":1,"jsonrpc":"2.0","method":"system_health","params":[]}' http://localhost:9943 | grep -q "true"; then
    echo "   ✅ Validator 0 RPC is responding"
else
    echo "   ⚠️  Validator 0 RPC test failed"
fi

# Check 3: Verify internal DNS resolution
echo
echo "3. Testing internal service DNS..."
if kubectl run test-dns --image=busybox --rm -it --restart=Never -- nslookup fennel-validator-0-b4ps-v2.fennel-production.svc.cluster.local 2>/dev/null | grep -q "Address"; then
    echo "   ✅ Internal DNS resolution working"
else
    echo "   ⚠️  Internal DNS resolution issue"
fi

# Check 4: Resource availability
echo
echo "4. Checking cluster resources..."
kubectl top nodes 2>/dev/null || echo "   ⚠️  Metrics server not available"

# Check 5: Storage class
echo
echo "5. Checking storage classes..."
kubectl get storageclass | grep -E "(managed-csi|premium-rwo|default)" || echo "   ⚠️  Recommended storage classes not found"

echo
echo "✅ Validation complete!"
echo
echo "💡 Ready to deploy? Run: ./deploy-to-k8s.sh"
