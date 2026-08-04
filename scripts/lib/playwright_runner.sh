#!/usr/bin/env bash
# Shared argument handling for scripts/verify_ui.sh. Keep this Bash 3.2
# compatible because the supported local developer shell on macOS still uses it.

validate_playwright_shard() {
  local shard="${1:-}"

  if [[ -n "$shard" && ! "$shard" =~ ^[1-9][0-9]*/[1-9][0-9]*$ ]]; then
    echo "[verify-ui] Invalid PLAYWRIGHT_SHARD: ${shard}" >&2
    echo "[verify-ui] Expected a Playwright shard such as 1/4." >&2
    return 2
  fi
}

run_playwright() {
  if (( "$#" == 0 )); then
    npm --prefix client run test:e2e
  else
    npm --prefix client run test:e2e -- "$@"
  fi
}
