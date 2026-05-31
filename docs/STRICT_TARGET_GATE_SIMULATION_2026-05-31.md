# Strict Target Gate Simulation (Ready To Run)

Date: 2026-05-31
Purpose: One-command strict target-environment gate with production-shape settings.

## Defaults Used

- Release commit: fe77689e61163763a7836b9359c57281cb1b04db
- Target host default: cms-aegis-preview.onrender.com
- Script: scripts/run_strict_target_gate.sh

## 1) Set Required Secrets

Run on the target host/session:

```bash
export TARGET_DB_URL='postgresql://<user>:<password>@<host>:5432/<db>?sslmode=require'
export TARGET_SECRET_KEY='<long-random-secret>'
```

Secret requirements enforced by the script:
- at least 50 characters
- at least 5 unique characters

Optional overrides:

```bash
export TARGET_HOST='cms-aegis-preview.onrender.com'
export TARGET_ORIGIN="https://${TARGET_HOST}"
export ORG_SLUG='demo-firm'
export ORG_NAME='Demo Firm'
export PYTHON_BIN="$PWD/.venv/bin/python"
export RELEASE_COMMIT_SHA='fe77689e61163763a7836b9359c57281cb1b04db'
```

## 2) Verify Approved Commit

```bash
git rev-parse HEAD
```

Expected:
- fe77689e61163763a7836b9359c57281cb1b04db

If not at expected commit:

```bash
git fetch origin codex/cms-aegis-activation
git checkout fe77689e61163763a7836b9359c57281cb1b04db
```

## 3) Execute Strict Gate

```bash
./scripts/run_strict_target_gate.sh
```

This performs:
- production-shape env export
- deploy checks and migration preflight
- tenant audit and isolation test
- strict evidence gate (`CUTOVER_MODE=require`) via scripts/run_target_signoff_gate.sh
- artifact and summary generation

Security gate policy:
- npm vulnerabilities fail the gate at `moderate` or higher by default.
- Override only if explicitly approved:

```bash
.venv/bin/python manage.py generate_release_gate_report --npm-fail-threshold=high --fail-on-no-go
```

## 4) Expected Outputs

Evidence directory:
- evidence/strict-target-gate-<timestamp>/

Required files include:
- postgres-cutover-evidence.json
- sprint3-integration-report.json
- esign-integration-report.json
- release-gate-report.json
- release-bundle/release-evidence-bundle.json
- target-signoff-summary.json

## 5) Manual Completion Steps

After strict gate succeeds:
1. Execute docs/MANUAL_SMOKE_CHECKLIST.md and attach smoke signoff.
2. Capture backup/restore rehearsal evidence and append docs/DRILL_LOG.md.
3. Use docs/PRODUCTION_CUTOVER_RUN_LOG_TEMPLATE_2026-05-31.md for operator log and approvals.
