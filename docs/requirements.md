# Luban CI Requirements

## 1. Project Overview
**Project Name:** `luban-ci`

**Goal:** Build a flexible, extensible, GitOps-based CI/CD platform on Kubernetes.

**Scope:** Cluster bootstrap (Argo, Argo CD, kpack, ingress/gateway, etc.) is assumed to be provisioned externally (e.g. by `luban-bootstrapper`). This repository focuses on:
- CI/CD workflows and templates
- Buildpacks / builder / stack
- Provisioning automation (`luban-provisioner`)
- GitOps conventions and promotion mechanics

**Design Principles:**
- **Extensibility:** Multiple Git providers (GitHub, Azure DevOps) and templates (apps + Dagster).
- **Security defaults:** Non-root execution and least-privilege RBAC.
- **GitOps-first:** Desired state is driven by Git commits.
- **Promotion-based delivery:** Build in Sandbox (`snd`), promote to Production (`prd`).

## 2. Core Components
- **Argo Workflows:** Pipeline orchestration.
- **Argo Events:** Webhook ingestion and workflow triggers.
- **Argo CD:** GitOps deployment.
- **kpack:** Kubernetes-native Cloud Native Buildpacks build engine.
- **Registries:** Quay (external) and Harbor (internal).

## 3. Pipeline Architecture

### 3.1 Trigger Phase (Argo Events)
- Receives webhook events from GitHub/Azure.
- Normalizes event payloads into common parameters.
- Triggers the dispatcher workflow.

### 3.2 Build Phase (Argo Workflows + kpack)
- Runs in `ci-<project>` namespaces.
- Creates/updates a kpack `Image` resource and watches its `Build` status.
- Streams kpack build logs via `kp`.

### 3.3 Deploy Phase (GitOps + Argo CD)
- Updates the GitOps repo overlay for `snd` to the new image tag.
- Argo CD syncs into `snd-<project>`.

### 3.4 Promotion Phase
- Promotes from `snd` to `prd` (often via Git tag or explicit promotion workflow).
- Updates the `prd` overlay (typically via PR) for review/approval.

## 4. Provisioning & Templates

### 4.1 Unified Provisioner
`luban-provisioner` provisions:
- Projects/namespaces and RBAC
- Source repos and GitOps repos
- Multi-cluster infra repos (CI/CD overlays)
- Dagster platform and code location templates

### 4.2 Workflows
Kubernetes manifests for workflow templates live under `manifests/workflows/`.

## 5. Secrets & Replication

### 5.1 Local Secrets Input
Secrets are provided via `secrets/*.env` (gitignored). These files are parsed by `manifests/secrets/setup-secrets.sh` as plain `KEY=VALUE` lines (not executed via `source`, and not interpreted by `make`). Use a literal `$` in values (for example Harbor robot users like `robot$luban-ci`).

### 5.2 Applying Secrets
- `make secrets` applies secrets using `manifests/secrets/setup-secrets.sh`.
- Secrets are applied using server-side apply, and the script removes the `kubectl.kubernetes.io/last-applied-configuration` annotation from Secrets to avoid persisting secret payloads in annotations.
- Source-of-truth secrets live in `luban-ci` and are replicated into target namespaces via the Kubernetes replicator using the opt-in model:
  - Source secrets set `replication-allowed` and `replication-allowed-namespaces`.
  - Target namespaces include stub resources with `replicate-from: luban-ci/<name>`.

For application runtime secrets, the recommended naming convention is:

- Source secret in `luban-ci`: `<project>-<app>-secrets-<env>` (for example `dwt1-etl-jobs-secrets-snd`).
- Target secret in `<env>-<project>`: `<app>-secret` (a GitOps-managed stub with `replicate-from`).

### 5.3 Docker Registry Credential Semantics
- `luban-ci/quay-creds`, `luban-ci/harbor-creds`, `luban-ci/harbor-ro-creds` contain the real `.dockerconfigjson`.
- Target namespaces include stub `kubernetes.io/dockerconfigjson` Secrets with `replicate-from`.
- These stubs must include a placeholder `.dockerconfigjson` key (for example `e30=`) because the type requires the key to exist.

### 5.4 Azure SSH Credential Semantics
- `luban-ci/azure-ssh-creds` contains the real key material.
- `ci-*/azure-ssh-creds` is created by the infra repo templates and uses `replicate-from` so the GitOps source owns required annotations like `kpack.io/git`.

### 5.4.1 ADO SSH Credential Semantics
- `luban-ci/ado-ssh-creds` contains the real key material.
- `ci-*/ado-ssh-creds` is created by the infra repo templates and uses `replicate-from` so the GitOps source owns required annotations like `kpack.io/git`.

### 5.5 uv/Python Mirror netrc Semantics
- `luban-ci/uv-mirror-netrc` contains the real netrc content (type `service.binding/netrc`).
- `ci-*/uv-mirror-netrc` is created by the infra repo templates and uses `replicate-from` so the GitOps source owns required metadata.
- The `netrc` file may contain multiple `machine` entries (for example one host for uv releases and another host for managed Python downloads).
