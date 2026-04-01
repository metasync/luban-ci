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

Notes:
- Luban CI uses clean HTTPS repo URLs and relies on git's credential mechanism for authentication (no PATs embedded in remote URLs).
- `GITHUB_USERNAME` is used as the Basic auth username; the PAT is used as the password.

**Option B: Azure DevOps**
Create `secrets/azure.env`:
```bash
# Personal Access Token (PAT) with Code (Read & Write) scope
AZURE_DEVOPS_TOKEN=xxxxxxxxxxxx
AZURE_ORGANIZATION=your_org

# Optional (Azure DevOps Server / on-prem)
# Hostname used for SSH clones in kpack (kpack.io/git annotation)
# AZURE_SSH_HOST=ado.example.com
```

Notes:
- For Azure DevOps Server (on-prem), set `azure_server` in `manifests/config/luban-config.yaml` to your server hostname.
- Luban CI uses git's credential mechanism for HTTPS auth for both Azure DevOps cloud and on-prem.

**Azure SSH Keys (Required for kpack builds on Azure)**:
1. Generate an SSH key pair: `ssh-keygen -t rsa -b 4096 -f secrets/azure_id_rsa`
2. Add the public key (`secrets/azure_id_rsa.pub`) to your Azure DevOps user settings (SSH Public Keys).
3. Add Azure's host key to `secrets/known_hosts`:
   ```bash
   # Azure DevOps Services (cloud)
   ssh-keyscan -t rsa ssh.dev.azure.com > secrets/known_hosts

   # Azure DevOps Server (on-prem)
   # ssh-keyscan -t rsa <your_azure_server_host> > secrets/known_hosts
   ```

**uv/Python Mirrors (HTTP Basic Auth via netrc, Optional)**

If you use air-gapped mirrors for:
- `BP_UV_RELEASE_BASE_URL` (uv binaries + `.sha256`)
- `BP_UV_PYTHON_INSTALL_MIRROR` (uv managed Python downloads)

and those mirrors require HTTP Basic Auth, configure a netrc binding.

1. Create `secrets/uv-mirror.env`:
   ```bash
   # Required if your uv release mirror requires auth
   # Host only; scheme/path/port are ignored if present.
   UV_MIRROR_HOST=mirror.example.com
   UV_MIRROR_USERNAME=your_user
   UV_MIRROR_PASSWORD=your_password

   # Optional: set only if the Python mirror is a different host
   # If set, credentials default to UV_MIRROR_USERNAME/PASSWORD unless overridden.
   UV_PYTHON_MIRROR_HOST=python-mirror.example.com
   # Leave empty to reuse UV_MIRROR_USERNAME/PASSWORD
   UV_PYTHON_MIRROR_USERNAME=
   UV_PYTHON_MIRROR_PASSWORD=
   ```

2. Apply secrets:
   ```bash
   make secrets
   ```

What this does:
- Creates `luban-ci/uv-mirror-netrc` (type `service.binding/netrc`) containing a `netrc` file.
- CI namespaces (`ci-*`) contain a stub `uv-mirror-netrc` Secret; the replicator fills the real data.
- During kpack builds, if `ci-*/uv-mirror-netrc` contains a real `netrc` (not placeholder), the CI workflow mounts it as a kpack Service Binding.

Notes:
- If all `UV_*` fields are empty, no netrc secret is created and builds run unchanged.
- If you set `UV_PYTHON_MIRROR_HOST`, you must provide credentials either via `UV_PYTHON_MIRROR_USERNAME/PASSWORD` or `UV_MIRROR_USERNAME/PASSWORD`.
- Do not put credentials into `BP_UV_RELEASE_BASE_URL` / `BP_UV_PYTHON_INSTALL_MIRROR` URLs; they may be logged.

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
