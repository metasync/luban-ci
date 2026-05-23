# Runbook: Git Auth Failing (Azure DevOps Server / On-Prem)

Symptoms:
- Workflow fails when cloning/pulling/pushing.
- Errors like `401`, `403`, `authentication failed`, or `fatal: could not read Username`.

## Quick Checks

1. Verify provider credentials Secret exists in the namespace where the workflow runs:

```bash
kubectl -n <namespace> get secret ado-creds -o yaml | head
```

2. Verify `luban-config` contains the correct ADO host keys:
- `ado_server`
- optional `ado_base_url`
- `ado_https_auth_mode` (commonly `extraheader_basic` for on-prem)
- `ado_basic_auth_username` (if required by your ADO configuration)

See: [../../guides/admin-guide.md](../../guides/admin-guide.md)

3. If using SSH clones, confirm the SSH secret and known_hosts exist and are non-placeholder.

## Common Root Causes

- `ado_server` does not match the host used in repo URLs (host mismatch breaks auth).
- HTTPS auth mode mismatch:
  - `credential_store`: relies on git credential helper
  - `extraheader_basic`: injects HTTP `Authorization` header
- Token lacks required scopes/permissions on the repo.

## Next Steps

- Update secrets via `make secrets`.
- Redeploy pipeline templates if config defaults were changed:

```bash
make pipeline-deploy
```

