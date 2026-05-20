# {{cookiecutter.app_name}} GitOps

Dagster Code Location GitOps configuration for {{cookiecutter.app_name}}.

## Runtime configuration

The code location Deployment wires runtime configuration into the `dagster code-server` pod via:

- `dagster-env` ConfigMap (optional): shared Dagster platform connection settings.
- `dagster-observability` ConfigMap (optional): shared OpenTelemetry environment variables.
- `{{cookiecutter.app_name}}-config` ConfigMap: app-specific environment variables.
- `{{cookiecutter.app_name}}-secret` Secret (optional): app-specific secrets.

## Config changes and rollouts

When environment variables are sourced from a ConfigMap/Secret via `envFrom`, Kubernetes does not update a running container’s environment when that ConfigMap/Secret changes. A restart is required for the new values to take effect in the code location server.

To make config changes take effect reliably, the `snd`/`prd` overlays generate an additional ConfigMap named `{{cookiecutter.app_name}}-config-rollout` (with a hashed suffix) and reference it from the Deployment as an optional ConfigMap volume mount. When either of these files changes, the generated ConfigMap name changes and the Deployment rolls out:

- `app/base/configmap.yaml`
- `app/overlays/<env>/configmap.yaml`

`{{cookiecutter.app_name}}-config-rollout` is not meant to be read by application code. It exists only to trigger a Deployment rollout.
