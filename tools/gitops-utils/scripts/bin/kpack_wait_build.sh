#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/kpack/wait_build.sh "$@"
