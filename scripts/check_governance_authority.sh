#!/usr/bin/env bash
# Fail if DESIGN_CONSTITUTION.md is treated as live authority without the
# historical supersession banner, or if GOVERNANCE_CHARTER.md is missing.
set -euo pipefail
ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f GOVERNANCE_CHARTER.md ]]; then
  echo "FAIL: GOVERNANCE_CHARTER.md missing (canonical charter required)"
  exit 1
fi

if ! grep -q 'canonical repository governance document' GOVERNANCE_CHARTER.md; then
  echo "FAIL: GOVERNANCE_CHARTER.md is not marked canonical"
  exit 1
fi

if [[ ! -f DESIGN_CONSTITUTION.md ]]; then
  echo "FAIL: DESIGN_CONSTITUTION.md must be retained as historical"
  exit 1
fi

if ! grep -q 'HISTORICAL — SUPERSEDED' DESIGN_CONSTITUTION.md; then
  echo "FAIL: DESIGN_CONSTITUTION.md lacks historical supersession banner"
  exit 1
fi

if ! grep -q '0009-governance-charter-supersession' DESIGN_CONSTITUTION.md; then
  echo "FAIL: DESIGN_CONSTITUTION.md must link ADR-0009"
  exit 1
fi

if ! grep -q 'Approved by' docs/adr/0009-governance-charter-supersession.md; then
  echo "FAIL: ADR-0009 missing approval authority metadata"
  exit 1
fi

if ! grep -q 'GOVERNANCE_CHARTER.md' docs/design-system/README.md; then
  echo "FAIL: design-system README must reference GOVERNANCE_CHARTER.md"
  exit 1
fi

# Authority order: charter must appear before historical constitution in design-system README.
charter_line=$(rg -n 'GOVERNANCE_CHARTER' docs/design-system/README.md | head -1 | cut -d: -f1)
hist_line=$(rg -n 'DESIGN_CONSTITUTION' docs/design-system/README.md | head -1 | cut -d: -f1)
if [[ -z "$charter_line" || -z "$hist_line" || "$charter_line" -ge "$hist_line" ]]; then
  echo "FAIL: design-system authority order must list GOVERNANCE_CHARTER before DESIGN_CONSTITUTION"
  exit 1
fi

echo "OK: governance amendment integrity checks passed"
exit 0
