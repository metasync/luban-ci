# Environment Promotion

Luban CI enforces a strict separation between environments and uses a "Build Once, Promote Anywhere" strategy.

## Environment Mapping

- **Sandbox (`snd`)**:
  - The default build and deployment environment.
  - **All** CI pipelines (from `main` branch, feature branches, or tags) run in the `snd-<project>` namespace.
  - Automatically deploys to the `snd` environment overlay.
  - Used for integration testing and validation.

- **Production (`prd`)**:
  - The release environment.
  - **No** CI builds occur directly in Production namespaces.
  - Deploys happen via **Promotion** (updating the `main` branch with the verified image tag from `snd`).

## Promotion Workflow

To promote an application from `snd` to `prd`, use the `luban-promotion-template`. This workflow leverages the [GitOps Branching Strategy](gitops-architecture.md#gitops-branching-strategy) (`develop` -> `main`).

- **Workflow**: `luban-promotion-template`
- **Parameters**:
  - `project_name`: (Required) Name of the project.
  - `app_name`: (Required) Name of the application.
  - `git_organization`: (Optional) Auto-detected if not provided.
  - `git_provider`: (Optional) `github` (default) or `gitlab`.

This workflow:
1.  Extracts the currently deployed image tag from the **Sandbox** overlay.
2.  Updates the **Production** overlay with that tag.
3.  Creates a Pull Request (or commits directly) to the GitOps repository to apply the change.

> **Note**: This ensures that only artifacts that have been successfully deployed and verified in Sandbox can be promoted to Production.
