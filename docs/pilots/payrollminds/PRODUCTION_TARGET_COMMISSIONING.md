# PayrollMinds production target commissioning

> **TECHNICAL ENVIRONMENT: LIVE.** A real, correctly-scoped pilot
> deployment exists and is running (Render/Frankfurt, Neon/Frankfurt,
> Cloudflare R2, `clmone.com`) — see `TARGET_ENVIRONMENT_INVENTORY.md`
> §1c.
>
> **PAYROLLMINDS CUSTOMER ONBOARDING: NO-GO.** The technical environment
> being live does not authorize onboarding real PayrollMinds customer
> users. That remains blocked on the specific, named gaps in this
> document's Recommendation section (backup/recovery readiness, an
> isolated restore drill, monitoring/alerting, and several named
> operational owners) — not on infrastructure existing, which it now
> does.
>
> These are two separate questions with two separate answers. Do not
> conflate "the environment is live" with "customer onboarding is
> authorized" — it is not.

This began as an infrastructure-readiness evidence record against
infrastructure that did not yet exist. Mid-conversation on 2026-08-08, it
emerged that the pilot sponsor already had a real deployment running
independently, unconnected to this document's own phased commissioning
process — see `TARGET_ENVIRONMENT_INVENTORY.md` §1c for the full record of
its discovery, database migration, and security hardening. This document
now describes a real, live, pilot-scope-restricted system handling
sponsor-only usage (no other PayrollMinds users yet), not a synthetic
exercise. It still is not a claim that every readiness gate in this
document has been satisfied — several genuinely have not (§7, §8, §9,
§11, §13, §14) — and nothing here authorizes onboarding real PayrollMinds
customer users while those gaps remain open.

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

## 2. Target environment identification — BLOCKED (database component decided)

See `TARGET_ENVIRONMENT_INVENTORY.md` §1a for the full record. Update
(2026-08-08): the pilot sponsor has selected and confirmed a production
database — Neon managed PostgreSQL, project region `eu-central-1` (AWS
Frankfurt, DE) — directly, outside this coding session's own (still
credential-less) access. This is real progress on one line of
`PRODUCTION_INFRASTRUCTURE_PLAN.md`'s topology table, not fabricated: the
sponsor supplied a live connection string in conversation, confirmed it as
the intended production instance, and confirmed it is new/empty (no
migration needed). The connection string itself was never written to this
repository, any commit, or any CI configuration, and this session could not
independently verify reachability (a direct connection attempt from this
sandbox produced no response, consistent with this environment's outbound
network policy blocking raw TCP egress to arbitrary hosts — the sandbox's
limitation, not evidence about the database itself).

**Further update, 2026-08-08:** the sponsor also confirmed object storage
(Cloudflare R2, an existing account), a DNS/TLS domain (`clmone.com` on the
same Cloudflare account), and a named Infrastructure operator (Haroon
Wahed) — see `TARGET_ENVIRONMENT_INVENTORY.md` §1b for the full record,
including honest, currently-researched (not assumed) reasons why
application runtime has no clean free+EU+indefinite answer yet.
Application runtime, cache/queue, secret management, and a true
long-retention backup target remain unselected or only partially answered.
`PRODUCTION_INFRASTRUCTURE_PLAN.md` remains "Proposed" overall, gated on an
unaccepted decision record (ADR-0018). This coding session still has no
installed cloud CLI for any provider and no valid cloud credentials
(`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` resolve to
`InvalidClientTokenId` against AWS STS — confirmed, not assumed).

