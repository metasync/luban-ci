# Runbook: `templateRef` Volume Not Found

Symptoms:
- Workflow submission fails fast with errors like:
  - `volume '<name>' not found in workflow spec`

## Explanation

When a workflow uses `templateRef` to execute a template from a `WorkflowTemplate` or `ClusterWorkflowTemplate`, the referenced template may include `volumeMounts`. If the volume is not defined in the instantiated workflow spec, validation fails.

In practice, to make a referenced template self-contained, declare `volumes:` at the template level (the same level as `container:` / `script:`), not only at the parent spec level.

## Quick Fix Pattern

1. Find the template that has `volumeMounts` referencing the missing volume.
2. Add a `volumes:` block to that template.
3. Re-apply templates:

```bash
make pipeline-deploy
```

## Related Guides

- Private CA handling: [../../guides/private-ca.md](../../guides/private-ca.md)
- Admin/config reference: [../../guides/admin-guide.md](../../guides/admin-guide.md)

