## Refactor ArgoCD Application Creation for Better Readability

I will refactor the `argocd-app-workflow-template.yaml` to improve the readability of the conditional `syncPolicy`. Instead of using a complex JSON-in-string expression, I will use specialized templates for each synchronization strategy.

### Technical Implementation:
1.  **Split Resource Templates**:
    - Create `create-app-resource-auto`: A clean, dedicated template for environments with automatic synchronization (like `snd`).
    - Create `create-app-resource-manual`: A dedicated template for production (`prd`) with manual synchronization.
2.  **Conditional Step Selection**:
    - Update the `ensure-application` steps to choose between these templates using clear, readable `when` expressions.
    - This eliminates the need for escaping JSON strings and makes the target manifests much easier to inspect.

### Implementation Steps:
1.  Modify [argocd-app-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argocd-app-workflow-template.yaml):
    - Refactor `ensure-application` to call specialized templates.
    - Define `create-app-resource-auto` and `create-app-resource-manual`.
2.  Deploy the updated template using `make pipeline-deploy`.

This approach provides the most "natural" reading experience as the actual Kubernetes manifest for each case is clearly visible without any logic obfuscating the structure.
