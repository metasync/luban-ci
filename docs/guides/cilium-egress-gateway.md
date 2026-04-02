# Cilium Egress Gateway for CI Namespaces

This guide describes how Luban can integrate with a shared `CiliumEgressGatewayPolicy` so that all `ci-*` namespaces egress via a controlled set of static IPs.

## Overview

- The cluster admin provisions a cluster-scoped `CiliumEgressGatewayPolicy` that selects CI workloads by **namespace label**.
- Luban labels each newly created `ci-<project>` namespace at creation time via Argo CD `managedNamespaceMetadata`.
- The setup is opt-in. If the Luban config key is unset, nothing changes.

## Luban Configuration

Set this key in `ConfigMap/luban-config`:

- `cilium_egress_gateway_policy`: name of the shared `CiliumEgressGatewayPolicy`.

When non-empty, Luban adds a label to each newly created CI namespace:

- Label key: `luban-ci.io/cilium-egress-gateway-policy`
- Label value: the policy name from `cilium_egress_gateway_policy`

## Argo CD Namespace Labeling

Luban creates the CI infra Argo CD Application with `CreateNamespace=true`. When `cilium_egress_gateway_policy` is set, the generated Application includes:

```yaml
spec:
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
    managedNamespaceMetadata:
      labels:
        luban-ci.io/cilium-egress-gateway-policy: "<policy-name>"
```

This ensures the namespace is labeled at creation time and stays reconciled by Argo CD.

## Sample `CiliumEgressGatewayPolicy`

The policy is cluster-scoped (`apiVersion: cilium.io/v2`, `kind: CiliumEgressGatewayPolicy`) and should select namespaces by the label above.

Example (route all external traffic via a gateway node and egress IP):

```yaml
apiVersion: cilium.io/v2
kind: CiliumEgressGatewayPolicy
metadata:
  name: luban-ci-egress
spec:
  selectors:
    - namespaceSelector:
        matchLabels:
          luban-ci.io/cilium-egress-gateway-policy: luban-ci-egress
      podSelector:
        matchExpressions:
          - key: not-existing
            operator: NotIn
            values: [not-existing]

  destinationCIDRs:
    - "0.0.0.0/0"

  egressGateway:
    nodeSelector:
      matchLabels:
        egress-gateway: "true"
    egressIP: 10.0.1.100
```

Notes:

- The `podSelector` uses a common "match all pods" trick. If you prefer selecting only specific pods, use explicit labels.
- Set `destinationCIDRs`/`excludedCIDRs` based on your environment. Be careful with `0.0.0.0/0` and exclude cluster-internal ranges as needed.

## Operational Notes

- The admin must ensure gateway nodes and `egressIP` are correctly provisioned for the cluster.
- This design avoids patching the `CiliumEgressGatewayPolicy` on each project creation; it only labels namespaces.
