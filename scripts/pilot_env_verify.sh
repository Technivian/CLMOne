#!/usr/bin/env bash
# Clean-state controlled-pilot environment verification / bootstrap.
# Does not use remote DATABASE_URL / REDIS_URL from .env.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

EVIDENCE_DIR="${PILOT_EVIDENCE_DIR:-$ROOT_DIR/docs/audits/evidence/2026-07-20-pilot-verification}"
mkdir -p "$EVIDENCE_DIR"
LOG="$EVIDENCE_DIR/pilot-env-setup.log"
: > "$LOG"

exec > >(tee -a "$LOG") 2>&1

echo "=== Pilot environment clean-state verification ==="
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

PY="$ROOT_DIR/.venv/bin/python"
DB_PATH="${PILOT_DB_PATH:-/tmp/clmone-pilot-env-verify.sqlite3}"
REDIS_URL_LOCAL="${PILOT_REDIS_URL:-redis://127.0.0.1:6379/14}"

rm -f "$DB_PATH"

if ! command -v redis-cli >/dev/null 2>&1; then
  echo "FAIL: redis-cli missing"
  exit 2
fi
redis-cli ping | grep -q PONG
redis-cli -n 14 FLUSHDB >/dev/null || true

export DATABASE_URL="sqlite:///$DB_PATH"
export REDIS_URL="$REDIS_URL_LOCAL"
export DJANGO_SETTINGS_MODULE=config.settings_development
export DJANGO_DEBUG=false
export LOGIN_RATE_LIMIT_REQUESTS=3
export LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
export RATELIMIT_ENABLED=true
export RATELIMIT_TRUSTED_IPS=
export CONTROLLED_PILOT_ENABLED=true
export GEMINI_AI_ENABLED=false
export GEMINI_API_KEY=
export BILLING_SELF_SERVE_ENABLED=false
export TRUST_ACCOUNTING_ENABLED=false

echo "--- migrate ---"
"$PY" manage.py migrate --noinput

echo "--- seed controlled pilot ---"
"$PY" manage.py seed_controlled_pilot --reset-samples

echo "--- feature flags ---"
"$PY" manage.py shell <<'PY'
from contracts.services.pilot_monitoring import pilot_feature_flag_state
from contracts.services.finance_approval_policy import get_finance_approval_threshold
print(pilot_feature_flag_state())
print('finance_threshold=', get_finance_approval_threshold())
PY

echo "--- health: redis ---"
redis-cli -n 14 PING

echo "--- redis rate-limit script ---"
"$PY" scripts/verify_redis_login_rate_limit.py

echo "--- health: django check ---"
"$PY" manage.py check

echo "--- pilot daily health (baseline empty day) ---"
"$PY" manage.py pilot_daily_health --output "$EVIDENCE_DIR/pilot-daily-health-sample.json"

echo "=== PASS: pilot environment clean-state verification complete ==="
echo "db=$DB_PATH"
echo "redis=$REDIS_URL_LOCAL"
echo "flags: CONTROLLED_PILOT_ENABLED=true GEMINI_AI_ENABLED=false BILLING_SELF_SERVE_ENABLED=false TRUST_ACCOUNTING_ENABLED=false"
echo "reset: rm -f $DB_PATH && redis-cli -n 14 FLUSHDB && re-run scripts/pilot_env_verify.sh"
