#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

INTERVAL_MINUTES="${1:-60}"
DEV_PORT="${DEV_PORT:-8060}"
DEV_HOST="${DEV_HOST:-0.0.0.0}"
mkdir -p logs

wait_for_port() {
  local tries=0
  while [[ $tries -lt 40 ]]; do
    if lsof -i "tcp:${DEV_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
    tries=$((tries + 1))
  done
  return 1
}

health_check() {
  curl -sf --connect-timeout 3 "http://127.0.0.1:${DEV_PORT}/login/" >/dev/null
}

start_proc() {
  local name="$1"
  local pid_file="$2"
  local log_file="$3"
  shift 3

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    echo "$name already running (pid $(cat "$pid_file"))."
    return 0
  fi

  : > "$log_file"
  # macOS has no setsid(1). nohup + background is enough to detach from the
  # calling shell; Linux keeps setsid when available for a new session.
  if command -v setsid >/dev/null 2>&1; then
    nohup setsid "$@" >> "$log_file" 2>&1 &
  else
    nohup "$@" >> "$log_file" 2>&1 &
  fi
  local pid=$!
  disown "$pid" 2>/dev/null || true
  echo "$pid" > "$pid_file"

  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$pid_file"
    echo "Failed to start $name. See $log_file for details."
    tail -20 "$log_file" || true
    return 1
  fi

  echo "Started $name (pid $pid)."
}

stop_port_listeners() {
  local pids
  pids="$(lsof -ti "tcp:${DEV_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Stopping existing listeners on port ${DEV_PORT}..."
    for pid in $pids; do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
    pids="$(lsof -ti "tcp:${DEV_PORT}" -sTCP:LISTEN 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      for pid in $pids; do
        kill -9 "$pid" 2>/dev/null || true
      done
    fi
  fi
}

start_dev_server() {
  local pid_file="logs/devserver.pid"
  local log_file="logs/devserver.log"

  if [[ -f "$pid_file" ]] && kill -0 "$(cat "$pid_file")" 2>/dev/null; then
    if wait_for_port && health_check; then
      echo "dev server already running (pid $(cat "$pid_file"))."
      return 0
    fi
    echo "Stale dev server pid file; restarting."
    kill "$(cat "$pid_file")" 2>/dev/null || true
    rm -f "$pid_file"
  fi

  local port_pid
  port_pid="$(lsof -ti "tcp:${DEV_PORT}" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [[ -n "$port_pid" ]]; then
    if health_check; then
      echo "$port_pid" > "$pid_file"
      echo "Adopted existing dev server on port ${DEV_PORT} (pid $port_pid)."
      return 0
    fi
    stop_port_listeners
  fi

  # --noreload keeps a single long-lived worker under nohup. Auto-reload forks
  # a parent watcher that often dies when detached from an interactive shell.
  start_proc "dev server" "$pid_file" "$log_file" \
    env DATABASE_URL= DJANGO_SETTINGS_MODULE=config.settings_development DJANGO_DEBUG=true \
    "$ROOT_DIR/.venv/bin/python" -u manage.py runserver "${DEV_HOST}:${DEV_PORT}" --noreload

  if ! wait_for_port; then
    echo "dev server did not bind to port ${DEV_PORT}. See $log_file"
    tail -30 "$log_file" || true
    return 1
  fi

  if ! health_check; then
    echo "dev server is listening but /login/ is not healthy. See $log_file"
    tail -30 "$log_file" || true
    return 1
  fi

  echo "dev server ready at http://localhost:${DEV_PORT}/"
}

start_dev_server

start_proc "reminder scheduler" "logs/reminder_scheduler.pid" "logs/reminder_scheduler.log" \
  env DATABASE_URL= DJANGO_SETTINGS_MODULE=config.settings_development \
  "$ROOT_DIR/.venv/bin/python" -u manage.py run_reminder_scheduler --interval-minutes "$INTERVAL_MINUTES"

echo "Services started."
echo "- App URL: http://localhost:${DEV_PORT}/"
echo "- Server log: logs/devserver.log"
echo "- Scheduler log: logs/reminder_scheduler.log"
