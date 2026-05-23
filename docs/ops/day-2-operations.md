# Day-2 Operations

This guide covers routine operation tasks after the initial installation.

## Secrets Management

- Apply or update secrets:

```bash
make secrets
```

- Rotate the Argo Events webhook secret:

```bash
make events-webhook-secret-rotate
```

Notes:
- Secret replication into `ci-*` namespaces may be performed by a replicator. If builds appear to mount “placeholder” data, see: [runbooks/secret-replication-issues.md](runbooks/secret-replication-issues.md).

## Viewing Pipeline Logs

- Show logs for the latest kpack build (requires `kp`):

```bash
make pipeline-logs APP_NAME=<app_name>
```

## Redeploying Templates and Config

- Re-apply pipeline templates and config:

```bash
make pipeline-deploy
```

When to use this:
- after editing workflow templates under `manifests/workflows/`
- after changing `manifests/config/*.yaml`

## Event Ingestion

- Deploy Argo Events resources:

```bash
make events-deploy
```

If events are not triggering workflows, see:
- [runbooks/webhook-not-triggering.md](runbooks/webhook-not-triggering.md)

## Local Cluster DNS (OrbStack)

If you are running locally and in-cluster components cannot resolve ingress-style domains:

```bash
make patch-coredns
```

See: [../guides/admin-guide.md](../guides/admin-guide.md)

