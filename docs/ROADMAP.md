# Luban CI Roadmap

This roadmap breaks down the implementation of `luban-ci` into iterative milestones. Phases marked **Completed** reflect the current state of this repository.

## Phase 1: Foundation - The Custom Stack (Completed)
**Goal:** Create and verify a base Amazon Linux stack (Build & Run images) that enforces non-root execution.

**Deliverables:**
- `stack/build/Dockerfile`: Amazon Linux-based build image with necessary build tools.
- `stack/run/Dockerfile`: Minimal Amazon Linux-based run image with non-root user configuration.
- `stack/stack.toml`: Configuration for the stack.

## Phase 2: The Python + `uv` Buildpack (Completed)
**Goal:** Detect Python apps, install Python via `uv`, and manage dependencies.

**Deliverables:**
- `buildpacks/python-uv/bin/detect`: Detects `uv.lock` or `.python-version`.
- `buildpacks/python-uv/bin/build`: Resolves Python version and installs dependencies with `uv`.
- `buildpacks/python-uv/buildpack.toml`: Buildpack metadata.

## Phase 3: Trusted Builder (Completed)
**Goal:** Combine the stack and buildpack into a distributable builder.

**Deliverables:**
- `builder/builder.toml`: Builder configuration.

## Phase 4: CI Pipeline - Build (kpack) (Completed)
**Goal:** Run Kubernetes-native builds using kpack.

**Deliverables:**
- `manifests/kpack/kpack-stack.yaml` and `manifests/kpack/kpack-builder.yaml`: kpack resources.
- `manifests/workflows/luban-ci-kpack-workflow-template.yaml`: CI build workflow that triggers and watches kpack builds.

## Phase 5: CI Pipeline - Trigger (Argo Events) (Completed)
**Goal:** Connect Git provider webhooks to the CI pipeline.

**Deliverables:**
- `events/*-event-source.yaml`: GitHub/Azure event sources.
- `events/*-sensor.yaml`: Sensors to trigger the dispatcher.

## Phase 6: CD Pipeline - Deploy (Argo CD) (Completed)
**Goal:** Update GitOps repos and let Argo CD deploy to `snd-*` namespaces.

**Deliverables:**
- GitOps repo update logic in `manifests/workflows/*gitops*` templates.

## Phase 7: Provisioning & Tooling Unification (Completed)
**Goal:** Consolidate provisioning into a single tool and simplify workflow templates.

**Deliverables:**
- `tools/luban-provisioner/`: Unified tool and Cookiecutter templates.
- Workflows use `{{workflow.parameters.luban_provisioner_image}}` and rely on the image entrypoint.

## Phase 8: Multi-Cluster & Infra Repos (Completed)
**Goal:** Split admin/control-plane vs runtime clusters and standardize infra repos.

**Deliverables:**
- Infra repo templates under `tools/luban-provisioner/templates/infra-*`.
- Workflows: `infra-repo-update-*` and `luban-infra-setup-*`.

## Phase 9: Dagster Data Platform Support (Completed)
**Goal:** Provision Dagster platforms and code locations using GitOps.

**Deliverables:**
- `manifests/workflows/luban-dagster-platform-setup-template.yaml`
- `manifests/workflows/luban-dagster-code-location-workflow-template.yaml`
- Dagster GitOps and source templates under `tools/luban-provisioner/templates/`.

## Phase 10: Secrets & Replication Standardization (Completed)
**Goal:** Provide a repeatable secrets flow with clear replication semantics.

**Deliverables:**
- `manifests/secrets/templates/*`: Declarative Secret templates.
- `manifests/secrets/setup-secrets.sh`: Renders/applies templates, creates dockerconfigjson/ssh-auth secrets, uses server-side apply, and strips `kubectl.kubernetes.io/last-applied-configuration` from Secrets.

## Backlog

### Tooling & CI
- Validate Cookiecutter templates by linting rendered output (render → `kustomize build` → `kubectl apply --dry-run`).
- Improve template editor linting by excluding `tools/luban-provisioner/templates/**` from strict Kubernetes schema checks.

### Security Hardening
- Tighten Argo CD `AppProject.namespaceResourceWhitelist` (inventory required resource kinds first).
- Consider making secret annotation cleanup best-effort (warn on failure) if RBAC is constrained.

### Secrets Roadmap
- Introduce per-environment secrets namespaces (for example `snd-secrets` / `prd-secrets`) and move source-of-truth runtime secrets out of `luban-ci`.
- Standardize an application runtime secret contract in app namespaces (for example `{{app}}-secret` with stable keys like `postgresql-password`) to keep workloads decoupled from the secret delivery mechanism.
- Update Dagster GitOps templates to stop committing any default secret payloads (for example remove/replace `dagster-postgresql-secret` data) and ensure a single GitOps owner produces the runtime Secret.
- Ensure Argo CD does not fight replicated/operator-managed secrets (ignore `/data` and `/stringData` diffs for replicated/runtime secrets).
- Evaluate External Secrets Operator (ESO) + Vault as the long-term secret delivery mechanism and define an ESO-ready shape (SecretStore/ClusterSecretStore, Vault auth/policy model, and secret path conventions).
- Plan and document a phased migration from replication-based secrets to ESO-produced secrets (swap producer while keeping the app secret contract stable).

### GitOps Operations
- Align auto-sync policy for infra Argo CD Applications (keep `prd` manual where applicable).

### Multi-Cluster & Isolation
- Add NetworkPolicies for namespace isolation where supported by the cluster CNI.
- Define a worker-cluster secret bootstrap strategy (replicator is cluster-local).
