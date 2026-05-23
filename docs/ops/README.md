# Operations (DevOps)

This section is the DevOps/operator entrypoint for deploying, verifying, upgrading, and troubleshooting Luban CI.

## What This Repo Owns

- Argo Workflows templates and RBAC: `manifests/workflows/`, `manifests/rbac/`
- kpack stack/builder/lifecycle objects (as manifests): `manifests/kpack/`
- Argo Events resources (EventBus/EventSource/Sensor): `events/`
- Tooling images (GitOps/provisioning helpers): `tools/`

## What This Repo Does Not Own

- Cluster-level installation of Argo Workflows / Argo Events / kpack controllers (typically installed via `luban-bootstrapper`).

## Golden Paths

- Day-0 install: [day-0-install.md](day-0-install.md)
- Day-0 verification: [day-0-verify.md](day-0-verify.md)
- Day-2 operations: [day-2-operations.md](day-2-operations.md)
- Upgrades and rollbacks: [upgrades.md](upgrades.md)

## Runbooks

- Webhook not triggering: [runbooks/webhook-not-triggering.md](runbooks/webhook-not-triggering.md)
- kpack build failing: [runbooks/kpack-build-failing.md](runbooks/kpack-build-failing.md)
- Git auth failing (ADO/on-prem): [runbooks/git-auth-failing-ado.md](runbooks/git-auth-failing-ado.md)
- Secret replication issues: [runbooks/secret-replication-issues.md](runbooks/secret-replication-issues.md)
- `templateRef` volume not found: [runbooks/templateRef-volume-not-found.md](runbooks/templateRef-volume-not-found.md)

## References

- Make target reference: [../reference/make-targets.md](../reference/make-targets.md)
- Configuration keys: [../guides/admin-guide.md](../guides/admin-guide.md)
- Multi-cluster model (concept): [../architecture/multi-cluster-v2.md](../architecture/multi-cluster-v2.md)

