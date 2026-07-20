#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEV_PORT="${DEV_PORT:-8060}"

stop_proc() {
  local name="$1"
  local pid_file="$2"

  if [[ ! -f "$pid_file" ]]; then
    echo "$name not running (no pid file)."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" || true
    echo "Stopped $name (pid $pid)."
  else
    echo "$name pid file exists but process is not running (pid $pid)."
  fi
  rm -f "$pid_file"
}

stop_proc "reminder scheduler" "logs/reminder_scheduler.pid"
stop_proc "dev server" "logs/devserver.pid"

pids="$(lsof -ti "tcp:${DEV_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
if [[ -n "$pids" ]]; then
  echo "Stopping listeners still bound to port ${DEV_PORT}..."
  for pid in $pids; do
    kill "$pid" 2>/dev/null || true
  done
fi

if [[ -f logs/dev_https.pid ]]; then
  stop_proc "HTTPS dev server" "logs/dev_https.pid"
fi

echo "Shutdown complete."
