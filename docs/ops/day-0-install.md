# Day-0 Install

This guide describes a canonical “day-0” installation using this repo’s Make targets. The Make targets are the operator API for install/upgrade.

## Prerequisites

- Kubernetes cluster with:
  - Argo Workflows installed
  - Argo Events installed (only required if using webhook-driven triggers)
  - kpack installed
- CLI tools on your workstation:
  - `kubectl`
  - `kp` (kpack CLI) for log access
  - `pack` (Buildpacks CLI) for packaging the custom buildpack
  - `make`

Notes:
- kpack is typically installed via `luban-bootstrapper`. See [../guides/getting-started.md](../guides/getting-started.md).

## Step 1: Configure Secrets Inputs

Create a local `secrets/` directory (ignored by git) and add the provider/registry credentials you need.

- Follow: [../guides/getting-started.md](../guides/getting-started.md)
- If using a private CA: [../guides/private-ca.md](../guides/private-ca.md)

Before running `make secrets`, confirm the fundamental platform settings in `Makefile.env` match your cluster and registry (for example `K8S_NAMESPACE`, `ARGOCD_NAMESPACE`, `CERT_MANAGER_NAMESPACE`, `REGISTRY_SERVER`). The secrets setup scripts fail fast if these are missing.

Apply secrets:

```bash
make secrets
```

Dry-run rendering (does not apply to cluster):

```bash
make secrets-dry-run
```

## Step 2: Publish Images (Stack/Builder/Buildpack/Tools)

Publish all required images:

```bash
make stack-push
make buildpack-package
make builder-push
make tools-image-push
```

## Step 3: Deploy Pipeline Manifests (Workflows + RBAC + kpack objects)

```bash
make pipeline-deploy
```

Verify installed resources:

```bash
make pipeline-verify
```

This applies:
- RBAC objects under `manifests/rbac/`
- kpack objects under `manifests/kpack/`
- global Argo config restrictions under `manifests/config/` (requires access to `argo` namespace)
- workflow templates under `manifests/workflows/`

## Step 4: Deploy Events (optional, required for webhook triggers)

```bash
make events-deploy
make events-webhook-secret
```

Verify installed resources:

```bash
make events-verify
```

## Next: Verify

Proceed to: [day-0-verify.md](day-0-verify.md)
