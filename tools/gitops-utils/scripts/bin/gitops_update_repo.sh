#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/gitops/update_repo.sh "$@"
