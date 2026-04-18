# Developer Workflow

Luban CI provides a set of tools to facilitate development and testing of the CI pipelines and event triggers.

## User Access Management

Luban CI automatically configures RBAC for your project namespaces to enable OIDC group access to the Argo Workflows UI via ServiceAccount mapping.

- **Admin Access**:
  - The OIDC group defined in `admin_group` is mapped to the `project-admin` ServiceAccount.
  - Bound to the `admin` ClusterRole within the project namespace.
  - Can view, submit, resubmit, and delete workflows.
  - Can view logs and artifacts.
- **Developer Access**:
  - The OIDC group defined in `developer_group` is mapped to the `project-developer` ServiceAccount.
  - Bound to the `edit` ClusterRole within the project namespace.
  - Can view, submit, and resubmit workflows.
  - Can view logs.

### Service Accounts

The system provisions two permanent ServiceAccounts in each runtime environment namespace (e.g., `snd-payment`) which are used by Argo Workflows to execute actions on behalf of the user:

1. `project-admin`: Used by users in the `admin_group`.
2. `project-developer`: Used by users in the `developer_group`.

You can use these accounts to verify permissions using `kubectl auth can-i`:

```bash
# Verify Admin Access
kubectl auth can-i delete workflow --as=system:serviceaccount:snd-payment:project-admin -n snd-payment
# > yes

# Verify Developer Access (cannot delete)
kubectl auth can-i delete workflow --as=system:serviceaccount:snd-payment:project-developer -n snd-payment
# > no
```

## Testing CI Pipeline

Manually trigger the kpack CI workflow (via Argo CLI) with custom parameters.

```bash
# Default parameters (from test/Makefile.env)
make test-ci-pipeline

# Override parameters
make test-ci-pipeline APP_NAME=my-app REPO_URL=https://github.com/myorg/my-app.git TAG=2.0.0
```

Notes:

- CI workflows run in `ci-<project>` namespaces (not `snd-<project>`). The test target submits into `ci-<project>`.
- The workflow updates GitOps (`develop` for `snd`), and ArgoCD deploys into `snd-<project>`.

## Simulating Webhook Events

Send a signed GitHub push event payload to the local Gateway to verify the entire event-to-pipeline flow.

**Prerequisites**:

1. Gateway is running (`luban-gateway` in `gateway` namespace).
2. Webhook secret is configured (`make events-webhook-secret`).
3. Gateway URL is accessible (default: `https://webhook.luban.metasync.cc/push`).

**Usage**:

```bash
# Option 1: Python script (requires python3)
make test-events-webhook-py

# Option 2: Shell script (requires curl, openssl)
make test-events-webhook

# Testing with custom Tunnel Hostname
export GATEWAY_URL=https://my-webhook.metasync.cc/push
make test-events-webhook
```

Notes:

- The shell webhook test script expects `REVISION` to be a git commit SHA. If omitted, it resolves the repository `HEAD` SHA automatically.

### Local DNS Resolution (Patching CoreDNS)

If you are running locally (e.g., OrbStack) and need the cluster to resolve the ingress domains (like `webhook.luban.metasync.cc`) to the internal Gateway LoadBalancer IP, you can use the `patch-coredns` utility.

```bash
make patch-coredns
```

### Cloudflare Tunnel (Optional)

If you need to expose the internal webhook service to the internet (e.g., for real GitHub webhooks), you can use the built-in Cloudflare Tunnel setup.

```bash
# Setup Tunnel
make tunnel-setup

# Setup with custom hostname
make tunnel-setup TUNNEL_HOSTNAME=my-webhook.metasync.cc
```

## Check Build Logs

View the logs of the latest kpack build for a specific application:

```bash
make pipeline-logs APP_NAME=my-app
```

## Best Practices

### Branch Protection

It is highly recommended to enable branch protection rules on your GitOps repository:

- **`main`**: Require Pull Request reviews, status checks, and restrict direct pushes. This ensures Production changes are always reviewed.
- **`develop`**: Allow direct pushes from the CI ServiceAccount (for automated deployments) but require PRs for manual changes.
