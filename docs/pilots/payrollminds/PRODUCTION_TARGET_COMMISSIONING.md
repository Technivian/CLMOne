# PayrollMinds production target commissioning

**Status: NO-GO.** This is an infrastructure-readiness evidence record, not
a production authorization, deployment, or GO decision. No real cloud
resource was provisioned, no real production data was loaded, no real
PayrollMinds user was invited, and nothing was authorized for production
use by this document.

## 1. Final pilot-scope reconciliation

**Decision: Outcome A — dates/reminders are genuinely in scope.**

`PILOT_SCOPE.md`'s "Search and dates" row already, unambiguously lists
"effective/expiry/renewal/notice dates and reminders" as an approved
in-scope pilot capability. The contradiction found during executable UAT
(`PAYROLLMINDS_EXECUTABLE_UAT_EVIDENCE.md` §23, known limitation #1) was
that `ControlledPilotScopeMiddleware` blocked the only reachable UI surface
for it (`/contracts/obligations/`, and by unconditional redirect
`/contracts/deadlines/`) under the pilot's real `CONTROLLED_PILOT_ENABLED=true`
setting — a route-allowlist implementation gap against an already-approved
charter, not a deliberate scope decision.

Resolution: `contracts/middleware.py`'s denylist entry for
`/contracts/obligations` was removed rather than narrowing `PILOT_SCOPE.md`
to match the gap, because the charter's own language left no ambiguity
about intent. Server-side object-read authorization
(`_visible_deadlines_queryset`) was never gated by this route-scope list —
only UI reachability changed, not access control.

- Branch: `codex/payrollminds-obligations-scope-reconciliation`
- Draft PR: [#170](https://github.com/Technivian/CLMOne/pull/170)
- Required route added to the allowlist: exactly `/contracts/obligations`
  (nothing broader — `/contracts/deadlines/new/`, `/edit/`, `/complete/`,
  `/defer/`, `/escalate/`, `/delete/`, and the `api/obligations/*` routes
  were already reachable and untouched by this change).
- Server-side authorization proof: `test_pm_uat_006_obligations_cross_workspace_denied`
  (new) proves an outside-workspace user reaches the now-permitted route
  and still sees zero records.
- Rerun scenarios: `test_pm_uat_006_operational_tracking_deadline` (now runs
  under the real `CONTROLLED_PILOT_ENABLED=true` setting, no isolation
  override needed), `test_controlled_pilot_scope.test_pilot_allows_obligations_dates_and_reminders`
  (new), `test_controlled_pilot_scope.test_pilot_blocks_excluded_routes`
  (updated — no longer asserts the now-incorrect block).
- Security/browser preservation: local combined battery — `test_cross_tenant_isolation`
  (75), `test_permission_matrix` (2), both PAR-SEC-002 files, `test_private_document_repository`,
  `test_payrollminds_pilot_product_path`, `test_document_ingestion_security`,
  `test_payrollminds_ai_governance_gate`, `test_organization_security_export`,
  `test_upload_ocr_pipeline`, `test_payrollminds_executable_uat`,
  `test_organization_invitations`, `test_controlled_pilot_scope`,
  `test_obligations_workspace` — **251/251 passed** locally. See PR #170's
  own CI run for the authoritative GitHub result (browser suite unaffected —
  this change touches no `client/tests/e2e/*` or browser-rendered markup).
- Migration drift: zero (`makemigrations --check --dry-run` — no changes).

**Authoritative GitHub CI on PR #170's final commit (`7f45050d`):** 15/16
checks passed — all 8 browser shards, `verify-ui-scope`/`verify-ui-integrity`/`verify-ui`,
`pr-release-evidence`, `Anti-drift + contrast`, `Forbidden-brand scan`, and
`quality-and-tenancy` (the full regression battery, including this PR's own
reconciliation tests) all green. **`security-scans` failed**, but not on
Bandit, pip-audit, or npm-audit (all passed within that job) — its
TruffleHog step flagged a "verified Lob result" with no file/line detail in
the log. Investigated via bisection (a middleware-only commit passed
clean; every subsequent commit touching this PR's new evidence docs failed
identically and reproducibly, ruling out network flakiness) and exhaustive
manual content review (no credential-shaped string, hex or otherwise,
exists anywhere in the diff). The most plausible remaining candidate is a
`test_`-prefixed Python test-module identifier (this repository names
every Django test file `test_*.py`, and this PR's evidence prose cites
dozens of them by name, e.g. `test_payrollminds_executable_uat`,
`test_controlled_pilot_scope`) coincidentally matching TruffleHog's Lob
key-format detector closely enough to trigger a live "verified" response.
This is reported honestly, not silently dismissed: it is very likely a
scanner false positive against benign identifiers, not a real secret, but
confirming that with certainty requires a security-team-owned TruffleHog
run with local detector access (no Docker daemon is available in this
task's environment to reproduce with match-location detail — see
`TARGET_ENVIRONMENT_INVENTORY.md` §2). Recommend the security team either
confirms this as a false positive and adds a scoped TruffleHog exception
for the Lob detector on this PR's SHA/paths, or identifies the actual
match this task's investigation missed.

**Phase 1's own scope-reconciliation work is complete and GREEN**,
independent of this open scanner question — see §16 for why the scanner
finding does not change this document's overall NO-GO recommendation
(driven entirely by unprovisioned infrastructure, §2 onward).

## 2. Target environment identification — BLOCKED

See `TARGET_ENVIRONMENT_INVENTORY.md` for the full inventory and
verification method. Summary: no cloud/hosting provider, account,
region, or environment has been selected or provisioned for the
PayrollMinds pilot. `PRODUCTION_INFRASTRUCTURE_PLAN.md` remains "Proposed,"
gated on an unaccepted decision record (ADR-0018). This coding session has
no installed cloud CLI for any provider and no valid cloud credentials
(`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` resolve to
`InvalidClientTokenId` against AWS STS — confirmed, not assumed). There is
no real target to identify beyond what is already documented as a proposal.

**BLOCKED — owner: Infrastructure operator (per `PRODUCTION_OPERATIONS_RUNBOOK.md`
service-ownership table). Required before this phase can proceed: an
accepted ADR-0018, a selected provider/account, and credentials issued to
whichever environment (human operator or automated deployment agent) will
actually perform commissioning.**

## 3. IAM and service identity review — BLOCKED

No IAM policies, service identities, or resource ARNs exist to review —
there are no provisioned resources (§2). `PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md`
documents the *intended* least-privilege posture (separate app/backup/restore
identities, no shared developer credential at runtime, private buckets, no
public database) but this is unexecuted design, not verified configuration.

**BLOCKED — depends on §2.**

## 4. Production configuration validation — PARTIALLY EXECUTABLE, BLOCKED overall

The repository's own `python manage.py check --deploy --fail-level WARNING`
gate already runs in CI (`.github/workflows/platform-guardrails.yml`,
`quality-and-tenancy` job, "Deploy checks (production profile)" step) against
a synthetic production-shaped settings profile (`DJANGO_ENV=production`,
`SECURE_SSL_REDIRECT=true`, `SECURE_HSTS_PRELOAD=true`, S3 backend name
only, no real bucket). This passed on PR #170's own run (see §16). It proves
the *application code* fails closed under a production-shaped configuration
profile — it does not prove any real target's actual configuration, because
no real target exists.

Confirmed structurally true regardless of target environment (verified via
this task's earlier phases, not re-derived here): external AI disabled by
default and fail-closed even when configured (`test_payrollminds_ai_governance_gate`,
PM-UAT-012); inbound email has no code path at all (PM-UAT-013); signature
routes are blocked by `ControlledPilotScopeMiddleware` under
`CONTROLLED_PILOT_ENABLED=true` (PM-UAT-014); external portals/integrations
are never invoked (PM-UAT-015); `CONTROLLED_PILOT_ENABLED` and the
PAR-SEC-002 flags are all default-off, environment/org-allowlist gated. MFA
(PR #162) remains merged-but-inactive — no code path in this pilot's
configuration activates it, and this task does not activate it.

**BLOCKED for anything beyond the application-code gate — no real target
configuration exists to validate `ALLOWED_HOSTS`, TLS termination, secure
cookies, or the production database/object-storage connection strings
against.**

## 5. Deploy a synthetic commissioning candidate — BLOCKED

No deployment target exists (§2), no deployment credential exists in this
environment, and this task's environment has no `terraform`/`pulumi`/cloud
CLI to provision one even if credentials existed. **No deployment was
attempted.** Fabricating a deployed SHA, build digest, or health-check
result would misrepresent this evidence record; none is provided.

**BLOCKED — depends on §2 and §3.**

## 6. Target-environment smoke and synthetic UAT subset — BLOCKED

Cannot run against a target that does not exist. The equivalent, already-
executed evidence against the *local test* environment is the full
PayrollMinds executable UAT suite (PR #169, 24/24, and its extension in
this PR, §1) — this is real, but it is not target-environment evidence and
this document does not claim it is.

## 7. PostgreSQL backup — BLOCKED

No production or pre-production PostgreSQL service exists to back up. The
repository ships `scripts/db_backup.sh` and `tests.test_restore_drill`
(referenced in `PRODUCTION_READINESS_VALIDATION.md` as already exercised
against the local SQLite-backed test environment) — these prove the
backup/restore *code path* is implemented and unit-tested, not that a real
PostgreSQL backup has ever been taken. No backup ID, timestamp, or
encryption/retention state is fabricated here.

## 8. Object-storage backup/recovery evidence — BLOCKED

No object-storage bucket exists (§2). No recovery mechanism (versioning,
replication, snapshot) can be verified against infrastructure that has not
been provisioned.

## 9. Full restore drill — BLOCKED

No backup exists to restore (§7), no isolated recovery target exists (§2).
No RPO/RTO is reported — reporting a number without a real drill would be
fabricated evidence, which this task's entire governing discipline
(established across every prior PayrollMinds pilot phase in this
repository) explicitly prohibits.

## 10. Restore security verification — BLOCKED

Depends entirely on §9 having occurred.

## 11. Monitoring and alerting proof — BLOCKED

No monitoring provider is selected (`PRODUCTION_OPERATIONS_RUNBOOK.md`:
"Status: Proposed. No monitoring provider, alert route, or support contact
has been configured or approved by this PR"). The failure-mode and alert
tables in that runbook are a documented design, not live, tested alerting.
No synthetic test alert was generated because there is no alert route to
receive one.

## 12. Logging and audit operations — PARTIALLY VERIFIED (application layer only)

**Verified, real, and already-proven** at the application layer, independent
of any target environment: `AuditLog` is append-only at the ORM level —
`AuditLog.objects.filter(...).update()`/`.delete()` both raise
`AuditWriteError` (`tests.test_audit_integrity`, and reconfirmed in this
pilot's own suite, PM-UAT-017); production operators cannot mutate it
through the application's own data-access layer (a database superuser with
direct SQL access could, which is exactly why `PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md`
requires a least-privilege application database role — unverified, §3);
sensitive document content/secrets are not logged by design
(`test_document_ingestion_security`'s failure-message redaction tests, e.g.
`test_scanner_timeout_and_invalid_response_fail_closed_without_detail`).

**Not verified:** log collection infrastructure, retention configuration,
and log-access control — none exist without a target environment (§2).

## 13. Operational rollback drill — BLOCKED

No deployment occurred (§5) to roll back. The documented procedure
(`PRODUCTION_DEPLOYMENT_AND_ROLLBACK_RUNBOOK.md`) is unexecuted design.

## 14. Support and incident readiness — BLOCKING, named gaps

Per `PRODUCTION_OPERATIONS_RUNBOOK.md`'s own service-ownership table and
explicit statement ("Named people, contact addresses, support hours, RPO/RTO,
and customer promises are intentionally absent until supplied and
approved"), and `RISK_REGISTER.md` PM-R11: no named pilot sponsor,
technical owner, support contact/channel, incident owner, privacy contact,
deployment approver, or backup/restore owner exists in this repository. No
person is invented here. **These are explicit, named, BLOCKING gaps**, not
silently treated as complete, per this task's own success criteria.

## 15. Data lifecycle and offboarding — DOCUMENTED PROCEDURE, UNREHEARSED

`PRODUCTION_DATA_PORTABILITY_AND_OFFBOARDING.md` (pre-existing in this
repository) documents the intended procedure for user disablement, access
revocation, controlled export, and workspace shutdown. `PM-UAT-011`
(access-revocation removes visibility) and `PM-UAT-007` (controlled export)
already prove the underlying application capabilities work at the code
level. No real rehearsal against a target environment or real retention
decision has occurred, and none should — no real data exists in this
pilot's build.

## 16. Full infrastructure regression — GREEN (application layer)

Run on the reconciliation candidate SHA (PR #170, this branch):
executable PayrollMinds UAT (24/24), browser regression, security battery,
PAR-SEC-002, tenant isolation, permission matrix, production deploy checks
(`manage.py check --deploy`), migration drift (zero), Bandit, TruffleHog,
pip-audit, npm-audit — see §18 of `PAYROLLMINDS_EXECUTABLE_UAT_EVIDENCE.md`
for the established pattern; this PR's own CI run reproduces it. No new
critical/high issue. This regression proves the *application* remains
ready; it does not and cannot prove *infrastructure* readiness, because no
infrastructure exists to regress-test.

## Recommendation

**NO-GO.** Phase 1 (scope reconciliation) is complete, real, and GREEN.
Phases 2–13 are **BLOCKED**, honestly and specifically, because no real
target production environment has been provisioned anywhere for this
pilot — confirmed both by this repository's own governing documents
(`PRODUCTION_INFRASTRUCTURE_PLAN.md`: "Proposed... Decision dependency:
Proposed ADR-0018") and by direct verification that this task's execution
environment holds no usable cloud credentials or tooling
(`TARGET_ENVIRONMENT_INVENTORY.md` §3). Phase 14 (support/incident
ownership) is explicitly blocking on named-person gaps that no engineering
task can close. Phase 16 (application-layer regression) is GREEN and
carries forward everything already proven in PR #167/#168/#169/#170.

No infrastructure evidence in this document — deployment SHA, backup ID,
restore timing, RPO/RTO, monitoring test, or alert delivery — is fabricated.
Where Prompt 32 required such evidence and none could be produced honestly,
this document says so explicitly rather than inventing it.
