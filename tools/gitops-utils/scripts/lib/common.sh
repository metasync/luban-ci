die() {
  echo "$1" >&2
  exit 1
}

require_env() {
  var_name=$1
  eval "var_value=\${$var_name-}"
  if [ -z "$var_value" ]; then
    die "Error: ${var_name} is required"
  fi
}

has_cntrl() {
  printf '%s' "$1" | LC_ALL=C grep -q '[[:cntrl:]]'
}

require_no_cntrl() {
  name=$1
  value=$2
  if has_cntrl "$value"; then
    die "Error: ${name} contains control characters"
  fi
}

require_dns_label() {
  name=$1
  value=$2
  printf '%s' "$value" | grep -Eq '^[a-z0-9]([-a-z0-9]*[a-z0-9])?$' || die "Error: ${name} is not a valid DNS label: ${value}"
}

require_hex_rev() {
  name=$1
  value=$2
  printf '%s' "$value" | grep -Eq '^[0-9a-f]{7,40}$' || die "Error: ${name} is not a valid git revision: ${value}"
}

require_image_tag() {
  name=$1
  value=$2
  printf '%s' "$value" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$' || die "Error: ${name} is not a valid image tag: ${value}"
}

require_group_name() {
  name=$1
  value=$2
  if [ -z "$value" ]; then
    return 0
  fi
  printf '%s' "$value" | grep -Eq '^[A-Za-z0-9][A-Za-z0-9:._/@+-]{0,127}$' || die "Error: ${name} is not a valid group name: ${value}"
}
