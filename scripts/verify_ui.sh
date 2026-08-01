#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="./.venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

VERIFY_UI_MODE="${VERIFY_UI_MODE:-all}"
case "$VERIFY_UI_MODE" in
  all|integrity|browser) ;;
  *)
    echo "[verify-ui] Unknown VERIFY_UI_MODE: ${VERIFY_UI_MODE}" >&2
    echo "[verify-ui] Expected one of: all, integrity, browser" >&2
    exit 2
    ;;
esac

DEFAULT_E2E_PORT="${E2E_PORT:-8010}"
E2E_PORT="$DEFAULT_E2E_PORT"

if [[ -z "${E2E_BASE_URL:-}" ]]; then
  for candidate in $(seq "$DEFAULT_E2E_PORT" $((DEFAULT_E2E_PORT + 20))); do
    if ! lsof -nP -iTCP:"$candidate" -sTCP:LISTEN >/dev/null 2>&1; then
      E2E_PORT="$candidate"
      break
    fi
  done
  E2E_BASE_URL="http://127.0.0.1:${E2E_PORT}"
else
  E2E_BASE_URL="${E2E_BASE_URL}"
  E2E_PORT="${E2E_BASE_URL##*:}"
fi
E2E_USERNAME="${E2E_USERNAME:-e2e_owner}"
E2E_PASSWORD="${E2E_PASSWORD:-e2e_pass_123}"

mkdir -p logs

if [[ "$VERIFY_UI_MODE" == "all" || "$VERIFY_UI_MODE" == "integrity" ]]; then
  echo "[verify-ui] Running UI integrity suites..."
  "$PYTHON_BIN" manage.py test \
    tests.test_ui_click_integrity \
    tests.test_redesign_components \
    -v 2
fi

if [[ "$VERIFY_UI_MODE" == "integrity" ]]; then
  echo "[verify-ui] UI integrity suites completed successfully."
  exit 0
fi

if [[ "${VERIFY_UI_DEPS_READY:-0}" == "1" ]]; then
  echo "[verify-ui] Using pre-installed Playwright dependencies."
else
  echo "[verify-ui] Installing Playwright dependencies (if needed)..."
  npm --prefix client ci >/dev/null
  npm --prefix client exec playwright install chromium >/dev/null
fi

SERVER_LOG="logs/e2e-devserver-${E2E_PORT}.log"
echo "[verify-ui] Starting deterministic E2E fixture server at ${E2E_BASE_URL}..."
E2E_PORT="${E2E_PORT}" \
E2E_DATABASE_URL="${E2E_DATABASE_URL:-}" \
sh scripts/start_e2e_server.sh > "$SERVER_LOG" 2>&1 &
SERVER_PID=$!

cleanup() {
  if kill -0 "$SERVER_PID" >/dev/null 2>&1; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

for _ in {1..120}; do
  if curl -s -o /dev/null "${E2E_BASE_URL}/login/"; then
    break
  fi
  sleep 1
done

if ! curl -s -o /dev/null "${E2E_BASE_URL}/login/"; then
  echo "[verify-ui] Server did not become ready; check ${SERVER_LOG}"
  exit 1
fi

echo "[verify-ui] Running Playwright smoke tests..."
PLAYWRIGHT_ARGS=()
if [[ -n "${PLAYWRIGHT_SHARD:-}" ]]; then
  if [[ ! "$PLAYWRIGHT_SHARD" =~ ^[1-9][0-9]*/[1-9][0-9]*$ ]]; then
    echo "[verify-ui] Invalid PLAYWRIGHT_SHARD: ${PLAYWRIGHT_SHARD}" >&2
    echo "[verify-ui] Expected a Playwright shard such as 1/4." >&2
    exit 2
  fi
  PLAYWRIGHT_ARGS+=("--shard=${PLAYWRIGHT_SHARD}")
  echo "[verify-ui] Running isolated Playwright shard ${PLAYWRIGHT_SHARD}."
fi

E2E_BASE_URL="${E2E_BASE_URL}" \
E2E_USERNAME="${E2E_USERNAME}" \
E2E_PASSWORD="${E2E_PASSWORD}" \
npm --prefix client run test:e2e -- "${PLAYWRIGHT_ARGS[@]}"

echo "[verify-ui] Completed successfully."
