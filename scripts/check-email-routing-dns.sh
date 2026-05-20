#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-harmonia-community.com}"
DMARC="_dmarc.${DOMAIN}"

echo "== DNS check for ${DOMAIN} =="
echo

run_dig() {
  local type="$1"
  local name="$2"

  echo "$ dig ${type} ${name}"
  if command -v dig >/dev/null 2>&1; then
    dig "${type}" "${name}"
  else
    echo "dig not found"
  fi
  echo
}

run_nslookup() {
  local type="$1"
  local name="$2"

  echo "$ nslookup -type=${type} ${name}"
  if command -v nslookup >/dev/null 2>&1; then
    nslookup "-type=${type}" "${name}" || true
  else
    echo "nslookup not found"
  fi
  echo
}

run_dig MX "${DOMAIN}"
run_dig TXT "${DOMAIN}"
run_dig TXT "${DMARC}"

echo "== nslookup fallback =="
run_nslookup MX "${DOMAIN}"
run_nslookup TXT "${DOMAIN}"
run_nslookup TXT "${DMARC}"

cat <<'EOF'
== Expected for Cloudflare Email Routing ==
MX at the zone apex should route to Cloudflare mail exchangers:
  route1.mx.cloudflare.net
  route2.mx.cloudflare.net
  route3.mx.cloudflare.net

The apex SPF TXT should usually include Cloudflare's forwarding SPF:
  include:_spf.mx.cloudflare.net

If MX points to another provider, inbound mail reaches that provider first,
and Cloudflare Email Routing Activity Log may show no matching event.
EOF
