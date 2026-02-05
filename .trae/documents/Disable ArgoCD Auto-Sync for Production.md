## Disable Auto-Sync for Production ArgoCD Applications

I will modify the `argocd-app-workflow-template.yaml` to conditionally disable the `automated` sync policy for the `prd` environment. 

### Technical Implementation:
1.  **Refactor `ensure-application` Template**:
    - Update the `create-app` step to calculate a new `sync_policy` parameter.
    - Use an Argo expression `{{= ... }}` to return a configuration object:
        - For `prd`: `{"syncOptions": ["CreateNamespace=true"]}` (Manual sync)
        - For others: `{"automated": {"prune": true, "selfHeal": true}, "syncOptions": ["CreateNamespace=true"]}` (Auto sync)
2.  **Update `create-app-resource` Template**:
    - Add `sync_policy` to the template inputs.
    - Inject the `sync_policy` directly into the ArgoCD Application manifest.

### Implementation Steps:
1.  Modify [argocd-app-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argocd-app-workflow-template.yaml).
2.  Deploy the updated template using `make pipeline-deploy`.