**Update, 2026-08-08 (supersedes the above): a real target environment was
discovered, not commissioned through this phase's own process.** The
sponsor had already been running a live Render deployment (Frankfurt) at
`clmone.com` before this conversation began. Once disclosed, this task
verified and hardened it in place rather than treating it as hypothetical
— see `TARGET_ENVIRONMENT_INVENTORY.md` §1c for the complete record:
database migrated from a prior Render Postgres instance to Neon (verified
via full 122-table row-count comparison), pilot-scope enforcement
(`CONTROLLED_PILOT_ENABLED` and related flags) turned on where it had not
been, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` corrected, and quarantine
object storage wired to a separately-credentialed Cloudflare R2 bucket.
The superseded non-EU (`eu-west-2`/London) Neon project has also been
decommissioned by the sponsor directly.

**This phase is no longer BLOCKED in the sense the rest of this section
describes** — a target environment identifiably exists, in the correct
region, serving real (if sponsor-only) traffic. It is not, however,
GREEN in the sense Prompt 32 intended: it was not commissioned through
IAM review (§3), synthetic-candidate deployment (§5), or a formal
restore drill (§9) — those phases genuinely have not happened and remain
marked accordingly below. ADR-0018 remains formally unaccepted even
though its substance now largely exists in practice. Owner: Infrastructure
operator, Haroon Wahed (`PRODUCTION_OPERATIONS_RUNBOOK.md` service-ownership
table).

## 3. IAM and service identity review — STILL BLOCKED (resources now exist, but unauditable from here)

Resources now exist (§2), which changes what "BLOCKED" means here: this
is no longer blocked on *nonexistence*, it is blocked on this task's
*inability to audit* them. This task has no Render, Neon, or Cloudflare
account access — every fact about the live environment came from the
sponsor pasting logs/output, never from this task inspecting an IAM
console or policy document directly. One concrete, positive step did
happen: the quarantine object-storage credential was deliberately created
as a separate, bucket-scoped Cloudflare R2 Account API token rather than
reusing the main document-storage credential (`TARGET_ENVIRONMENT_INVENTORY.md`
§1c), which is exactly the least-privilege separation
`PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md` calls for. Beyond that one
item, this task cannot confirm whether the database role, the main storage
credential, or the Render service's own permissions follow least-privilege
— there is no IAM policy document to review, and no access to go look.

**BLOCKED — not because resources don't exist, but because this task
cannot independently verify their permission boundaries.**

## 4. Production configuration validation — SUBSTANTIALLY CONFIRMED (by inference, not direct inspection)

The repository's own `python manage.py check --deploy --fail-level WARNING`
gate already runs in CI against a synthetic production-shaped settings
profile and passed on PR #170's run (see §16) — that part is unchanged.

**What's new:** `config/settings_production.py` raises `ImproperlyConfigured`
at settings-import time — crash-looping the entire process, not failing one
request — if `DEBUG` is true, `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` are
empty, `DEFAULT_FROM_EMAIL`/`OPERATOR_ALERT_EMAIL` are placeholder values,
`APP_BASE_URL` isn't a valid public HTTPS origin, or `SECRET_KEY` is weak.
The live Render deployment has been running and serving real HTTP
responses throughout this conversation (`TARGET_ENVIRONMENT_INVENTORY.md`
§1c) — which is only possible if every one of those guards already passed.
That is an inference from the deployment's observed behavior, not a direct
inspection of Render's environment variables (this task still has none of
that access), but it is a real logical proof, not an assumption: a process
that violates any of those checks cannot boot at all under this codebase.
`SESSION_COOKIE_SECURE`/`CSRF_COOKIE_SECURE`/`SECURE_SSL_REDIRECT` are
hardcoded true in `settings_production.py` (not configurable, not
optional) whenever that module loads — so secure cookies and TLS redirect
are structurally guaranteed on this deployment, not merely hoped for.

Two configuration items were found actually wrong on the live deployment
and fixed in place, not just validated: `ALLOWED_HOSTS` (missing
`www.clmone.com`, causing every health check to fail) and
`CSRF_TRUSTED_ORIGINS` (still pointed at a leftover `*.onrender.com`
wildcard, or briefly a bare-domain value with no URL scheme). Both are
corrected now, per sponsor confirmation.

Confirmed structurally true regardless of target environment (unchanged
from before): external AI disabled by default and fail-closed
(`test_payrollminds_ai_governance_gate`, PM-UAT-012); inbound email has no
code path (PM-UAT-013); signature routes blocked under
`CONTROLLED_PILOT_ENABLED=true` (PM-UAT-014, now confirmed actually set
live, not just default — §2); external portals never invoked (PM-UAT-015).
MFA (PR #162) remains merged-but-inactive on this deployment — nothing in
this conversation activated it.

**Not verified even now: the exact live value of every environment
variable** — this task knows what was *reported* as set, not what a direct
inspection would show, because it has no access to perform one.

## 5. Deploy a synthetic commissioning candidate — SUPERSEDED BY A REAL DEPLOYMENT

This phase's original premise — deploy a synthetic candidate to prove the
mechanics work, since no real target existed — no longer applies. A real
deployment already existed independently of this process (§2) and has
since been redeployed multiple times in this task's presence (the
`DATABASE_URL` swap, then the `ALLOWED_HOSTS`/pilot-scope/`CSRF_TRUSTED_ORIGINS`/
storage fixes each triggered a fresh Render auto-deploy). Those were real
deployments of real, functional changes, not a synthetic exercise — but
this task still never held deployment credentials and never triggered any
of them directly; every deploy was the sponsor saving an environment
variable in the Render dashboard. **This task did not deploy anything
itself and does not claim to have.**

One real, unplanned deployment failure is on record: after PR #115 and
PR #162 were merged (each independently branching a new Django migration
off the same parent), the live deploy failed with Django's "multiple leaf
nodes" migration-graph error. It was fixed with a standard empty merge
migration (`contracts/migrations/0118_merge_20260808_1800.py`), pushed
directly to `main` outside a PR. This is disclosed here because it is a
genuine commissioning-relevant event — a merge-migration conflict this
task's own CI did not catch before either PR merged, only surfacing on
the real target's real deploy.

## 6. Target-environment smoke and synthetic UAT subset — PARTIALLY DONE, INFORMALLY

This task's own executable UAT suite (PR #169, 24/24, and its extension in
PR #170, §1) has still never been run against the live target — this task
has no credentials to do so. What did happen: the sponsor manually
confirmed `clmone.com` loads and is usable after each round of fixes,
including specifically testing a form submission to confirm
`CSRF_TRUSTED_ORIGINS` was corrected. That is real target-environment
smoke evidence, but it is manual and informal — a human clicking around,
not an automated, repeatable, evidenced test run. It does not substitute
for actually running the PayrollMinds UAT matrix against the live
deployment, which remains undone.

## 7. PostgreSQL backup — PARTIAL: a real dump was taken and verified, but no routine backup schedule exists

Update (2026-08-08): the sponsor-run database migration (§9, and
`TARGET_ENVIRONMENT_INVENTORY.md` §1c) means a real `pg_dump` of a real
PostgreSQL database with real data was, in fact, taken and successfully
used — twice (an initial dump, then a final `--clean --if-exists` pass
immediately before cutover to avoid losing anything written in between).
That is more than this phase had before, but it was a one-time migration
export, not a routine, scheduled backup process — `scripts/db_backup.sh`
still has never been run against either the old Render instance or the
new Neon one, and no backup ID/retention policy exists beyond Neon's own
built-in point-in-time recovery.

Neon's free-tier point-in-time recovery window is **6 hours** (verified
against current Neon documentation, not assumed) — materially short of a
meaningful RPO now that this database holds real (sponsor-only) usage
data. This is a genuine, unresolved gap, not a formality: if something
goes wrong more than 6 hours after it happens, Neon's own recovery cannot
help.

## 8. Object-storage backup/recovery evidence — PARTIAL: storage now exists, recovery mechanism unconfirmed

Object storage (Cloudflare R2) is now live for both released and
quarantine documents, each with its own bucket and scoped Account API
token (`TARGET_ENVIRONMENT_INVENTORY.md` §1c) — no longer unprovisioned.
What remains unconfirmed: whether bucket versioning, replication, or any
recovery mechanism has been enabled on either bucket. This task has no R2
dashboard access to check, and the sponsor was not asked this specific
question during the storage setup — it should be verified directly in the
Cloudflare dashboard.

## 9. Full restore drill — PARTIAL: the database migration functioned as a real, verified restore, but not a formal drill

The Render→Neon database migration (`TARGET_ENVIRONMENT_INVENTORY.md`
§1c) is, in substance, a real restore: a `pg_dump` from one live
PostgreSQL instance, restored via `pg_restore` into another, with
correctness independently verified — every one of 122 tables compared row
by row across both databases, all 34 non-empty tables matching exactly.
This is real, evidenced restore mechanics working against real
infrastructure with real data, not fabricated.

It falls short of a formal restore drill in specific, nameable ways: the
restore target was the new production database itself, not an isolated
recovery environment separate from production; no RPO/RTO timing was
measured; and it was prompted by a database migration need, not exercised
as a deliberate disaster-recovery test. No RPO/RTO number is reported here
— reporting one without a real timed drill would be fabricated evidence,
which this task's governing discipline prohibits throughout this
repository.

## 10. Restore security verification — NOT PERFORMED

§9's migration was verified for *correctness* (row counts matched) but not
specifically audited for *security* — e.g., whether the restored Neon
database ended up with the same access controls, roles, and privilege
boundaries as intended, or whether `--no-owner --no-privileges` (used in
the actual `pg_dump`/`pg_restore` commands) left anything under-permissioned
or over-permissioned relative to the design in
`PRODUCTION_ENVIRONMENT_VARIABLE_INVENTORY.md`. This still has not been
checked and remains open.

## 11. Monitoring and alerting proof — STILL BLOCKED

`SENTRY_DSN` is confirmed unset on the live deployment
(`TARGET_ENVIRONMENT_INVENTORY.md` §1c). `sentry-sdk` is already a runtime
dependency and the code silently no-ops without a DSN — so no error is
raised, but no error reporting exists either. The failure-mode and alert
tables in `PRODUCTION_OPERATIONS_RUNBOOK.md` remain a documented design,
not live, tested alerting. No synthetic test alert was generated because
there is no alert route to receive one. This is a real, live gap on a
system now handling real (sponsor-only) usage, not a hypothetical one.

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
and log-access control on the live target. A target now exists (§2), but
this task has no access to inspect Render's log retention/access settings
directly — this remains genuinely unverified, not resolved by the target
existing.

## 13. Operational rollback drill — STILL NOT PERFORMED

Deployments now genuinely occur on this target (§5 — each env-var change
triggered a real Render redeploy, including one that failed and was fixed
forward with a migration merge rather than rolled back). But a **rollback**
specifically — reverting to a previous known-good state after a bad
deploy — has never been exercised here. Every fix in this conversation
was applied forward, not rolled back to. The documented procedure
(`PRODUCTION_DEPLOYMENT_AND_ROLLBACK_RUNBOOK.md`) remains unexecuted
design.

## 14. Support and incident readiness — BLOCKING, named gaps (one closed)

Per `PRODUCTION_OPERATIONS_RUNBOOK.md`'s own service-ownership table and
explicit statement ("Named people, contact addresses, support hours, RPO/RTO,
and customer promises are intentionally absent until supplied and
approved"), and `RISK_REGISTER.md` PM-R11: no named pilot sponsor,
technical owner, support contact/channel, incident owner, privacy contact,
deployment approver, or backup/restore owner exists in this repository. No
person is invented here.

**Update, 2026-08-08:** one of these gaps is now closed. Haroon Wahed was
confirmed as the Infrastructure operator ("authorized to create production
resources and run backup/restore drills" — see
`PRODUCTION_OPERATIONS_RUNBOOK.md`'s service-ownership table and
`TARGET_ENVIRONMENT_INVENTORY.md` §1b). This covers PostgreSQL/Redis/
storage/DNS/TLS/backup ownership specifically. Engineering/Release
Authority, Security owner, Privacy/Product owner, PayrollMinds support
owner, incident owner, and privacy contact remain unnamed. **This phase
remains BLOCKING** on those still-open roles, not silently treated as
complete.

## 15. Data lifecycle and offboarding — DOCUMENTED PROCEDURE, UNREHEARSED

`PRODUCTION_DATA_PORTABILITY_AND_OFFBOARDING.md` (pre-existing in this
repository) documents the intended procedure for user disablement, access
revocation, controlled export, and workspace shutdown. `PM-UAT-011`
(access-revocation removes visibility) and `PM-UAT-007` (controlled export)
already prove the underlying application capabilities work at the code
level. Update (2026-08-08): real (if sponsor-only, non-customer) data does
now exist in the live database, migrated from the prior Render Postgres
instance (§7/§9) — the earlier premise that "no real data exists" is no
longer accurate. No real offboarding/retention rehearsal has been
performed against it, and none should be, absent an actual reason to
offboard or retire data right now.

## 16. Full infrastructure regression — GREEN (application layer), plus one real infrastructure incident

Run on the reconciliation candidate SHA (PR #170, this branch):
executable PayrollMinds UAT (24/24), browser regression, security battery,
PAR-SEC-002, tenant isolation, permission matrix, production deploy checks
(`manage.py check --deploy`), migration drift (zero), Bandit, TruffleHog,
pip-audit, npm-audit — see §18 of `PAYROLLMINDS_EXECUTABLE_UAT_EVIDENCE.md`
for the established pattern; this PR's own CI run reproduces it. No new
critical/high issue.

Since then, this task's own PR-merge activity produced a real
infrastructure-facing regression: merging PR #115 and PR #162 in the same
session, each adding an independent migration off the same parent, broke
the live target's deploy with Django's "multiple leaf nodes" error (§5).
This was not caught by this repository's CI — each PR's own CI run only
sees its own branch, not the combined graph both create once merged
together — and only surfaced against the real, live deployment. It was
fixed with a standard merge migration. This is disclosed as a genuine gap
in this task's own merge process, not smoothed over: application-layer CI
green does not, by itself, prove two independently-merged migrations
won't conflict against each other on a real target.

## Recommendation

**Neither GO nor NO-GO honestly describes the current state — a real,
live, pilot-scope-restricted deployment exists and is being used
(sponsor-only, so far), with specific, named gaps still open.** This
document's history:

Phase 1 (scope reconciliation) has been complete, real, and GREEN since
PR #170. Through most of this document's life, Phases 2–13 were correctly
reported **BLOCKED** because no real target environment existed anywhere
this task could see, and `TARGET_ENVIRONMENT_INVENTORY.md` §3 confirmed
this task's own credential-less state directly rather than assuming it.

**That premise changed on 2026-08-08.** A real deployment was discovered
mid-conversation — one the sponsor had built independently, outside this
document's own commissioning process (`TARGET_ENVIRONMENT_INVENTORY.md`
§1c). Once found, it was verified and hardened rather than left alone:
its database was migrated to the already-confirmed Neon instance and the
migration's correctness independently verified (§7/§9); missing
pilot-scope enforcement, host validation, and CSRF protection were
identified against this repository's own code and fixed (§4); a second,
separately-credentialed object-storage bucket was created for quarantine
documents (§8); and a real migration-graph deploy failure was caught and
fixed (§16).

**What is now GREEN or substantially answered:** Phases 1, 4 (by
inference from the live process's own successful boot, not direct
inspection), and most of §2's topology. **What remains genuinely open,
not GREEN:** Phase 3 (IAM/permission boundaries unauditable from this
task), Phase 6 (no automated UAT run against the live target, only manual
smoke checks), Phase 8 (document-storage recovery — R2 is live for both
released and quarantine buckets, but no bucket versioning/recovery drill
has been performed or confirmed configured), Phase 9 (the migration
functioned as a real restore but not a formal, timed drill into an
isolated target), Phase 10 (restore security never specifically audited),
Phase 11 (no monitoring — `SENTRY_DSN` unset), Phase 13 (no rollback ever
exercised, only forward fixes).

**Named-ownership gaps (Phase 14), stated precisely rather than lumped
together:** the **backup owner** role is the one that is actually
closed — Haroon Wahed is named as Infrastructure operator, explicitly
covering PostgreSQL/Redis/storage/DNS/TLS/backup. Still open and unnamed:
**support owner** (PayrollMinds customer communications), **incident
owner** (security/availability incident response), **privacy owner**
(Privacy/Product — retention, deletion, export approval), and
**deployment approver** (Engineering/Release Authority — who signs off on
a release reaching this environment).

**Onboarding blockers, explicitly, in one place:** routine backup/recovery
readiness (Phase 7 — only a one-time migration dump exists, Neon free-tier
PITR is 6 hours), an isolated PostgreSQL restore drill (Phase 9 — the
migration proved dump/restore mechanics work, not a drill into a separate
recovery target with timed RPO/RTO), a document-storage recovery drill
(Phase 8), monitoring/alerting (Phase 11), and the four still-unnamed
operational owners above (support, incident, privacy, deployment
approver). Redis (`REDIS_URL` unset) is **not** listed here — it degrades
gracefully to synchronous background-job execution rather than blocking
anything, so it is a real gap worth fixing but not a release blocker.

**Practical read:** this is a reasonable, honestly-configured pilot
deployment for continued sponsor-only use and further hardening. It is
not yet ready for real PayrollMinds customer users under this document's
own bar — the blockers listed above are the specific, named things that
would need to close first, not vague caution.

No infrastructure evidence in this document — deployment SHA, backup ID,
restore timing, RPO/RTO, monitoring test, or alert delivery — is
fabricated. Where evidence could not be produced honestly, or could only
be inferred rather than directly observed, this document says so
explicitly (§4, §6, §9) rather than either inventing it or refusing to
update a now-stale blanket verdict.
