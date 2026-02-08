# Luban Provisioner

Unified provisioning tool for Luban CI/CD platform.
This tool consolidates functionality for provisioning:
-   **GitOps Repositories**: Scaffolding ArgoCD application manifests.
-   **Source Repositories**: Scaffolding application source code (Python, etc.).
-   **Project Namespaces**: Bootstrapping Kubernetes namespaces with RBAC and secrets.

## Architecture

The tool is a Python CLI application built with `click` and `cookiecutter`.
It runs inside a container (Alpine-based) with `kubectl`, `git`, `curl`, and `jq` installed.

### Directory Structure

-   `src/`: Python source code.
    -   `main.py`: Entrypoint.
    -   `commands/`: Subcommands (`gitops`, `source`, `project`).
    -   `providers/`: Git provider logic (GitHub API).
    -   `utils.py`: Shared utilities.
-   `templates/`: Cookiecutter templates.
    -   `gitops/`: Templates for GitOps repos.
    -   `source/`: Templates for Source repos.
    -   `project/`: Templates for Namespaces.
-   `Dockerfile`: Build definition for the tool.

## Usage

### GitOps Provisioning

Provision a GitOps repository, create it on GitHub, push the code, and configure branch protection.

```bash
python3 src/main.py gitops \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out \
    --container-port 8080 \
    --service-port 80 \
    --domain-suffix example.com \
    --git-organization my-org \
    --git-provider github
```

### Source Provisioning

Provision a source code repository, create it on GitHub, configure webhooks, and push the code.

```bash
python3 src/main.py source \
    --project-name my-project \
    --application-name my-app \
    --output-dir /tmp/out \
    --git-organization my-org \
    --webhook-url https://webhook.example.com
```

### Project Provisioning

Bootstrap a Kubernetes namespace with RBAC, resource quotas, and copied secrets.

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
