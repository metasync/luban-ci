#!/bin/bash
set -e

# Configuration
GATEWAY_NAMESPACE="gateway"
CA_SECRET="local-ca-root"
KPACK_NAMESPACE="kpack"
KPACK_CONFIG="kpack-config"

echo "Extracting Root CA from secret ${CA_SECRET} in namespace ${GATEWAY_NAMESPACE}..."

# Extract CA certificate
# The secret is type kubernetes.io/tls, so the key is 'ca.crt' (or sometimes 'tls.crt' if it's self-signed root)
# We check for ca.crt first, then tls.crt
CA_CERT=$(kubectl get secret ${CA_SECRET} -n ${GATEWAY_NAMESPACE} -o jsonpath='{.data.ca\.crt}' 2>/dev/null)

if [ -z "$CA_CERT" ]; then
    echo "ca.crt not found, checking tls.crt..."
    CA_CERT=$(kubectl get secret ${CA_SECRET} -n ${GATEWAY_NAMESPACE} -o jsonpath='{.data.tls\.crt}')
fi

if [ -z "$CA_CERT" ]; then
    echo "Error: Could not find CA certificate in secret ${CA_SECRET}."
    exit 1
fi

echo "Found CA certificate."

# Decode the cert to a file temporarily
echo "$CA_CERT" | base64 -d > /tmp/kpack-ca.crt

# Verify it's a valid cert
if ! openssl x509 -in /tmp/kpack-ca.crt -noout; then
    echo "Error: Extracted data is not a valid certificate."
    rm /tmp/kpack-ca.crt
    exit 1
fi

echo "Updating kpack-config in namespace ${KPACK_NAMESPACE}..."

# Create/Update ConfigMap
# We include ca-certs for build-time trust
# We also include insecure-registries as a fallback/compatibility measure
kubectl create configmap ${KPACK_CONFIG} \
    -n ${KPACK_NAMESPACE} \
    --from-file=ca-certs=/tmp/kpack-ca.crt \
    --from-literal="insecure-registries=harbor.k8s.orb.local" \
    --dry-run=client -o yaml | kubectl apply -f -

rm /tmp/kpack-ca.crt

echo "Restarting kpack-controller to apply changes..."
kubectl rollout restart deployment kpack-controller -n ${KPACK_NAMESPACE}

echo "Waiting for kpack-controller to be ready..."
kubectl rollout status deployment kpack-controller -n ${KPACK_NAMESPACE} --timeout=60s

echo "Kpack TLS configuration completed successfully."
