# Private CA (On-Prem TLS)

Some enterprise/on-prem deployments use internal services (Azure DevOps Server, Harbor, asset mirrors, etc.) that are signed by a private CA. Luban CI supports this via an optional centralized CA bundle secret.

## How It Works

- You create `luban-ci/luban-ca-cert` containing a PEM CA bundle.
- That Secret is replicated automatically to matching namespaces (e.g. `ci-*`) via Mittwald replicator.
- Workflows that talk to on-prem services mount the CA bundle and set standard TLS env vars (only when the Secret exists).
- kpack builds mount the same Secret as a CNB Service Binding so buildpacks can download artifacts from internal HTTPS endpoints.
- This secret is intended for CI namespaces; application runtime namespaces should manage private CA trust separately.

## Setup

1. Put your PEM CA bundle in one of these:
   - `LUBAN_CA_CERT_PATH=/path/to/ca-bundle.pem`
   - `LUBAN_CA_CERT="-----BEGIN CERTIFICATE----- ..."`

2. Run:
   ```bash
   make secrets
   ```

This creates:
- `luban-ci/luban-ca-cert` (type `service.binding/ca-certificates`, key `ca.crt`)

## Standard Path Inside Containers

Workflows mount the Secret at:
- `/var/run/luban/ca/ca.crt`

The secret also carries helper keys used by workflows to set env vars (only when the Secret exists):
- `ssl_cert_file`
- `requests_ca_bundle`
- `git_ssl_cainfo`
- `curl_ca_bundle`

## Rotation

- Update the CA bundle and re-run `make secrets`.
- Restart any long-running pods that cache TLS state as needed (depends on the component).
