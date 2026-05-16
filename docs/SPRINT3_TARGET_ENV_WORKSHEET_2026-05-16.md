# Sprint 3 Target-Environment Worksheet

Date: 2026-05-16
Purpose: Execute and record the final Sprint 3 target-environment proof required for launch signoff.

Companion docs:

- Command sheet: [docs/SPRINT3_TARGET_ENV_COMMAND_SHEET_2026-05-16.md](SPRINT3_TARGET_ENV_COMMAND_SHEET_2026-05-16.md)
- GO/NO-GO call script: [docs/SPRINT3_GO_NO_GO_CALL_SCRIPT_2026-05-16.md](SPRINT3_GO_NO_GO_CALL_SCRIPT_2026-05-16.md)

## 1) Run Context

| Field | Value |
|---|---|
| Environment name | local-postgres-rehearsal (baseline) |
| Host / URL | localhost / 127.0.0.1 |
| Operator | GitHub Copilot |
| Commit SHA | c1b1772 |
| Start timestamp (UTC) | 2026-05-16T11:07:38+00:00 |
| End timestamp (UTC) | 2026-05-16T11:07:42+00:00 |

## 2) Pre-Run Preconditions

Mark each item before execution.

- [x] PostgreSQL target is reachable and credentials validated (local rehearsal)
- [x] Salesforce connection is configured for target org (local synthetic rehearsal)
- [x] Webhook endpoint and secrets are configured (local synthetic rehearsal)
- [x] E-sign provider webhook secret is configured (local synthetic rehearsal)
- [ ] Backup destination and permissions are confirmed (target env pending)
- [ ] `evidence/` artifact upload path is available (target env pending)

## 3) Strict Execution Command

Run from repository root on the target environment:

```bash
DJANGO_ENV=production \
DJANGO_SECRET_KEY='<long-random-secret>' \
ALLOWED_HOSTS='staging.example.com' \
CSRF_TRUSTED_ORIGINS='https://staging.example.com' \
DEFAULT_FROM_EMAIL='ops@example.com' \
DATABASE_URL='postgresql://<user>:<password>@<host>:5432/<db>?sslmode=require' \
DB_SSL_REQUIRE=true \
SECURE_SSL_REDIRECT=true \
SECURE_HSTS_PRELOAD=true \
CUTOVER_MODE=require \
ORG_SLUG='demo-firm' \
ORG_NAME='Demo Firm' \
./scripts/run_live_evidence_pack.sh
```

> **Preferred:** use the full target signoff script which also runs the backup/restore drill and emits a machine-readable verdict:
> ```bash
> # same env vars as above, plus:
> PG_BIN_DIR='/path/to/pg16/bin'   # e.g. /usr/lib/postgresql/16/bin on Ubuntu
> SIGNOFF_OUTPUT='evidence/target-signoff-report.json'
> ./scripts/target_signoff.sh
> # Exit 0 = GO   |   Exit 1 = NO-GO (FAILED gates listed to stderr)
> ```
> Output artifact: `evidence/target-signoff-report.json`

## 4) Evidence Gate Results

| Gate | Expected | Actual | Pass/Fail | Artifact Link |
|---|---|---|---|---|
| Postgres cutover | `cutover_ready=true` | `cutover_ready=true`; engine=`django.db.backends.postgresql`; migrations clean | PASS (baseline) | [evidence/postgres-cutover-evidence.json](../evidence/postgres-cutover-evidence.json) |
| Sprint 3 integration | `GO` | `GO`; sync `SUCCESS`; webhook `SENT` | PASS (baseline) | [evidence/sprint3-integration-report.json](../evidence/sprint3-integration-report.json) |
| E-sign integration | `GO` | `GO`; applied event present; terminal signature present | PASS (baseline) | [evidence/esign-integration-report.json](../evidence/esign-integration-report.json) |
| Release gate | `GO` | `GO`; db/integrations/security all pass | PASS (baseline) | [evidence/release-gate-report.json](../evidence/release-gate-report.json) |
| Executive analytics evidence | generated | generated (`organization_count=1`) | PASS (baseline) | [evidence/executive-analytics-evidence.json](../evidence/executive-analytics-evidence.json) |
| Retention audit evidence | generated | generated (`count=0` in 30-day window) | PASS (baseline) | [evidence/retention-audit-actions.json](../evidence/retention-audit-actions.json) |
| Release bundle | `GO` | `GO` | PASS (baseline) | [evidence/release-bundle/release-evidence-bundle.json](../evidence/release-bundle/release-evidence-bundle.json) |
| Target signoff (all gates) | `GO` | `GO`; all 8 gates; backup drill PASS | PASS (local rehearsal 2026-05-16T11:57:44Z) | [evidence/target-signoff-report.json](../evidence/target-signoff-report.json) |

## 5) Manual Smoke and Rollback Proof

- [ ] Manual smoke executed using [docs/MANUAL_SMOKE_CHECKLIST.md](MANUAL_SMOKE_CHECKLIST.md)
- [x] Manual smoke signoff placeholder exists at [evidence/manual-smoke-signoff.md](../evidence/manual-smoke-signoff.md)
- [x] Local PostgreSQL backup + restore rehearsal completed (2026-05-16) and logged in [docs/DRILL_LOG.md](DRILL_LOG.md)
- [ ] Backup + restore rehearsal completed in target environment using [docs/ROLLBACK_RUNBOOK.md](ROLLBACK_RUNBOOK.md)
- [x] Drill entry appended for local replay in [docs/DRILL_LOG.md](DRILL_LOG.md)

## 6) Final Decision

| Field | Value |
|---|---|
| Release Gate | GO (baseline) |
| Sprint 3 Integration | GO (baseline) |
| E-sign Integration | GO (baseline) |
| Cutover Ready | true (baseline) |
| Manual Smoke | PENDING (target env) |
| Rollback Drill | PARTIAL (local PostgreSQL restore PASS; target env rehearsal pending) |
| Final Decision | NO-GO for production until target evidence is attached |
| Notes | Local strict Postgres rehearsal is green; target-environment run is required for launch signoff. |

## 7) Target-Only Remaining Work

Complete these in target environment to convert this worksheet to final `GO`:

1. Run strict 8-step evidence pack against target PostgreSQL with live integrations.
2. Execute and sign off manual smoke in target environment.
3. Run backup + restore rehearsal in target environment and record timings.
4. Update gate table above with target artifact timestamps and statuses.

## 8) Signoff

| Role | Name | Timestamp (UTC) | Signature |
|---|---|---|---|
| TL | | | |
| QA | | | |
| SRE | | | |
| Security | | | |
