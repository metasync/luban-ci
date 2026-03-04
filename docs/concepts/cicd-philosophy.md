# CI/CD Philosophy

Luban CI follows a **Trunk-Based Development** model with **Promotion-Based Releases**.

## Development & Release Model

### 1. Development (Continuous Integration)
- **Trigger**: Commit to any branch (e.g., `main`, `feat/login`).
- **Action**:
  1.  **Dispatch**: The `luban-ci` dispatcher triggers a pipeline in the project's Sandbox namespace (`snd-<project>`).
  2.  **Build**: kpack builds the container image in Sandbox.
  3.  **Deploy**: The pipeline updates the **Sandbox** overlay (`app/overlays/snd`) in the `develop` branch of the GitOps repository.
  4.  **Verify**: The application is deployed to the Sandbox cluster for verification.

### 2. Release (Continuous Delivery)
- **Trigger**: Git Tag (e.g., `v1.0.0`) OR Manual Promotion.
- **Action**:
  1.  **Build**: Tags are also built and deployed to **Sandbox** first to ensure the exact artifact is verified.
  2.  **Promote**: A separate **Promotion Workflow** is triggered (manually or via automation).
  3.  **Deploy**: The Promotion Workflow:
      - Reads the verified image tag from the Sandbox environment.
      - Updates the **Production** overlay in the GitOps repository.
      - Creates a Pull Request (or auto-merges) to apply changes to Production.

## Why this model?
- **Build Once, Deploy Many**: The exact image tested in Sandbox is promoted to Production. We do not rebuild for Production.
- **Isolation**: Heavy build workloads run only in Sandbox/CI namespaces, keeping Production clusters stable and clean.
- **Safety**: Production deployments are explicit promotion actions, not side-effects of a merge.
