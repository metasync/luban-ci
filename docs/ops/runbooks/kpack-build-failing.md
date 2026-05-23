# Runbook: kpack Build Failing

Symptoms:
- Workflow runs but build never becomes ready.
- `kp build logs` shows lifecycle/buildpack failures.
- Image resource exists but Build fails or is not created.

## Quick Checks

1. Verify kpack objects exist:

```bash
kubectl get clusterstack
kubectl get clusterbuilder
kubectl get clusterlifecycle
```

2. Check the Image and Build objects (namespace matters):

```bash
kubectl -n <target_namespace> get image
kubectl -n <target_namespace> get build
kubectl -n <target_namespace> describe build <build_name>
```

3. Inspect logs (requires `kp`):

```bash
kp build logs <image_name> -n <target_namespace>
```

## Common Causes

- Registry credentials missing or wrong (`image_pull_secret`, registry secrets).
- Builder/stack not present or incompatible.
- Missing network access (air-gapped clusters) without configured mirrors:
  - `uv_release_base_url`
  - `uv_python_install_mirror`
  See: [../../guides/admin-guide.md](../../guides/admin-guide.md)
- Private CA required but not injected (Harbor/on-prem endpoints):
  - See: [../../guides/private-ca.md](../../guides/private-ca.md)

## Next Steps

- Confirm the workflow applied the expected Image spec and that it matches your builder/stack.
- If the build needs a service binding (netrc/CA cert), confirm the Secret exists and is not a placeholder; see: [secret-replication-issues.md](secret-replication-issues.md)

