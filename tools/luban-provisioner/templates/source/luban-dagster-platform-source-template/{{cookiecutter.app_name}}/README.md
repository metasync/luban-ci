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

## Run Launcher: Code-Location-Aware Env Injection

The platform uses a custom K8s run launcher (`CodeLocationAwareK8sRunLauncher`)
that ensures every run pod receives the correct ConfigMaps and Secrets for its
code location — including ad-hoc asset materializations (e.g. `__ASSET_JOB`
from the Dagster UI).

### How it works

1. **Auto-discovery** (default): Every code location automatically gets
   `<code_location>-config` (ConfigMap) and `<code_location>-secret` (Secret)
   injected. No configuration needed — this follows the naming convention set
   by code location deployments.
   
   `<code_location>-secret` is expected to exist. If a pipeline does not need any
   secrets, create an empty Secret with that name.

2. **Explicit overrides** (optional): Add entries to `code_location_env` in
   the instance ConfigMap (`dagster-instance-cm.yaml`) to append extra
   env vars, ConfigMaps, Secrets, or custom k8s config. Explicit entries
   **augment** auto-discovered defaults — they do not replace them.
   
   `env_vars` are `NAME=value` strings. NAME must match `[A-Za-z_][A-Za-z0-9_]*`.

### Configuration

Configure in `dagster-instance-cm.yaml` (GitOps repo):

```yaml
run_launcher:
  config:
    code_location_env: {}
```

Leave empty for auto-discovery only. Add per-location overrides as needed:

```yaml
code_location_env:
  my_etl:
    env_config_maps: ["extra-env"]
    env_vars: ["CUSTOM_VAR=value"]
```

See the comments in `dagster-instance-cm.yaml` for full merge rules.
