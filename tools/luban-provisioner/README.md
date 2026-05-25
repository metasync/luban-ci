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
    -   `commands/`: Subcommands (`gitops`, `source`, `project`, `infra`, `promote`, `dagster`, `config`).
    -   `cli/`: CLI helpers (for example `--set key=value` parsing).
    -   `config/`: Config file loading helpers.
    -   `git/`: Git auth and repo helpers.
    -   `providers/`: Git provider logic (GitHub, Azure DevOps).
    -   `templates/`: Template rendering and path helpers.
    -   `provider_factory.py`: Factory for Git provider instantiation.
-   `templates/`: Cookiecutter templates.
    -   `gitops/`: Templates for GitOps repos.
    -   `source/`: Templates for Source repos.
-   `Dockerfile`: Build definition for the tool.
-   `pyproject.toml`: Project configuration and dependencies.
-   `uv.lock`: Dependency lockfile.

## Configuration

The tool requires the following environment variables for Git provider authentication:

-   `GIT_TOKEN`: Personal Access Token (PAT) for GitHub or Azure DevOps.
-   `GIT_SERVER`: The Git server domain (e.g., `github.com`, `dev.azure.com`, or an Azure DevOps Server hostname like `ado.example.com`).
-   `LUBAN_PROVISIONER_SUPPRESS_URLLIB3_WARNING`: Set to `0` to show the `urllib3` version warning (default: `1`).
-   `LUBAN_PROVISIONER_LOG_CONTEXT`: Set to `0` to disable printing template context (default: `1`).
-   `LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS`: Set to `0` to print template context without masking (default: `1`).
-   `LUBAN_PROVISIONER_LOG_CONTEXT_MODE`: `summary` or `full` (default: `summary`).

### Logging

Template context logging is controlled by:

-   `LUBAN_PROVISIONER_LOG_CONTEXT`: `0` disables context logging entirely.
-   `LUBAN_PROVISIONER_LOG_CONTEXT_MODE`: `summary` (default) prints keys + safe preview + sensitive keys; `full` prints the full context dict.
-   `LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS`: `1` (default) masks sensitive values; `0` prints them as-is.

Examples:

```bash
# Disable context logging
export LUBAN_PROVISIONER_LOG_CONTEXT=0

# Print the full context but still mask secrets
export LUBAN_PROVISIONER_LOG_CONTEXT_MODE=full

# Print the full context without masking (use carefully)
export LUBAN_PROVISIONER_LOG_CONTEXT_MODE=full
export LUBAN_PROVISIONER_MASK_CONTEXT_SECRETS=0
```

### Configuration File (Optional)
The `source` and `gitops` commands accept a `--config-file` argument (YAML/JSON). This allows injecting custom variables into templates, such as:
- `python_index_url`: Custom Python Package Index URL (injected into `pyproject.toml`).
- `python_index_name`: Name for the custom index (default: `custom`).

When provisioning, the tool can print the template context for troubleshooting. Values for keys matching `token`, `secret`, `password`, or `*_key` are masked by default.
By default, the tool prints a summary (keys + safe preview + masked sensitive values). Set `LUBAN_PROVISIONER_LOG_CONTEXT_MODE=full` to print the full (masked/unmasked) context dict.
Use `--dry-run` on `source` / `gitops` to render the template without calling the Git provider APIs.
Use `--dry-run` on `infra ci init|update` and `infra cd init|update` to render templates without provider/git operations.
Use `--dry-run` on `project` to validate provider selection without creating/verifying remote projects.
Use `--dry-run` on `promote` to compute the target image/tag and render the PRD overlay update without committing/pushing/creating a PR.
Use `dry-run` (top-level command) to run a one-shot local rendering of common templates into a single output directory.

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

## Template Types

### Source templates

- `python`: Minimal Python application skeleton.
- `dagster-platform`: Dagster platform dependency skeleton (Dagster components are deployed via GitOps templates).
- `dagster-code-location`: Dagster code location skeleton exporting `defs`.
- `dagster-dbt-starrocks-code-location`: Dagster code location skeleton wired to a StarRocks dbt project.

## Examples (Local)

### 1. Project Setup (Git Provider)

Ensure the Git organization or project exists on the provider (GitHub/Azure).

```bash
uv run luban-provisioner project \
    --project-name my-project \
    --git-organization my-org \
    --git-provider github
```

### 2. CI Infra Repo (Init)

Initialize a CI infrastructure repository (base manifests).

```bash
uv run luban-provisioner infra ci init \
    --repo-name my-infra-ci-repo \
    --git-organization my-org \
    --git-provider github \
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
