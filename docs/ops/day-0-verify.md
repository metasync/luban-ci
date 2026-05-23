# Day-0 Verification

This guide provides quick health checks after installation.

## Verify Core Resources Exist

```bash
kubectl get clusterrole luban-view-templates
kubectl get clusterrolebinding luban-view-templates-binding
```

```bash
kubectl -n luban-ci get sa workflow-runner
kubectl -n luban-ci get configmap luban-config
```

## Verify Workflow Templates Are Installed

List templates in `luban-ci`:

```bash
kubectl -n luban-ci get workflowtemplates
```

List cluster-scoped templates:

```bash
kubectl get clusterworkflowtemplates | grep luban
```

## Verify kpack Is Ready

```bash
kubectl get clusterstack
kubectl get clusterbuilder
kubectl get clusterlifecycle
```

If you have `kp` installed:

```bash
kp version
```

## Verify Argo Events (if installed)

Argo Events is commonly installed in `argo-events`, but your cluster may use a different namespace.

```bash
kubectl -n <argo_events_namespace> get eventbus
kubectl -n <argo_events_namespace> get eventsources
kubectl -n <argo_events_namespace> get sensors
```

## Smoke Test: Trigger a Workflow

If you have the test harness configured, run:

```bash
make test-ci-pipeline
```

Then check the latest workflows:

```bash
kubectl -n luban-ci get wf --sort-by=.metadata.creationTimestamp | tail -n 10
```

If the workflow uses kpack and you know the app name:

```bash
make pipeline-logs APP_NAME=<app_name>
```

## If Something Fails

Start with runbooks:

- [runbooks/webhook-not-triggering.md](runbooks/webhook-not-triggering.md)
- [runbooks/kpack-build-failing.md](runbooks/kpack-build-failing.md)
- [runbooks/templateRef-volume-not-found.md](runbooks/templateRef-volume-not-found.md)
