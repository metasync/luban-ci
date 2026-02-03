#!/bin/bash
set -e

# Default values
TUNNEL_NAME=${TUNNEL_NAME:-"luban-webhook"}
TUNNEL_HOSTNAME=${TUNNEL_HOSTNAME:-"webhook-luban.metasync.cc"}
K8S_NAMESPACE=${K8S_NAMESPACE:-"luban-ci"}
CREDENTIALS_SECRET_NAME="cloudflare-tunnel-credentials"
# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/cloudflared-config.yaml.template"
CONFIG_FILE="$SCRIPT_DIR/cloudflared-config.yaml"
DEPLOYMENT_FILE="$SCRIPT_DIR/cloudflared-deployment.yaml"

echo "------------------------------------------------"
echo "Cloudflare Tunnel Setup"
echo "Tunnel Name: $TUNNEL_NAME"
echo "Hostname:    $TUNNEL_HOSTNAME"
echo "Namespace:   $K8S_NAMESPACE"
echo "------------------------------------------------"

# Check dependencies
if ! command -v cloudflared &> /dev/null; then
    echo "Error: cloudflared not found. Please install it first."
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl not found. Please install it first."
    exit 1
fi

if [ ! -f "$TEMPLATE_FILE" ]; then
    echo "Error: Template file $TEMPLATE_FILE not found."
    exit 1
fi

# 1. Login
echo "Checking Cloudflare authentication..."
if [ ! -f ~/.cloudflared/cert.pem ]; then
    echo "You are not logged in. Opening browser for authentication..."
    cloudflared tunnel login
else
    echo "Already logged in."
fi

# 2. Create Tunnel
echo "Checking tunnel '$TUNNEL_NAME'..."
# Try to find existing tunnel ID by name
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' | head -n 1)

if [ -z "$TUNNEL_ID" ]; then
    echo "Creating tunnel '$TUNNEL_NAME'..."
    cloudflared tunnel create "$TUNNEL_NAME"
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' | head -n 1)
else
    echo "Tunnel '$TUNNEL_NAME' exists with ID: $TUNNEL_ID"
fi

if [ -z "$TUNNEL_ID" ]; then
    echo "Error: Failed to obtain Tunnel ID."
    exit 1
fi

# 3. Route DNS
echo "Routing DNS '$TUNNEL_HOSTNAME' to tunnel..."
# Use -f to overwrite if exists
cloudflared tunnel route dns -f "$TUNNEL_NAME" "$TUNNEL_HOSTNAME"

# 4. Create Kubernetes Secret
echo "Creating Kubernetes Secret..."
CRED_FILE=~/.cloudflared/$TUNNEL_ID.json

if [ ! -f "$CRED_FILE" ]; then
    echo "Error: Credentials file $CRED_FILE not found!"
    exit 1
fi

# Ensure namespace exists
kubectl create ns "$K8S_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic "$CREDENTIALS_SECRET_NAME" \
    --from-file=credentials.json="$CRED_FILE" \
    -n "$K8S_NAMESPACE" \
    --dry-run=client -o yaml | kubectl apply -f -

# 5. Generate ConfigMap
echo "Generating ConfigMap from template..."
sed -e "s/\${TUNNEL_ID}/$TUNNEL_ID/g" \
    -e "s/\${TUNNEL_HOSTNAME}/$TUNNEL_HOSTNAME/g" \
    -e "s/\${K8S_NAMESPACE}/$K8S_NAMESPACE/g" \
    "$TEMPLATE_FILE" > "$CONFIG_FILE"

# 6. Deploy
echo "Deploying to Kubernetes..."
kubectl apply -f "$CONFIG_FILE"
kubectl apply -f "$DEPLOYMENT_FILE"

# 7. Restart
echo "Restarting cloudflared..."
kubectl rollout restart deployment cloudflared -n "$K8S_NAMESPACE"

echo "------------------------------------------------"
echo "Tunnel setup complete!"
echo "Public URL: https://$TUNNEL_HOSTNAME"
echo "------------------------------------------------"
