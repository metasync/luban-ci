#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/infra/apply_ci_infra_app.sh "$@"
