# Make Targets Reference

This document describes the Make targets that function as the operator API for installing and operating Luban CI.

Core platform defaults (namespaces, registry settings, versions) live in `Makefile.env`.

## Root Makefile

Source: `Makefile`

### Day-0 / Deploy

- `make all`: end-to-end setup (secrets → images → pipeline → events)
- `make secrets`: apply/update Kubernetes Secrets from local `secrets/*.env`
- `make secrets-dry-run`: render and validate secret templates without applying
- `make stack-push`: build/tag/push stack images
- `make buildpack-package`: package and publish the custom buildpack image
- `make builder-push`: build/tag/push builder image
- `make tools-image-push`: push tooling images (gitops-utils, luban-provisioner)
- `make pipeline-deploy`: deploy RBAC, kpack objects, config, workflow templates
- `make pipeline-verify`: verify pipeline resources are present (RBAC/config/kpack/templates)
- `make events-deploy`: deploy Argo Events resources
- `make events-verify`: verify events resources are present (EventBus/EventSource/Sensor/HTTPRoute)
- `make events-webhook-secret`: ensure webhook secret exists

### Day-2 / Operations

- `make pipeline-logs APP_NAME=<app>`: show latest kpack build logs (requires `kp`)
- `make events-webhook-secret-rotate`: rotate webhook secret
- `make patch-coredns`: patch CoreDNS for local DNS resolution (OrbStack)

### Tests and Dev

- `make test-ci-pipeline`: trigger a CI workflow (test harness)
- `make test-events-webhook`: send signed webhook payload (test harness)
- `make lint`: run lint checks (currently provisioner-focused)
- `make format`: run auto-format (currently provisioner-focused)

## manifests/Makefile

Source: `manifests/Makefile`

- `make -C manifests deploy`: apply RBAC + kpack objects + config + workflow templates
- `make -C manifests verify`: verify pipeline resources are present
- `make -C manifests secrets`: apply secrets via `manifests/secrets/setup-secrets.sh`
- `make -C manifests secrets-dry-run`: dry-run secret rendering
- `make -C manifests logs APP_NAME=<app>`: `kp build logs` helper

## events/Makefile

Source: `events/Makefile`

- `make -C events deploy`: apply Argo Events manifests
- `make -C events verify`: verify events resources are present
- `make -C events webhook-secret`: ensure webhook secret exists
- `make -C events webhook-secret-rotate`: force rotate webhook secret

## Related Ops Docs

- Day-0 install: [../ops/day-0-install.md](../ops/day-0-install.md)
- Day-0 verification: [../ops/day-0-verify.md](../ops/day-0-verify.md)
- Day-2 operations: [../ops/day-2-operations.md](../ops/day-2-operations.md)
