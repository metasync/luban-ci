#!/bin/bash
set -e

# Configuration
GATEWAY_NAMESPACE="gateway"
GATEWAY_SERVICE="luban-gateway"
DOMAINS=(
    "harbor.luban.metasync.cc"
    "argocd.luban.metasync.cc"
    "argo-workflows.luban.metasync.cc"
    "webhook.luban.metasync.cc"
)
COREDNS_NAMESPACE="kube-system"
COREDNS_CM="coredns"

echo "Checking LoadBalancer IP for ${GATEWAY_SERVICE}..."
LB_IP=$(kubectl get svc -n ${GATEWAY_NAMESPACE} ${GATEWAY_SERVICE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

if [ -z "$LB_IP" ]; then
    echo "Error: Could not find LoadBalancer IP for ${GATEWAY_SERVICE}. Is the gateway deployed?"
    exit 1
fi

echo "Found LoadBalancer IP: ${LB_IP}"

# Check current config
CURRENT_HOSTS=$(kubectl get cm ${COREDNS_CM} -n ${COREDNS_NAMESPACE} -o jsonpath='{.data.NodeHosts}')
NEW_HOSTS="$CURRENT_HOSTS"
UPDATED=false

for DOMAIN in "${DOMAINS[@]}"; do
    if echo "$CURRENT_HOSTS" | grep -q "${DOMAIN}"; then
        echo "CoreDNS already has an entry for ${DOMAIN}."
    else
        echo "Adding ${DOMAIN} -> ${LB_IP}..."
        NEW_HOSTS="${NEW_HOSTS}
${LB_IP} ${DOMAIN}"
        UPDATED=true
    fi
done

if [ "$UPDATED" = "false" ]; then
    echo "All entries are up to date."
    exit 0
fi

echo "Patching CoreDNS..."

# Apply patch
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
