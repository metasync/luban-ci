# Luban Provisioner

Unified provisioning tool for Luban CI/CD platform.
This tool consolidates functionality for provisioning:

-   **GitOps Repositories**: Scaffolding ArgoCD application manifests.
-   **Source Repositories**: Scaffolding application source code (Python, etc.).
-   **Project Setup**: initializing Git organizations/projects.
-   **Kubernetes Resources**: Bootstrapping Kubernetes namespaces with RBAC and secrets.
-   **Promotion**: Automating the promotion of applications from Sandbox (snd) to Production (prd).

## Architecture

The tool is a Python CLI application built with `click` and `cookiecutter`.
It uses `uv` for dependency management and runs inside a container (Alpine-based) with `kubectl`, `git`, `curl`, and `jq` installed.

### Directory Structure

-   `src/`: Python source code.
    -   `main.py`: Entrypoint.
    -   `commands/`: Subcommands (`gitops`, `source`, `project`, `k8s`, `promote`).
    -   `providers/`: Git provider logic (GitHub, Azure DevOps).
    -   `utils.py`: Shared utilities.
    -   `provider_factory.py`: Factory for Git provider instantiation.
-   `templates/`: Cookiecutter templates.
    -   `gitops/`: Templates for GitOps repos.
    -   `source/`: Templates for Source repos.
    -   `project/`: Templates for Namespaces.
-   `Dockerfile`: Build definition for the tool.
-   `pyproject.toml`: Project configuration and dependencies.
-   `uv.lock`: Dependency lockfile.

## Configuration

The tool requires the following environment variables for Git provider authentication:

-   `GIT_TOKEN`: Personal Access Token (PAT) for GitHub or Azure DevOps.
-   `GIT_SERVER`: The Git server domain (e.g., `github.com` or `dev.azure.com`).

## Usage

### Local Development
This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

1.  Install dependencies:
    ```bash
    uv sync
    ```

2.  Run the tool locally:
    ```bash
    uv run luban-provisioner --help
    ```

### Container Usage
The container image uses `luban-provisioner` as the entrypoint. You can pass arguments directly.

```bash
docker run --rm -it \
    -e GIT_TOKEN=$GIT_TOKEN \
    quay.io/luban-ci/luban-provisioner:latest \
    project --help
```

## Examples (Local)

### 1. Project Setup (Git Provider)

Ensure the Git organization or project exists on the provider (GitHub/Azure).

```bash
uv run luban-provisioner project \
    --project-name my-project \
    --git-org my-org \
    --git-provider github
```

### 2. Kubernetes Provisioning

Bootstrap a Kubernetes namespace with RBAC, resource quotas, and copied secrets.

```bash
uv run luban-provisioner k8s \
    --project-name my-project \
    --environment snd \
    --git-org my-org \
    --image-pull-secret harbor-creds
```

### 3. GitOps Provisioning

Provision a GitOps repository, create it on the provider, push the code, and configure branch protection.

```bash
uv run luban-provisioner gitops \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out \
    --container-port 8080 \
    --service-port 80 \
    --domain-suffix example.com \
    --git-organization my-org \
    --git-provider github
```

### 4. Source Provisioning

Provision a source code repository, create it on the provider, configure webhooks, and push the code.

```bash
uv run luban-provisioner source \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out \
    --git-organization my-org \
    --webhook-url https://webhook.example.com
```

### 5. Promotion

Promote an application from Sandbox (snd) to Production (prd) by updating the image tag in the GitOps repository and creating a Pull Request.

```bash
uv run luban-provisioner promote \
    --app-name my-app \
    --git-organization my-org \
    --git-provider github \
    --project-name my-project
```

## Development

1.  Build the image:
    ```bash
    make build
    ```

2.  Push the image:
    ```bash
    make push
    ```

## Versioning

1.  Update `Makefile.env` to bump the version.
2.  **Important**: Update `pyproject.toml` `version` field to match `Makefile.env`.
3.  Ensure you update the Workflow Templates in `manifests/workflows/` or `manifests/config/` to reference the new version.
