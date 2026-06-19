#!/usr/bin/env bash
# db_backup.sh — dump the CMS Aegis PostgreSQL database to a timestamped file.
# Usage:  ./scripts/db_backup.sh [output_dir]
# Reads DATABASE_URL from the environment (or .env if present).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Load .env if present and DATABASE_URL not already set
if [[ -z "${DATABASE_URL:-}" && -f "$ROOT_DIR/.env" ]]; then
  export $(grep -v '^#' "$ROOT_DIR/.env" | grep DATABASE_URL | xargs)
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set." >&2
  exit 1
fi

# Prefer a pg_dump that matches the server version (17/18) over the system default (14).
for _candidate in \
  /opt/homebrew/opt/postgresql@18/bin/pg_dump \
  /opt/homebrew/opt/postgresql@17/bin/pg_dump \
  /usr/local/opt/postgresql@18/bin/pg_dump \
  /usr/local/opt/postgresql@17/bin/pg_dump \
  pg_dump; do
  if command -v "$_candidate" &>/dev/null; then
    PG_DUMP="$_candidate"
    break
  fi
done
PG_DUMP="${PG_DUMP:-pg_dump}"

OUTPUT_DIR="${1:-$ROOT_DIR/backups}"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTFILE="$OUTPUT_DIR/cms_aegis_${TIMESTAMP}.dump"

echo "Backing up to $OUTFILE (using $PG_DUMP) ..."
"$PG_DUMP" --format=custom --no-acl --no-owner "$DATABASE_URL" -f "$OUTFILE"

SIZE=$(du -sh "$OUTFILE" | cut -f1)
echo "Done. $OUTFILE ($SIZE)"
