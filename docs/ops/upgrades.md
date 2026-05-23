# Upgrades and Rollbacks

This guide describes an operator-oriented approach to upgrading Luban CI components managed by this repo.

## What Usually Changes

- Workflow templates: `manifests/workflows/`
- ConfigMaps: `manifests/config/`
- kpack objects (stack/builder/lifecycle): `manifests/kpack/`, plus images under `stack/`, `builder/`, `buildpacks/`
- Tooling images: `tools/`
- Argo Events resources: `events/`

## Standard Upgrade Flow

1. Update secrets if needed:

```bash
make secrets
```

2. Publish images if you changed them (stack/builder/buildpack/tools):

```bash
make stack-push
make buildpack-package
make builder-push
make tools-image-push
```

3. Apply pipeline changes (RBAC/config/kpack objects/templates):

```bash
make pipeline-deploy
```

4. Apply events changes (if relevant):

```bash
make events-deploy
```

5. Verify:

- Use: [day-0-verify.md](day-0-verify.md)

## Tooling Upgrades (gitops-utils / luban-provisioner)

Luban workflows typically run with tool images referenced from `luban-config` (for example `gitops_utils_image`, `luban_provisioner_image`).

Recommended procedure:

1. Build and push the new tooling images:

```bash
make tools-image-push
```

2. Update the `luban-config` ConfigMap to point to the new image tags/digests.

3. Re-apply pipeline config and templates:

```bash
make pipeline-deploy
```

Notes:
- Prefer immutable tags or digests for tooling images to avoid accidental drift.
- If you upgraded the provisioner but existing workflow templates still reference older behavior/flags, upgrade templates in the same change.

## Buildpack / Builder Upgrades (python-uv)

Upgrading the `python-uv` buildpack and ensuring kpack uses the new buildpack is usually a multi-step change, because it involves both:
- publishing a new buildpack package image
- updating the kpack `ClusterBuilder` configuration to reference that package (directly or via a builder image rebuild, depending on how your builder is constructed)
and may also require a stack upgrade if the new buildpack/runtime expects different OS libraries or base image behavior (build/run images).

Recommended procedure:

1. Package and publish the buildpack:

```bash
make buildpack-package
```

2. Publish the builder:

```bash
make builder-push
```

3. If the upgrade includes stack changes, publish stack images:

```bash
make stack-push
```

4. Apply the updated kpack objects:

```bash
make pipeline-deploy
```

This step applies the kpack manifests from `manifests/kpack/` (lifecycle, stack, builder) via `manifests/Makefile`.

5. Verify the cluster builder state and do a test build:

- Use: [day-0-verify.md](day-0-verify.md)

Notes:
- Treat buildpack+builder upgrades as higher-risk than workflow template changes because they can change build behavior across all projects.
- If you maintain air-gapped mirrors (uv/Python), verify mirror settings and CA injection still work after the upgrade; see: [../guides/admin-guide.md](../guides/admin-guide.md) and [../guides/private-ca.md](../guides/private-ca.md).

## Rollback Strategy (Practical)

The simplest rollback path is to revert to a known-good git revision of this repo and re-apply manifests.

1. Checkout the known-good revision locally.
2. Re-apply:

```bash
make pipeline-deploy
make events-deploy
```

3. If a webhook secret rotation caused issues, re-run:

```bash
make events-webhook-secret
```

## Notes on kpack Lifecycle Pinning

The kpack lifecycle image is pinned by digest in `manifests/kpack/kpack-lifecycle.yaml`. If your cluster cannot reach upstream registries reliably, mirror the lifecycle image into your registry and keep it pinned by digest.

See: [../guides/admin-guide.md](../guides/admin-guide.md)
