#!/usr/bin/env bash
set -euo pipefail

# Run the base and head in isolated worktrees. Raw Playwright failures are
# captured, never converted to success; the comparator decides PR eligibility.
BASE_REF=${1:?base revision required}
ROOT=$(git rev-parse --show-toplevel)
ARTIFACT_DIR=${BROWSER_GATE_ARTIFACT_DIR:-"$ROOT/browser-gate-artifacts"}
BASE_DIR=$(mktemp -d)
cleanup() { git -C "$ROOT" worktree remove --force "$BASE_DIR" 2>/dev/null || true; }
trap cleanup EXIT
mkdir -p "$ARTIFACT_DIR"
git -C "$ROOT" worktree add --detach "$BASE_DIR" "$BASE_REF" >/dev/null

run_suite() {
  local checkout=$1 output=$2 port=$3 status
  (
    cd "$checkout"
    python manage.py migrate --noinput >/dev/null
    PLAYWRIGHT_JSON_OUTPUT="$output" E2E_PORT="$port" ./scripts/verify_ui.sh
  )
  status=$?
  printf '%s\n' "$status" > "${output}.exit-status"
  [[ -s "$output" ]] || { echo "missing Playwright JSON: $output" >&2; return 2; }
  return 0
}

set +e
run_suite "$BASE_DIR" "$ARTIFACT_DIR/base.json" 8031
base_runner_status=$?
run_suite "$ROOT" "$ARTIFACT_DIR/head.json" 8032
head_runner_status=$?
set -e
python scripts/browser_regression_gate.py \
  --base "$ARTIFACT_DIR/base.json" \
  --head "$ARTIFACT_DIR/head.json" \
  --baseline docs/quality/PLAYWRIGHT_BASELINE.json \
  --report "$ARTIFACT_DIR/comparison.json"
gate_status=$?
printf 'raw base runner exit=%s; raw head runner exit=%s; comparator exit=%s\n' "$base_runner_status" "$head_runner_status" "$gate_status"
exit "$gate_status"
