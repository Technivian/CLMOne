#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTERVAL_MINUTES="${1:-60}"

"$ROOT_DIR/scripts/dev_down.sh"
pkill -f "uvicorn config.asgi:application" 2>/dev/null || true
sleep 1

# Prefer the durable HTTPS path on this project; fall back to HTTP runserver.
if [[ -x "$ROOT_DIR/scripts/dev_https.sh" ]]; then
  "$ROOT_DIR/scripts/dev_https.sh" up --background
  # Reminder scheduler is still started by the HTTP helper when available.
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    mkdir -p "$ROOT_DIR/logs"
    if [[ ! -f "$ROOT_DIR/logs/reminder_scheduler.pid" ]] || ! kill -0 "$(cat "$ROOT_DIR/logs/reminder_scheduler.pid")" 2>/dev/null; then
      : > "$ROOT_DIR/logs/reminder_scheduler.log"
      nohup env DATABASE_URL= DJANGO_SETTINGS_MODULE=config.settings_development \
        "$ROOT_DIR/.venv/bin/python" -u manage.py run_reminder_scheduler --interval-minutes "$INTERVAL_MINUTES" \
        >> "$ROOT_DIR/logs/reminder_scheduler.log" 2>&1 &
      echo $! > "$ROOT_DIR/logs/reminder_scheduler.pid"
      echo "Started reminder scheduler (pid $(cat "$ROOT_DIR/logs/reminder_scheduler.pid"))."
    fi
  fi
else
  "$ROOT_DIR/scripts/dev_up.sh" "$INTERVAL_MINUTES"
fi
