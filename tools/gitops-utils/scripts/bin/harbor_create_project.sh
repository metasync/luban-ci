#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/harbor/create_project.sh "$@"

