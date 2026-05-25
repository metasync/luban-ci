#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/infra/apply_namespace_infra_app.sh "$@"
