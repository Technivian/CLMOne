#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEV_PORT="${DEV_PORT:-8060}"

echo "CLM One dev status (port ${DEV_PORT})"
echo

if lsof -i "tcp:${DEV_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Listener: up"
  lsof -i "tcp:${DEV_PORT}" -sTCP:LISTEN | tail -n +2
else
  echo "Listener: down"
fi

if [[ -f logs/devserver.pid ]] && kill -0 "$(cat logs/devserver.pid)" 2>/dev/null; then
  echo "PID file: logs/devserver.pid -> $(cat logs/devserver.pid) (running)"
else
  echo "PID file: missing or stale"
fi

if curl -sf --connect-timeout 3 "http://127.0.0.1:${DEV_PORT}/login/" >/dev/null; then
  echo "Health:   http://127.0.0.1:${DEV_PORT}/login/ -> 200"
  echo "Open:     http://localhost:${DEV_PORT}/"
else
  echo "Health:   /login/ not reachable"
  echo "Try:      scripts/dev_restart.sh"
fi

if [[ -f logs/devserver.log ]]; then
  echo
  echo "Recent server log:"
  tail -5 logs/devserver.log
fi
