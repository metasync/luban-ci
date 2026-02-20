# {{cookiecutter.app_name}}

Dagster Platform for {{cookiecutter.app_name}}.

## Local Development

1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Sync dependencies: `uv sync`
3. Run Dagster: `uv run dagster dev`

## Deployment

This project is built using Kpack and deployed via ArgoCD.
- **Build**: Uses `pyproject.toml` to build a container image.
- **Deploy**: Updates the GitOps repository with the new image tag.
