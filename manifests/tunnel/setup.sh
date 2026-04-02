#!/usr/bin/env bash
set -euo pipefail

# This script manages the Kubernetes-side resources for an existing Cloudflare Tunnel.
# It does NOT create tunnels or route DNS. Those are assumed to be already done.

# Namespace where cloudflared runs and where the ConfigMap/Secret live.
K8S_NAMESPACE=${K8S_NAMESPACE:-"luban-ci"}

# Hostname for incoming webhook traffic (optional). If unset, derive from the existing ConfigMap.
TUNNEL_HOSTNAME=${TUNNEL_HOSTNAME:-""}

# Tunnel name is informational only when relying solely on Kubernetes resources.
TUNNEL_NAME=${TUNNEL_NAME:-"luban-webhook"}

# Secret holding the Cloudflare tunnel credentials.
CREDENTIALS_SECRET_NAME=${CREDENTIALS_SECRET_NAME:-"cloudflare-tunnel-credentials"}

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/cloudflared-config.yaml.template"
CONFIG_FILE="$SCRIPT_DIR/cloudflared-config.yaml"
DEPLOYMENT_FILE="$SCRIPT_DIR/cloudflared-deployment.yaml"

echo "------------------------------------------------"
echo "Cloudflare Tunnel Setup (Kubernetes only)"
echo "Tunnel Name: $TUNNEL_NAME"
echo "Hostname:    ${TUNNEL_HOSTNAME:-<derive from cluster>}"
echo "Namespace:   $K8S_NAMESPACE"
echo "------------------------------------------------"

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl not found. Please install it first." >&2
  exit 1
fi

if [ ! -f "$TEMPLATE_FILE" ]; then
  echo "Error: Template file $TEMPLATE_FILE not found." >&2
  exit 1
fi

if [ ! -f "$DEPLOYMENT_FILE" ]; then
  echo "Error: Deployment file $DEPLOYMENT_FILE not found." >&2
  exit 1
fi

echo "Ensuring namespace '$K8S_NAMESPACE' exists..."
kubectl create ns "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - >/dev/null

echo "Reading existing tunnel configuration from ConfigMap/cloudflared-config..."
EXISTING_CFG=$(kubectl get configmap cloudflared-config -n "$K8S_NAMESPACE" -o jsonpath='{.data.config\.yaml}' 2>/dev/null || true)
if [ -z "$EXISTING_CFG" ]; then
  echo "Error: missing ConfigMap cloudflared-config in namespace '$K8S_NAMESPACE'." >&2
  echo "This script manages an existing tunnel; bootstrap the tunnel and credentials first." >&2
  exit 1
fi

TUNNEL_ID=$(printf '%s\n' "$EXISTING_CFG" | awk -F': *' '/^\s*tunnel:\s*/{print $2; exit}' | tr -d '"')
if [ -z "$TUNNEL_ID" ]; then
  echo "Error: failed to derive tunnel id from existing cloudflared-config." >&2
  exit 1
fi

if [ -z "$TUNNEL_HOSTNAME" ]; then
  TUNNEL_HOSTNAME=$(printf '%s\n' "$EXISTING_CFG" | awk -F': *' '/hostname:\s*/{print $2; exit}' | tr -d '"')
fi

if [ -z "$TUNNEL_HOSTNAME" ]; then
  echo "Error: TUNNEL_HOSTNAME is not set and could not be derived from existing config." >&2
  exit 1
fi

echo "Checking credentials Secret/${CREDENTIALS_SECRET_NAME}..."
if ! kubectl -n "$K8S_NAMESPACE" get secret "$CREDENTIALS_SECRET_NAME" >/dev/null 2>&1; then
  echo "Error: missing Secret '$CREDENTIALS_SECRET_NAME' in namespace '$K8S_NAMESPACE'." >&2
  echo "It must contain credentials.json for tunnel id '$TUNNEL_ID'." >&2
  exit 1
fi

echo "Rendering ConfigMap from template..."
sed -e "s/\${TUNNEL_ID}/$TUNNEL_ID/g" \
  -e "s/\${TUNNEL_HOSTNAME}/$TUNNEL_HOSTNAME/g" \
  -e "s/\${K8S_NAMESPACE}/$K8S_NAMESPACE/g" \
  "$TEMPLATE_FILE" > "$CONFIG_FILE"

echo "Applying ConfigMap and Deployment..."
kubectl apply -f "$CONFIG_FILE" >/dev/null
kubectl apply -f "$DEPLOYMENT_FILE" >/dev/null

echo "Restarting deployment/cloudflared..."
kubectl rollout restart deployment cloudflared -n "$K8S_NAMESPACE" >/dev/null

echo "------------------------------------------------"
echo "Tunnel setup complete!"
echo "Public URL: https://$TUNNEL_HOSTNAME"
echo "------------------------------------------------"
