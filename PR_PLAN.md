# PR Plan (Temporary)

This document tracks a proposed multi-PR refactor/documentation effort for `luban-ci`. It is intentionally temporary and can be removed once the work is complete.

## Goals

- Improve readability by reducing large inline shell blocks in Argo workflow templates.
- Improve maintainability via clearer separation of concerns (Makefiles and Python tooling).
- Reduce unnecessary runtime overhead (especially Kubernetes API polling from workflows).
- Align documentation with how the repo is actually deployed/operated (DevOps-first).

## Proposed PR Sequence

### PR 1 — DevOps Docs: Day-0/Day-2 + Runbooks

**Intent**
- Make the repo operable from documentation alone; treat Make targets as the “operator API”.

**Changes**
- Add:
  - `docs/ops/README.md` (operator landing page: scope, boundaries, supported modes)
  - `docs/ops/day-0-install.md` (prereqs → secrets → image publish → deploy)
  - `docs/ops/day-0-verify.md` (copy/paste health checks + “hello world” run)
  - `docs/ops/day-2-operations.md` (rotation/logs/concurrency/cleanup)
  - `docs/ops/upgrades.md` (safe upgrade + rollback for workflows/config/builder/stack/buildpack)
  - `docs/ops/runbooks/`:
    - `webhook-not-triggering.md`
    - `kpack-build-failing.md`
    - `git-auth-failing-ado.md`
    - `secret-replication-issues.md`
    - `templateRef-volume-not-found.md`
  - `docs/reference/make-targets.md` (curated “operator API” reference)
- Update `README.md` to link DevOps docs first (and make the ops path explicit).

**Acceptance criteria**
- A DevOps engineer can: install → verify → trigger a test workflow → troubleshoot common failures without reading code.

**Risk**
- Low (docs-only).

---

### PR 2 — Deploy Ergonomics: Makefile Target Decomposition + Verification

**Intent**
- Make deployments composable and safer by decomposing `deploy` into smaller targets and adding verification.

**Changes**
- Refactor `manifests/Makefile` into explicit targets:
  - `deploy-rbac`
  - `deploy-kpack`
  - `deploy-global-argo-config`
  - `deploy-config`
  - `deploy-workflows`
  - `verify` (fast sanity checks; minimal output; non-zero on failure)
  - keep `deploy` as the orchestrator of the above
- Add root-level shortcuts:
  - `make pipeline-verify` → runs manifest verification
  - `make events-verify` (if feasible) → checks EventBus/Sensor health

**Acceptance criteria**
- Existing `make pipeline-deploy` continues to work.
- Operators can run narrower targets and a standard `verify` step.

**Risk**
- Low/medium (touches deployment flow; keep backwards compatibility).

---

### PR 3 — Workflow Reliability: Extract Inline Shell into Tooling Scripts

**Intent**
- Reduce YAML/shell fragility and make workflow logic testable and reusable.

**Changes**
- Add versioned scripts into an existing tooling image (prefer `tools/gitops-utils` if it is the standard runtime):
  - `kpack_apply_image_spec.sh` (generate/apply `/tmp/kpack-image.yaml` safely)
  - `kpack_wait_build.sh` (prefer `kubectl wait`; otherwise backoff polling)
  - `gitops_update_repo.sh` (update overlays, commit/push)
- Update workflow templates to invoke scripts with args instead of embedding large shell programs:
  - `manifests/workflows/luban-ci-kpack-workflow-template.yaml`
  - scan other `manifests/workflows/*.yaml` for similar patterns
- Add lightweight script checks where possible (e.g., `shellcheck`) and document them.

**Acceptance criteria**
- Workflow behavior remains functionally equivalent (same inputs/outputs).
- Reduced risk of indentation/quoting issues; less Kubernetes API polling overhead.

**Risk**
- Medium (runtime behavior changes; mitigate with careful equivalence + debug/dry-run options).

---

### PR 4 — luban-provisioner Maintainability: Module Split + Shared CLI Helpers

**Intent**
- Reduce coupling and duplication in the Python CLI tooling.

**Changes**
- Split `tools/luban-provisioner/.../utils.py` into cohesive modules, for example:
  - `git.py`, `config.py`, `templates.py`, `retry.py` (names to match repo conventions)
- Add shared CLI scaffolding helpers (e.g. `cli_common.py`) to dedupe repeated patterns across commands.
- Narrow or gate global warning suppression in `tools/luban-provisioner/.../main.py`.
- Remove or hard-fail deprecated no-op functions (based on whether external callers exist).

**Acceptance criteria**
- `make lint` / `make format` remain green.
- CLI behavior unchanged (flags/env vars/outputs).

**Risk**
- Medium (refactor; mitigate with incremental refactor and targeted verification).

## Suggested Merge Order

- PR 1 (docs) → PR 2 (deploy/verify) → PR 3 (workflows/scripts) → PR 4 (provisioner refactor)

