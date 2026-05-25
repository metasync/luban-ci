#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/argo/dispatch_ci_pipeline.sh "$@"

