#!/usr/bin/env sh
set -eu

API_URL="${API_URL:-http://localhost:8000}"

failed=0
sensitive_matches=""

section() {
  printf '\n## %s\n\n' "$1"
}

code_block() {
  printf '```%s\n' "${1:-text}"
}

end_code_block() {
  printf '```\n'
}

run_capture() {
  title="$1"
  shift
  printf '### %s\n\n' "$title"
  code_block text
  if "$@" 2>&1; then
    :
  else
    status=$?
    printf '\n(command exited with status %s)\n' "$status"
  fi
  end_code_block
  printf '\n'
}

fetch_endpoint() {
  endpoint="$1"
  printf '### GET %s\n\n' "$endpoint"
  code_block json
  if curl -fsS "$API_URL$endpoint" 2>&1; then
    printf '\n'
  else
    status=$?
    failed=1
    printf '\nERROR: request failed with status %s\n' "$status"
  fi
  end_code_block
  printf '\n'
}

scan_sensitive_patterns() {
  if ! command -v git >/dev/null 2>&1; then
    printf 'git not available; tracked-source sensitive scan was not executed.\n'
    return 0
  fi

  sensitive_matches="$(
    git grep -n -E \
      -e 'BINANCE_API_KEY[[:space:]]*=' \
      -e 'BINANCE_API_SECRET[[:space:]]*=' \
      -e 'https://api\.binance\.com' \
      -e 'AURUM_ENVIRONMENT[[:space:]]*=[[:space:]]*mainnet' \
      -e 'LEVERAGE[[:space:]]*=' \
      -- \
      ':(exclude)*.md' \
      ':(exclude)package-lock.json' \
      ':(exclude)scripts/collect-testnet-evidence.sh' || true
  )"

  if [ -n "$sensitive_matches" ]; then
    printf '%s\n' "$sensitive_matches"
    failed=1
  else
    printf 'No sensitive Mainnet, leverage, or Binance credential patterns found in tracked source scan.\n'
  fi
}

printf '# Aurum Testnet evidence\n\n'
printf '%s\n' "- API_URL: \`$API_URL\`"
printf '%s\n' "- Collected at UTC: \`$(date -u '+%Y-%m-%dT%H:%M:%SZ')\`"

section "Git state"
run_capture "git status --short" git status --short

section "Docker Compose"
run_capture "docker compose ps" docker compose ps

section "Read-only API evidence"
fetch_endpoint "/health"
fetch_endpoint "/bot/status"
fetch_endpoint "/market/summary"
fetch_endpoint "/market/candles?interval=1h&limit=5"
fetch_endpoint "/decisions?limit=5"
fetch_endpoint "/mcp/status"
fetch_endpoint "/mcp/audit-log?limit=5"

section "Scope and secret scan"
code_block text
scan_sensitive_patterns
end_code_block

section "Manual follow-up"
printf -- '- Review database evidence for `market_candles`, `bot_runs`, `decision_logs`, `audit_logs`, and `mcp_access_logs` using `docs/runbooks/testnet-validation-checklist.md`.\n'
printf -- '- If worker validation is required, run it manually after prerequisites are ready; this script intentionally does not run the worker.\n'

exit "$failed"
