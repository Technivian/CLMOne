#!/usr/bin/env bash
# Run the Django dev server in the foreground. Keep this terminal open.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DEV_PORT="${DEV_PORT:-8060}"
DEV_HOST="${DEV_HOST:-0.0.0.0}"

mkdir -p logs
echo "$$" > logs/devserver.pid

exec env DATABASE_URL= \
  DJANGO_SETTINGS_MODULE=config.settings_development \
  DJANGO_DEBUG=true \
  "$ROOT_DIR/.venv/bin/python" -u manage.py runserver "${DEV_HOST}:${DEV_PORT}" --noreload
