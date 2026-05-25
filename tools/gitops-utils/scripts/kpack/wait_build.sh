#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "${SCRIPT_DIR}/../lib/common.sh"
. "${SCRIPT_DIR}/../lib/kube.sh"

cleanup() {
  if [ -n "${KP_LOGS_PID:-}" ]; then
    kill "$KP_LOGS_PID" 2>/dev/null || true
  fi
}

wait_for_build_ref() {
  build_ref=""
  build_rev=""
  last_log_ts=0
  start_ts=$(date +%s)
  timeout_seconds=600

  while true; do
    build_ref=$($KUBECTL -n "$TARGET_NAMESPACE" get image "$APP_NAME" -o jsonpath='{.status.latestBuildRef.name}' 2>/dev/null || true)
    if [ -z "$build_ref" ]; then
      build_ref=$($KUBECTL -n "$TARGET_NAMESPACE" get image "$APP_NAME" -o jsonpath='{.status.latestBuildRef}' 2>/dev/null || true)
    fi

    if [ -n "$build_ref" ]; then
      build_rev=$($KUBECTL -n "$TARGET_NAMESPACE" get build "$build_ref" -o jsonpath='{.spec.source.git.revision}' 2>/dev/null || true)
      if [ "$build_rev" = "$REVISION" ]; then
        BUILD_REF=$build_ref
        return
      fi
    fi

    now_ts=$(date +%s)
    elapsed=$((now_ts - start_ts))
    if [ $((now_ts - last_log_ts)) -ge 60 ]; then
      if [ -n "$build_ref" ] && [ -n "$build_rev" ] && [ "$build_rev" != "$REVISION" ]; then
        echo "Waiting for kpack build for revision ${REVISION}... current latestBuildRef=${build_ref} (rev=${build_rev})"
      else
        echo "Waiting for kpack BuildRef... (${elapsed}s, target namespace: ${TARGET_NAMESPACE})"
      fi
      last_log_ts=$now_ts
    fi

    if [ "$elapsed" -ge "$timeout_seconds" ]; then
      break
    fi
    sleep 2
  done

  if [ -z "$build_ref" ]; then
    echo "Error: kpack did not create a build for Image/$APP_NAME within timeout (${timeout_seconds}s)." >&2
  else
    echo "Error: kpack did not create a build for revision ${REVISION} within timeout (${timeout_seconds}s)." >&2
  fi
  kubectl -n "$TARGET_NAMESPACE" get image "$APP_NAME" -o yaml || true
  exit 1
}

wait_for_build_completion() {
  echo "Build created: $BUILD_REF"
  kp build logs "$APP_NAME" -n "$TARGET_NAMESPACE" &
  KP_LOGS_PID=$!

  echo "Waiting for kpack build to complete..."
  start_ts=$(date +%s)
  timeout_seconds=3600

  while true; do
    build_status=$($KUBECTL -n "$TARGET_NAMESPACE" get build "$BUILD_REF" -o jsonpath='{.status.conditions[?(@.type=="Succeeded")].status}' 2>/dev/null || true)
    build_reason=$($KUBECTL -n "$TARGET_NAMESPACE" get build "$BUILD_REF" -o jsonpath='{.status.conditions[?(@.type=="Succeeded")].reason}' 2>/dev/null || true)

    if [ "$build_status" = "True" ]; then
      echo "Build succeeded."
      return
    fi

    if [ "$build_status" = "False" ]; then
      echo "Build failed (${build_reason:-unknown})." >&2
      kubectl -n "$TARGET_NAMESPACE" get build "$BUILD_REF" -o yaml || true
      exit 1
    fi

    now_ts=$(date +%s)
    elapsed=$((now_ts - start_ts))
    if [ "$elapsed" -ge "$timeout_seconds" ]; then
      echo "Error: kpack build did not complete within timeout (${timeout_seconds}s): $BUILD_REF" >&2
      kubectl -n "$TARGET_NAMESPACE" get build "$BUILD_REF" -o yaml || true
      exit 1
    fi

    sleep 2
  done
}

trap cleanup EXIT INT TERM

require_env REGISTRY_NAMESPACE
require_env APP_NAME
require_env REVISION
require_env KUBERNETES_SERVICE_HOST
require_env KUBERNETES_SERVICE_PORT

configure_incluster_kubeconfig

KUBECTL='kubectl --request-timeout=5s'
TARGET_NAMESPACE="ci-${REGISTRY_NAMESPACE}"
BUILD_REF=""

wait_for_build_ref
wait_for_build_completion
