# Runbook: Secret Replication Issues

Symptoms:
- Workflow expects a Secret but sees placeholder data.
- kpack service bindings do not appear in builds even though secrets exist in `luban-ci`.
- CI namespaces (`ci-*`) contain stub secrets but not real data.

## Quick Checks

1. Check the Secret in the target namespace:

```bash
kubectl -n <namespace> get secret <name> -o jsonpath='{.data}' ; echo
```

2. For known “placeholder” patterns, verify data is not placeholder:
- some workflows treat base64 `cGxhY2Vob2xkZXI=` as placeholder

3. Confirm the source Secret exists in `luban-ci` (or the expected source namespace):

```bash
kubectl -n luban-ci get secret <name>
```

## Common Root Causes

- Secret replicator is not installed or not configured for the destination namespace.
- Replicator permissions are missing (cannot read source or write destination).
- Replicator created destination Secret object, but `.data` is not populated yet.

## Next Steps

- Fix replicator installation/configuration.
- Re-apply secrets after correcting configuration:

```bash
make secrets
```

- If the workflow is expected to conditionally mount service bindings, re-run the workflow after the destination Secret contains real data.

