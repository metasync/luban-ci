# Getting Started with Luban CI

## Prerequisites

- **Kubernetes Cluster**: OrbStack (recommended for local) or any K8s cluster.
  - *Note: kpack must be installed on the cluster (managed by `luban-bootstrapper`).*
- **Tools**:
  - `kubectl`
  - `pack` CLI
  - `make`
  - `perl` (used to render Secret templates during `make secrets`)
- **Accounts**:
  - GitHub Account (for source code)
  - Quay.io Account (for container registry)
  - **Git Provider**: GitHub (Default) or Azure DevOps.

## Installation & Setup

### 1. Credentials Setup
Create a `secrets/` directory and add the following files (these are ignored by git). The `make secrets` command reads `secrets/*.env` and applies the Kubernetes Secrets.

#### Git Provider Credentials (Required)

**Option A: GitHub (Default)**
Create `secrets/github.env`:
```bash
# Personal Access Token (PAT) with repo and workflow scopes
GITHUB_USERNAME=your_user
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
GITHUB_ORGANIZATION=your_org
```

**Option B: Azure DevOps**
Create `secrets/azure.env`:
```bash
# Personal Access Token (PAT) with Code (Read & Write) scope
AZURE_DEVOPS_TOKEN=xxxxxxxxxxxx
AZURE_ORGANIZATION=your_org
```

**Azure SSH Keys (Required for kpack builds on Azure)**:
1. Generate an SSH key pair: `ssh-keygen -t rsa -b 4096 -f secrets/azure_id_rsa`
2. Add the public key (`secrets/azure_id_rsa.pub`) to your Azure DevOps user settings (SSH Public Keys).
3. Add Azure's host key to `secrets/known_hosts`:
   ```bash
   ssh-keyscan -t rsa ssh.dev.azure.com > secrets/known_hosts
   ```

#### Container Registry Credentials (Required)

**Quay.io (Public/Private Registry)**
Create `secrets/quay.env`:
```bash
QUAY_USERNAME=your_org+robot
QUAY_PASSWORD=your_token
REGISTRY_EMAIL=ci@luban.io
```

**Harbor (Internal Registry)**
Create `secrets/harbor.env`:
```bash
# Harbor Server Domain
HARBOR_SERVER=harbor.luban.metasync.cc

# Admin/RW User (for pushing images)
HARBOR_USERNAME=admin
HARBOR_PASSWORD=xxxxxxxxxxxx

# Read-Only Robot Account (for pulling images in clusters)
HARBOR_RO_USERNAME=robot$luban-ro
HARBOR_RO_PASSWORD=xxxxxxxxxxxx
```

#### Optional Credentials

**Cloudflare (for Tunneling)**
Create `secrets/cloudflare.env`:
```bash
CLOUDFLARE_API_TOKEN=xxxxxxxxxxxx
```

### 2. Apply Secrets
Apply all credentials to the Kubernetes cluster:
```bash
make secrets
```

### 3. Build and Push Stack
Build the custom stack (Base/Run/Build images) and push the Run image to Quay.io:
```bash
make stack-build
make stack-push
```

### 4. Create and Push Builder
Create the CNB Builder and push it to Quay.io:
```bash
make builder-build
make builder-push
```

Notes:
- The kpack `ClusterBuilder` references `quay.io/luban-ci/luban-kpack-builder:<tag>`. Ensure you publish that builder image name (this repo uses `luban-kpack-builder`).
- For local clusters (e.g., OrbStack), if `harbor.luban.metasync.cc` / `argocd.luban.metasync.cc` are not resolvable inside the cluster, run `make patch-coredns`.

### 5. Deploy Pipeline Infrastructure
Set up ServiceAccounts and RBAC for Argo Workflows:
```bash
make pipeline-deploy
```
