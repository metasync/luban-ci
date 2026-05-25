#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/argocd/apply_application.sh "$@"
