#!/bin/sh

set -eu

exec sh /opt/luban/gitops-utils/scripts/kpack/apply_image_spec.sh "$@"
