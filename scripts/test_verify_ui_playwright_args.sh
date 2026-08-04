#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT_DIR/scripts/lib/playwright_runner.sh"

TEST_TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/verify-ui-args.XXXXXX")"
cleanup() {
  rm -rf "$TEST_TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$TEST_TMP_DIR/bin"
cat > "$TEST_TMP_DIR/bin/npm" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$VERIFY_UI_ARGS_CAPTURE"
EOF
chmod +x "$TEST_TMP_DIR/bin/npm"
export PATH="$TEST_TMP_DIR/bin:$PATH"
export VERIFY_UI_ARGS_CAPTURE="$TEST_TMP_DIR/args"

assert_args() {
  local expected="$1"
  local actual
  actual="$(cat "$VERIFY_UI_ARGS_CAPTURE")"
  if [[ "$actual" != "$expected" ]]; then
    echo "unexpected npm arguments" >&2
    echo "expected: $expected" >&2
    echo "actual: $actual" >&2
    exit 1
  fi
}

unset PLAYWRIGHT_ARGS || true
run_playwright
assert_args $'--prefix\nclient\nrun\ntest:e2e'

PLAYWRIGHT_ARGS=()
if (( ${#PLAYWRIGHT_ARGS[@]} )); then
  run_playwright "${PLAYWRIGHT_ARGS[@]}"
else
  run_playwright
fi
assert_args $'--prefix\nclient\nrun\ntest:e2e'

run_playwright '--shard=1/8'
assert_args $'--prefix\nclient\nrun\ntest:e2e\n--\n--shard=1/8'

run_playwright '--shard=1/8' '--grep=contract review' '--project=chromium'
assert_args $'--prefix\nclient\nrun\ntest:e2e\n--\n--shard=1/8\n--grep=contract review\n--project=chromium'

if validate_playwright_shard 'bad/shard'; then
  echo "invalid shard was accepted" >&2
  exit 1
fi
validate_playwright_shard ''
validate_playwright_shard '1/8'

echo "verify_ui Playwright argument handling: PASS"
