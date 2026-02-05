## Optimize Workflow Performance while Maintaining Readability

I will refactor the workflow to eliminate pod overhead by moving simple logic into centralized, declarative expressions at the template entrypoints.

### Technical Implementation:
1.  **Centralize Derived Parameters**: In each main template (e.g., `ci-pipeline`, `create-applications`), I will move the logic from `gitops-helper-template` into `inputs.parameters` using Argo expressions.
2.  **Simplify Steps**: Refactor the steps to use these pre-calculated parameters, removing the intermediate `determine-*` pod steps.
3.  **Templates to Refactor**:
    - [argocd-app-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argocd-app-workflow-template.yaml)
    - [argocd-project-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/argocd-project-workflow-template.yaml)
    - [luban-app-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/luban-app-workflow-template.yaml)
    - [luban-ci-kpack-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/luban-ci-kpack-workflow-template.yaml)
4.  **Cleanup**: Delete [gitops-helper-workflow-template.yaml](file:///Users/chi/Workspace/projects/luban/luban-ci/manifests/gitops-helper-workflow-template.yaml) and update deployment scripts.

### Implementation Steps:
1.  Update each template sequentially, ensuring derived parameters are clearly defined and commented.
2.  Verify the logic of each expression (e.g., URL construction, Org determination).
3.  Delete the helper template file.
4.  Deploy all changes using `make pipeline-deploy`.
