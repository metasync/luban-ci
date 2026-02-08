# Luban Provisioner

Unified provisioning tool for Luban CI/CD platform.
This tool consolidates functionality for provisioning:
-   **GitOps Repositories**: Scaffolding ArgoCD application manifests.
-   **Source Repositories**: Scaffolding application source code (Python, etc.).
-   **Project Namespaces**: Bootstrapping Kubernetes namespaces with RBAC and secrets.

## Architecture

The tool is a Python CLI application built with `click` and `cookiecutter`.
It runs inside a container (Alpine-based) with `kubectl` and `jq` installed.

### Directory Structure

-   `src/`: Python source code.
    -   `main.py`: Entrypoint.
    -   `commands/`: Subcommands (`gitops`, `source`, `project`).
    -   `utils.py`: Shared utilities.
-   `templates/`: Cookiecutter templates.
    -   `gitops/`: Templates for GitOps repos.
    -   `source/`: Templates for Source repos.
    -   `project/`: Templates for Namespaces.
-   `Dockerfile`: Multi-stage build (or simple Alpine build) for the tool.

## Usage

### GitOps Provisioning

```bash
python3 src/main.py gitops \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out \
    --container-port 8080 \
    --service-port 80 \
    --domain-suffix example.com
```

### Source Provisioning

```bash
python3 src/main.py source \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out
```

### Project Provisioning

```bash
python3 src/main.py project \
    --project-name my-project \
    --environment snd \
    --git-org my-org \
    --image-pull-secret harbor-creds
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

Update `Makefile.env` to bump the version.
Ensure you update the Workflow Templates in `manifests/workflows/` to reference the new version.
