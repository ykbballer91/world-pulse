#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${DOMAIN:-harmonia-community.com}"
CUSTOM_ADDRESS="${CUSTOM_ADDRESS:-info@harmonia-community.com}"
DESTINATION="${DESTINATION:-ykbballer91@gmail.com}"
API_BASE="${CLOUDFLARE_API_BASE:-https://api.cloudflare.com/client/v4}"

if [[ -z "${CF_API_TOKEN:-}" ]]; then
  cat >&2 <<'EOF'
CF_API_TOKEN is required.

Required token permissions should be read-only where possible:
  Zone:Read
  Account:Read
  Email Routing Rules:Read
  Email Routing Addresses:Read

Optional environment variables:
  DOMAIN=harmonia-community.com
  CUSTOM_ADDRESS=info@harmonia-community.com
  DESTINATION=ykbballer91@gmail.com
EOF
  exit 2
fi

api_get() {
  local path="$1"
  curl -fsS \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    "${API_BASE}${path}"
}

node_filter() {
  node -e '
const mode = process.argv[2];
let input = '';
process.stdin.setEncoding('utf8');
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
  const data = JSON.parse(input);
  if (!data.success) {
    console.error(JSON.stringify(data.errors || data, null, 2));
    process.exit(1);
  }
  const result = data.result;
  if (mode === 'zone') {
    const zone = Array.isArray(result) ? result[0] : result;
    if (!zone) process.exit(3);
    console.log(JSON.stringify({
      id: zone.id,
      name: zone.name,
      status: zone.status,
      account_id: zone.account && zone.account.id,
      account_name: zone.account && zone.account.name
    }, null, 2));
  } else if (mode === 'settings') {
    console.log(JSON.stringify(result, null, 2));
  } else if (mode === 'rules') {
    const customAddress = process.env.CUSTOM_ADDRESS.toLowerCase();
    const matching = result.filter(rule =>
      (rule.matchers || []).some(m =>
        m.type === 'literal' &&
        m.field === 'to' &&
        String(m.value || '').toLowerCase() === customAddress
      )
    );
    console.log(JSON.stringify({
      matching_count: matching.length,
      matching,
      drop_or_worker_rules: result.filter(rule =>
        (rule.actions || []).some(a => a.type === 'drop' || a.type === 'worker')
      )
    }, null, 2));
  } else if (mode === 'catch_all') {
    console.log(JSON.stringify(result, null, 2));
  } else if (mode === 'addresses') {
    const destination = process.env.DESTINATION.toLowerCase();
    const matching = result.filter(address =>
      String(address.email || '').toLowerCase() === destination
    );
    console.log(JSON.stringify({
      matching_count: matching.length,
      matching
    }, null, 2));
  }
});
' "$@"
}

echo "== Cloudflare zone =="
ZONE_JSON="$(api_get "/zones?name=${DOMAIN}&per_page=1")"
printf '%s' "${ZONE_JSON}" | node_filter zone
ZONE_ID="$(printf '%s' "${ZONE_JSON}" | node -e "let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>{const z=JSON.parse(s).result[0]; if(!z) process.exit(3); process.stdout.write(z.id);})")"
ACCOUNT_ID="$(printf '%s' "${ZONE_JSON}" | node -e "let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>{const z=JSON.parse(s).result[0]; if(!z || !z.account) process.exit(3); process.stdout.write(z.account.id);})")"
echo

echo "== Email Routing settings =="
api_get "/zones/${ZONE_ID}/email/routing" | node_filter settings
echo

echo "== Email Routing DNS requirements reported by Cloudflare =="
api_get "/zones/${ZONE_ID}/email/routing/dns" | node_filter settings
echo

echo "== Routing rules for ${CUSTOM_ADDRESS} and drop/worker rules =="
api_get "/zones/${ZONE_ID}/email/routing/rules?per_page=100" | node_filter rules
echo

echo "== Catch-all =="
api_get "/zones/${ZONE_ID}/email/routing/rules/catch_all" | node_filter catch_all
echo

echo "== Destination address ${DESTINATION} =="
api_get "/accounts/${ACCOUNT_ID}/email/routing/addresses?per_page=100" | node_filter addresses
