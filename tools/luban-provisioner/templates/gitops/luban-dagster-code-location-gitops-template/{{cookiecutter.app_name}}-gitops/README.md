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

To make config changes take effect reliably, the app generates additional hashed ConfigMaps and references them from the Deployment as optional ConfigMap volume mounts:

- `{{cookiecutter.app_name}}-base-config-rollout`: tracks `app/base/configmap.yaml`
- `{{cookiecutter.app_name}}-overlay-config-rollout`: tracks `app/overlays/<env>/configmap.yaml`

These rollout ConfigMaps are not meant to be read by application code. They exist only to trigger a Deployment rollout.

Note: When Argo CD builds Kustomize from `app/overlays/<env>`, using `configMapGenerator.files` to read files from `../../base` can fail with errors like `security; file ... is not in or below ...`. Splitting the rollout ConfigMaps avoids cross-tree file reads while keeping `resources: ../../base`.
