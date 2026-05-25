configure_incluster_kubeconfig() {
  mkdir -p "${HOME}/.kube"
  kubectl config set-cluster local \
    --server="https://${KUBERNETES_SERVICE_HOST}:${KUBERNETES_SERVICE_PORT}" \
    --certificate-authority=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt >/dev/null
  kubectl config set-credentials luban \
    --token="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" >/dev/null
  sa_namespace=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
  kubectl config set-context local \
    --cluster=local \
    --user=luban \
    --namespace="${sa_namespace}" >/dev/null
  kubectl config use-context local >/dev/null
}
