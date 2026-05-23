# Runbook: Webhook Not Triggering

Symptoms:
- A git push happens, but no workflow runs.
- Argo Events components appear deployed, but nothing triggers.

## Quick Checks

1. Verify Argo Events resources exist:

```bash
# Argo Events is commonly installed in `argo-events`
kubectl -n <argo_events_namespace> get eventbus
kubectl -n <argo_events_namespace> get eventsources
kubectl -n <argo_events_namespace> get sensors
```

2. Check Sensor status and recent errors:

```bash
kubectl -n <argo_events_namespace> describe sensor -l app=luban-ci
kubectl -n <argo_events_namespace> get events --sort-by=.metadata.creationTimestamp | tail -n 50
```

3. Verify webhook secret exists (and rotate if needed):

```bash
make events-webhook-secret
```

Rotate (forces regeneration):

```bash
make events-webhook-secret-rotate
```

## Gateway Reachability

Confirm the configured webhook URL matches the actual reachable endpoint:
- `manifests/config/luban-config.yaml` key: `webhook_url`
- If local dev, ensure DNS routing (OrbStack) is working; see `make patch-coredns` in [../../guides/admin-guide.md](../../guides/admin-guide.md)

### Local Development: Cloudflare Tunnel Relay

If you use a Cloudflare Tunnel to relay a public webhook URL into a local Kubernetes cluster, a stale tunnel process is a common failure mode (the public URL works, but it no longer forwards to the current local gateway/service IP).

Recommended steps:

1. Restart the Cloudflare tunnel service (`cloudflared`). In local development, the tunnel process can get stuck and may not recover without a restart.

```bash
kubectl -n <cloudflared_namespace> rollout restart deploy/cloudflared
```

2. If the tunnel is up but the forwarded destination changed (cluster restart, ingress IP change), re-run tunnel setup:

```bash
make tunnel-setup
```

## Next Steps

- If the gateway receives traffic but the Sensor does not trigger, inspect EventSource logs and Sensor logs.
- If the signature fails, re-check the secret on both the sender side and the gateway side and rotate if uncertain.
