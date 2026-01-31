#!/bin/bash
set -e

# Configuration
GATEWAY_NAMESPACE="gateway"
GATEWAY_SERVICE="luban-gateway"
DOMAIN="harbor.k8s.orb.local"
COREDNS_NAMESPACE="kube-system"
COREDNS_CM="coredns"

echo "Checking LoadBalancer IP for ${GATEWAY_SERVICE}..."
LB_IP=$(kubectl get svc -n ${GATEWAY_NAMESPACE} ${GATEWAY_SERVICE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$LB_IP" ]; then
    echo "Error: Could not find LoadBalancer IP for ${GATEWAY_SERVICE}. Is the gateway deployed?"
    exit 1
fi

echo "Found LoadBalancer IP: ${LB_IP}"

# Check if entry already exists in CoreDNS
CURRENT_HOSTS=$(kubectl get cm ${COREDNS_CM} -n ${COREDNS_NAMESPACE} -o jsonpath='{.data.NodeHosts}')

if echo "$CURRENT_HOSTS" | grep -q "${DOMAIN}"; then
    echo "CoreDNS already has an entry for ${DOMAIN}."
    
    # Optional: Update IP if it changed (simple implementation just warns)
    EXISTING_IP=$(echo "$CURRENT_HOSTS" | grep "${DOMAIN}" | awk '{print $1}')
    if [ "$EXISTING_IP" != "$LB_IP" ]; then
        echo "WARNING: Existing entry points to ${EXISTING_IP}, but current LB IP is ${LB_IP}."
        echo "Please manually update CoreDNS or delete the entry and re-run this script."
    else
        echo "Entry is up to date."
    fi
else
    echo "Patching CoreDNS to add ${DOMAIN} -> ${LB_IP}..."
    
    # Append the new entry
    NEW_HOSTS="${CURRENT_HOSTS}
${LB_IP} ${DOMAIN}"
    
    # Apply patch
    # We use a temporary file to handle newlines correctly in the patch
    cat <<EOF > /tmp/coredns-patch.yaml
data:
  NodeHosts: |
$(echo "$NEW_HOSTS" | sed 's/^/    /')
EOF
    
    kubectl patch cm ${COREDNS_CM} -n ${COREDNS_NAMESPACE} --patch-file /tmp/coredns-patch.yaml
    rm /tmp/coredns-patch.yaml
    
    echo "Restarting CoreDNS..."
    kubectl rollout restart deployment coredns -n ${COREDNS_NAMESPACE}
    
    echo "CoreDNS patched successfully."
fi
