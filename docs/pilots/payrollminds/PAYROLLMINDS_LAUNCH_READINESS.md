# PayrollMinds Production Pilot — Launch Readiness

**Audit date:** 2026-08-02  
**Assessment:** controlled production pilot, not an enterprise launch  
**Verdict:** **NO-GO**

This is a repository-readiness assessment, not production-release evidence. It
does not authorize a deployment, use real PayrollMinds data, or supersede the
active Governance Charter or accepted decision records.

## Executive verdict

The repository contains useful, tested building blocks for a constrained
contract-record pilot: tenant-scoped query helpers, contract and document
records, immutable document versions, mandatory contract provenance, manual
and bulk document intake, review states, search, deadlines/obligations,
authentication controls, and a tamper-evident audit-chain implementation.

It is not eligible for the proposed production pilot. The evaluated checkout is
not a release candidate: it is **32 commits behind `origin/main`** and has a
large dirty working tree containing unrelated product, UI, governance, and
untracked changes. More importantly, the present `can_access_contract_action`
policy lets every active workspace member view every contract in that workspace.
That does not meet the pilot's private-by-default, named-user and object-level
access requirement. The included deployment blueprint is explicitly a
demo/evaluation configuration, uses an automatically deployed `main`, runs
without workers or durable operational evidence, and seeds demo data at start.

No real PayrollMinds data may be loaded. Production activation must stop until
the critical blockers below are closed on an immutable, reviewed release SHA
and the required production evidence exists.

## Repository state and HEAD SHA

| Item | Observed fact |
|---|---|
| Checked-out branch | `codex/repository-essentials-phase1-baseline` |
| HEAD | `6ff28f2013d7236850f31b5395adc6b22665482d` — `docs: plan repository essentials phase 1` |
| Relationship to deployment branch | `git rev-list --left-right --count HEAD...origin/main` returned `0 32`: this checkout is 32 commits behind `origin/main`. |
| `origin/main` observed tip | `4d194dcc` — merge of document-ingestion security work. |
| Worktree | Dirty before this report. It contains modified code/configuration/templates/tests and untracked import, presentation, and documentation artifacts. Those changes were not authored, modified, staged, committed, rebased, or merged by this audit. |
| Open PRs observed | #133, #123, and #115 were open when queried. No PR was merged. |
| Migrations in local development SQLite | `showmigrations --plan` reported all applied through `contracts.0115_exception_correlation_id`. This is local-state evidence only. |

## Current deployment state

**Not verified.** The repository contains `render.yaml`, but its own header
calls it a free demo/evaluation Blueprint, not production. Its web service:

- deploys the `main` branch automatically;
- invokes `migrate` and `seed_mvp_demo` in the web process start command;
- has no worker or cron resource in the Blueprint;
- states that background jobs use a synchronous/in-process fallback and email
  uses the console backend; and
- relies on operator-supplied object-storage and alert configuration.

Production settings do fail closed for several inputs: PostgreSQL, S3-backed
media storage, a strong secret, HTTPS application URL, allowed hosts, trusted
origins, real sender address, and an operator-alert address. A local
`check --deploy` could not initialize because `APP_BASE_URL` was not a valid
HTTPS production origin. That is expected in an unconfigured local checkout;
it is not evidence that a production environment is configured correctly.

No deployed environment, managed secret store, storage bucket policy, Redis,
SMTP provider, Sentry/monitoring configuration, backup run, restoration drill,
operator log, GitHub CI result, or reviewed deployment SHA was made available
to this audit.

## Pilot scope assessed

Assessed scope: one isolated PayrollMinds workspace; up to 10 named users;
up to 50 initial contracts; manual and bulk upload; email forwarding only if
proven; provenance; human-confirmed metadata; named access; search; expiry,
renewal and notice reminders; audit evidence; and controlled exports.

Excluded for this assessment: payroll calculations or files, salary or employee
bulk data, external users, signatures, advanced negotiation, SAML/SCIM,
unproven integrations, advanced analytics, and autonomous AI decisions.

Email forwarding is code-present but disabled by default
(`EMAIL_FORWARDED_INGESTION_ENABLED=false`). It is not launch scope until its
token, forwarding provider, abuse controls and failure operation are separately
proven. AI must remain disabled for launch; setting `GEMINI_AI_ENABLED=false`
is the available deployment-level kill switch.

## End-to-end lifecycle map

| Pilot step | Current entry/service/persistence | Authorization and audit | Evidence and gap |
|---|---|---|---|
| Upload / bulk upload | `document_upload_api`, `document_mass_import_api`; `DocumentIngestionService`; `Contract`, `Document`, `DocumentVersion`, `DocumentReviewRun` | Login required for browser upload; org resolved from membership; `document.ingested` and `document.metadata_extracted` events | Extension and 50 MB size checks exist. No malware scanner, content-signature validation, or quarantine boundary exists in this checkout. |
| Persist source/version | `create_document_version`; `Document` and `DocumentVersion` | Tenant assertion in service; version audit events | Focused document version/download tests pass. Private S3 is configuration-required, not deployment-proven. |
| Metadata extraction / entry | `agreement_metadata_extract`, review workspace and `contract_review_confirm_api` | Logged as unverified/review state | Deterministic extraction hints and confirmation path exist. The canonical Property Definition object is not implemented; `FieldDefinition` is workflow/template scoped. |
| Create durable contract record | import lifecycle/provenance services; `Contract` | Provenance fields lock after save; provenance events | `IMPORT_INBOUND`/`UPLOAD` origins are supported and tests pass. Current import work is uncommitted in this checkout. |
| Assign owner/access | `OrganizationMembership`, owner field, `can_access_contract_action` | Membership is checked server-side | **View/comment/AI access is granted to every active member.** No private-per-record ACL/named-user enforcement was found. |
| Find contract / dates | repository/global search; `Deadline`, obligations workspace | Tenant-scoped querysets and membership filtering | Focused search and obligation tests pass. Search meets workspace isolation, not the required object-level confidentiality policy. |
| Reminders | `run_obligation_reminders`, `send_contract_reminders`, Django RQ/job records | Scheduled-job/audit patterns exist | Local tests cover model/service behavior. No production worker/scheduler, SMTP delivery, retry/dead-letter, or alert evidence was provided. |
| Export / audit inspection | organization-security export and `AuditLog`/chain verification | Owner/admin export path is tested; audit events chain by organization | Export authorization tests pass. End-to-end production export logging and PostgreSQL trigger evidence are not demonstrated. |

## Red / amber / green release matrix

| Gate | Status | Evidence |
|---|---|---|
| Workspace isolation | Green in focused tests; Red for release | Tenant helpers and cross-tenant tests pass, but no immutable release SHA/CI evidence exists. |
| Object-level/private access | **Red** | `contracts/permissions.py` grants view/comment/AI to any active workspace member. |
| Upload-to-record / provenance | Amber | Tested code exists, including bulk intake; current implementation is dirty and lacks malware/quarantine enforcement. |
| Metadata human verification | Amber | Review states and confirmation exist; canonical property registry is absent and AI/provider controls are unproven. |
| Search / filters | Amber | Tested tenant filtering exists; object-level filtering cannot be claimed. |
| Dates / reminders | Amber | Models/services/tests exist; production scheduler, email delivery and retry evidence is absent. |
| Audit history / integrity | Amber | Chain and append-only design/tests exist; audited coverage and PostgreSQL production evidence are absent. |
| Export control | Amber | Owner/admin export authorization test passes; release/deployment audit evidence absent. |
| Authentication / sessions / MFA | Amber | Password, rate limit, session and MFA tests exist. MFA is available/configurable, not verified as enforced for PayrollMinds. |
| File safety / private storage | **Red** | Extension/size checks and private-S3 configuration exist; no malware/content-signature scan or deployed bucket evidence. |
| AI safety | Amber when disabled; **Red if enabled** | Global deployment kill switch exists. No workspace-level policy, data-processing/retention evidence, or production provider review was supplied. |
| Privacy | **Red** | Product surfaces exist, but no DPA, subprocessors, data location, retention/deletion, offboarding or customer-data handling evidence was supplied. |
| Operations / backup / restore | **Red** | Scripts and scheduled workflow definitions exist; no successful production run or restoration evidence was supplied. |
| Quality / release control | **Red** | `make check` passes; full-suite run did not complete cleanly and the release candidate is neither clean nor reviewed. |

## Critical security findings

| ID | Severity | Evidence | Affected capability | Smallest safe remediation | Likely files/modules | Dependency | Stop launch |
|---|---|---|---|---|---|---|---|
| PM-SEC-01 | Critical | `can_access_contract_action()` returns `True` for view/comment/AI for every active organization member. | Private contracts, restricted metadata, search, exports and AI context | Do not activate with more than one user until an accepted authorization decision and server-side object ACL/read-filter implementation with revocation, search, count, audit and export negative tests are complete. | `contracts/permissions.py`, tenancy/query services, search/export/API/views/tests | Approved authority for read-enforcement policy; currently PDR-0008 is Proposed. | Yes |
| PM-SEC-02 | Critical | No `malware`, `clam`, `virus`, or implemented quarantine scan was found in current upload code; `documents_ai.py` checks extension and size only. | Manual, bulk and forwarded ingestion | Keep real uploads closed. Merge/review the current main's approved ingestion boundary or implement a quarantine-first scanner/type-validation path with fail-closed tests and operator procedure. | Document ingestion/API/storage/worker configuration | Clean release candidate and scanner/infrastructure evidence | Yes |
| PM-SEC-03 | Critical | `HEAD` is 32 commits behind `origin/main`; worktree is dirty with unrelated changes. | Every pilot capability | Create a clean branch from the intended immutable release SHA; isolate only pilot blocker fixes; obtain required GitHub reviews and green CI for that exact SHA. | Git/GitHub/release process | Human release authority | Yes |
| PM-SEC-04 | High | S3 configuration defaults private and signed, but actual bucket settings and production download behavior were not inspected. | Document confidentiality | Provide private-bucket/IAM evidence and a deployed signed-download/access-revocation test. | Production config, storage provider, document download tests | Production environment | Yes |
| PM-SEC-05 | High | `render.yaml` is a demo/evaluation blueprint with auto-deploy and demo seeding. | Production isolation / operational integrity | Replace or separately configure a controlled production deployment: no demo seed on boot, explicit migration job, workers, alerts and approved SHA deploy. | Deployment infrastructure / `render.yaml` | Operator and release authority | Yes |

## Privacy and AI findings

- AI output is represented as extraction spans, review findings and review-run
  metadata rather than an implemented canonical `AISuggestion` aggregate. The
  accepted data/AI documentation requires source, policy version, model,
  confidence, reviewer, disposition, authoritative value and audit evidence.
  Current review states support human confirmation, but no complete deployed
  evidence demonstrates every required field.
- Gemini configuration is environment-wide. `GEMINI_AI_ENABLED=false` is a
  safe launch default and is required for this pilot. There is no demonstrated
  PayrollMinds workspace-level opt-in/disablement, redaction layer, provider
  retention/data-location record, or proof that prompt/document content is
  excluded from logs.
- The repository has privacy, retention, legal-hold, subprocessor, transfer
  and DSAR surfaces. It does not provide the required completed customer DPA,
  subprocessor list, data-location statement, retention/deletion schedule,
  offboarding/export process, or signed data-processing decision for real
  PayrollMinds documents.
- The pilot’s exclusion of payroll files, salary data and bulk employee data
  is policy-only in the inspected code. Implemented generic document upload
  allows several textual/file extensions and does not classify or reject those
  data classes.

## Operational findings

- Framework/runtime: Django 5.2.16 in declared requirements; current README
  still names 5.2.5, so documentation drift exists. Development uses SQLite;
  production settings require PostgreSQL.
- Background work uses django-rq/Redis when configured and synchronous fallback
  otherwise. The included free deployment blueprint lacks worker/cron resources.
- SMTP is only real when host configuration exists; otherwise it is console
  email. Email forwarding is off by default.
- Logging is structured, and Sentry is optional when a DSN exists. Monitoring
  definitions and health checks exist, but no live alert/error telemetry was
  available.
- `scripts/db_backup.sh` verifies a custom Postgres dump and optional offsite
  upload. `scripts/db_restore_drill.sh` supports a scratch restore. These are
  capabilities, not completed backup/restoration evidence.
- A GitHub backup scheduler and release-evidence workflow exist, but no run
  status or artifact for the intended release SHA was provided.

## Test inventory and exact results

| Command | Result | Scope / limit |
|---|---|---|
| `make check` | **Pass** — `System check identified no issues (0 silenced).` | Test settings, in-memory SQLite. |
| Focused Django selection of 24 modules for tenancy/mutation, permissions, exports, search, document storage/versioning/ingestion/import, obligations, AI extraction/review, audit, lifecycle, session/MFA/security, restore and observability | **Pass (exit status 0)** | Negative-path 404/403/503 logs are exercised expected behavior. It is not a deployment or PostgreSQL proof. |
| `make test` | **Not green / not a usable release result.** Captured run showed failures and errors before no clean completion summary was available from the invocation. | The repository instructions already identify active lifecycle `status`/`lifecycle_stage` refactor drift and pytest import drift. Regardless of attribution, a full-green quality gate is absent. |
| Production `check --deploy --fail-level WARNING` with local placeholder configuration | **Unavailable by design** — failed configuration bootstrap because `APP_BASE_URL` was not a valid HTTPS production origin. | Does not test an actual production environment. |
| `.venv/bin/pip-audit -r requirements/runtime.txt` | **Unavailable** — installed executable has a stale interpreter path to the former `CMS-Aegis` checkout. | CI defines pip-audit/bandit/npm scan jobs; current local virtualenv must be repaired or CI results attached. |

Required invariant status:

| Invariant | Status |
|---|---|
| Tenant isolation | Focused tests passed. |
| Published/workflow immutability | Not independently re-run in this audit. |
| Access revocation | Membership deactivation exists; private record-level revocation is blocked by PM-SEC-01. |
| Audit append-only | Model/chain and focused audit tests passed; PostgreSQL production trigger evidence not obtained. |
| AI non-authority | Human-review states and focused AI tests passed; launch must keep AI disabled. |
| Workflow-version pinning | Not independently re-run in this audit. |
| Contract-record provenance | Focused provenance tests passed. |
| Obligation ownership | Focused obligation tests passed. |
| Permission-aware search/export | Workspace-level tests passed; record-level confidentiality remains blocked by PM-SEC-01. |

## Data migrations and rollback status

The local SQLite database reports migrations applied through `contracts.0115`.
That is not deployment evidence and does not show compatibility with the
production database. Existing migration/backup/restore scripts provide a
starting procedure only. No production backup, pre-migration snapshot,
staging migration, restoration drill, compensating plan, or post-migration
tenant-integrity evidence was supplied.

The pilot must use an explicit migration plan for the immutable release SHA:
backup, restore verification, migration preflight, migration execution,
tenant/provenance integrity check, smoke test, abort conditions and a
forward-only compensating action for any irreversible schema change.

## Existing useful capabilities

- `Organization` and `OrganizationMembership` tenancy, active membership and
  owner/admin/member roles.
- Contract records, document records and immutable document versions.
- Contract provenance fields and a governed provenance service supporting
  workflow, manual, upload and imported records.
- Browser upload, bulk import and a disabled-by-default forwarded-email path.
- Review states and a human confirmation route for extracted metadata.
- Tenant-scoped search, document download protections, reminders/deadlines and
  obligations workspace.
- Audit logging with per-organization chained hashes and append-only migration
  support.
- Production settings fail closed for several essential configuration values.
- CI definitions for guardrails, security scans, backup scheduling and release
  evidence collection.

## Excluded or unstable capabilities

- Email forwarding: disabled and unproven.
- AI: excluded; launch with `GEMINI_AI_ENABLED=false`.
- E-signature: excluded; default provider is the simulated `null` provider.
- SAML/SCIM, Salesforce, NetSuite, webhooks and other integrations: excluded.
- External collaboration portal: excluded.
- Advanced analytics and negotiation: excluded.
- Current dirty/uncommitted import and UI work: excluded until independently
  reviewed and merged into a clean release candidate.

## Critical launch blockers

| ID | Severity | Evidence | Affected pilot capability | Smallest safe remediation | Likely files/modules | Dependency | Stop launch |
|---|---|---|---|---|---|---|---|
| PM-SEC-01 | Critical | `contracts/permissions.py` grants view/comment/AI to every active member. | All contract/document access, search, exports, AI context | Governed authorization design and fully tested server-side ACL/read filtering. | `permissions.py`, tenancy/search/export/API/views/tests | Accepted policy/implementation authority | Yes |
| PM-SEC-02 | Critical | Current upload code has only extension/size checks; no scanner/quarantine implementation was found. | Any real document upload/import | Quarantine-first intake, scan/type validation and failure operation. | Document ingestion/API/storage/worker services | Clean SHA; scanner/storage service | Yes |
| PM-REL-01 | Critical | `HEAD...origin/main` is `0 32`; working tree is dirty. | Entire launch | Clean immutable candidate from intended `main` SHA, review and CI. | Git/GitHub/release process | GitHub release process | Yes |
| PM-OPS-01 | Critical | No deployment, backup, restoration, monitoring or operator evidence was supplied. | Recovery and safe operation | Isolated pre-production rehearsal and recorded successful controls. | Deployment/monitoring/backup infrastructure and runbooks | Operator/infrastructure owner | Yes |
| PM-QLT-01 | Critical | `make test` did not yield a clean completion; failures/errors were captured. | Quality gate | Triage and fix/re-baseline every failure; retain CI evidence for final SHA. | Affected test modules and lifecycle refactor implementation | Clean release candidate | Yes |
| PM-PRIV-01 | High | No DPA, retention/offboarding, data-location or payroll-data exclusion evidence. | Lawful processing | Complete human/customer privacy controls and documented intake exclusion. | Privacy policies, contracts, intake controls and operator runbook | Product/privacy/customer | Yes |
| PM-AI-01 | High | Provider controls/retention evidence is absent; current kill switch is deployment-wide. | AI metadata suggestions | Keep AI disabled for pilot; do not compensate with an unapproved AI path. | Settings, AI services and privacy controls | Deployment environment | Yes if AI enabled; no if disabled |
| PM-OPS-02 | High | `render.yaml` labels itself demo/evaluation-only; no worker/cron and demo seed on boot. | Reminders, operations, data integrity | Dedicated production deployment configuration and rehearsal. | `render.yaml`, deployment resources, job/email configuration | Infrastructure owner | Yes |

## Recommended minimum PR sequence

1. **Release-baseline PR:** create a clean branch from the selected current
   `origin/main` SHA; include no application change; establish CI, PR review,
   deployment target and evidence record. Do not reuse this dirty checkout.
2. **Object-access PR:** only after the required PDR/implementation authority;
   introduce server-side private record/document access and revocation,
   permission-aware search/count/export/AI filters, and negative tests.
3. **Safe-ingestion PR:** bring reviewed quarantine/malware/content-validation
   controls to the candidate, make all document channels fail closed, and add
   storage/scanner operational evidence. Do not enable email forwarding.
4. **Pilot operations PR/configuration:** production-only configuration with
   PostgreSQL, private S3, Redis workers/scheduler, SMTP, monitoring/alerts,
   secrets, backup/restore procedure, and demo-seed removal.
5. **Release-evidence PR/package:** full test stabilization, pre-production
   synthetic UAT, access-revocation and export evidence, migration/rollback
   rehearsal, backup restoration, privacy package references and signed-off
   operator record. It contains no activation.

## Dependencies between PRs

```text
clean immutable baseline
        |
        +--> authorization authority --> object-level access --> safe ingest
        |                                                \--> search/export/AI negative tests
        |
        +--> production infrastructure --> migration/backup/restore rehearsal
                                                    |
full green CI + synthetic UAT + privacy package ------+--> release evidence --> human go/no-go
```

## Items requiring human or customer action

- Product owner: confirm the final narrow scope, allowed agreement types,
  named users, data categories and that AI remains off.
- Security/privacy owner and PayrollMinds: execute/approve the DPA, subprocessors,
  data location/transfers, retention/deletion, offboarding/export and incident
  contact arrangements.
- Infrastructure operator: provision isolated production and pre-production
  environments; managed PostgreSQL, private object storage, Redis, SMTP,
  monitoring/error reporting and backup storage; supply no secrets to Git.
- Release authority: select the release SHA, approve applicable GitHub PRs,
  validate CI for the unchanged SHA and retain deployment/operator records.
- Customer launch owner: approve first synthetic UAT then approved first batch;
  ensure no payroll/employee datasets are ever uploaded.

## Proposed go/no-go criteria

**GO only when all are true:**

1. A clean reviewed release SHA is deployed to isolated pre-production and all
   mandatory CI is green for that unchanged SHA.
2. Private-by-default record/document access, access revocation, search/count,
   export and AI-context negative tests pass against that candidate.
3. Ingestion is quarantined/scanned/type-validated, private storage is proven,
   and no email forwarding or AI is enabled unless separately evidenced.
4. Synthetic PayrollMinds UAT proves upload → record/provenance → human
   metadata verification → owner/access → search → dates/reminder → audit and
   controlled export, including failure/retry states.
5. Production configuration, monitoring, backup and successful restoration,
   migration/compensating plan, rollback runbook, incident/support owners and
   a named operator record exist.
6. Privacy/customer documentation is complete and the prohibited-data rule is
   operationally enforced.
7. Required independent GitHub reviews and release evidence satisfy the active
   Charter. A feature flag alone does not grant authority.

Otherwise the decision is **NO-GO**.

## Evidence appendix with commands and outputs

| Command | Material output |
|---|---|
| `git status --short --branch` | Branch was dirty; see repository-state section. |
| `git rev-parse HEAD` | `6ff28f2013d7236850f31b5395adc6b22665482d` |
| `git rev-list --left-right --count HEAD...origin/main` | `0 32` |
| `gh pr list --state open --limit 30` | Open PRs #133, #123 and #115 observed. |
| `make check` | Passed: zero Django system-check issues. |
| Focused `manage.py test` selection | Passed with exit status 0; covered 24 listed test modules. |
| `make test` | Did not provide a clean completion; failures/errors were captured during run. |
| `manage.py showmigrations --plan` with development SQLite | All local migrations through `0115` shown applied. |
| Production `check --deploy` with incomplete local settings | Failed bootstrap at invalid `APP_BASE_URL`; no production claim. |
| `.venv/bin/pip-audit -r requirements/runtime.txt` | Could not execute because of a stale virtualenv interpreter path. |
| Repository inspection (`rg`, settings/services/workflows) | Basis for lifecycle, access, ingestion, operations and security findings. |

## Files inspected

- `AGENTS.md`, `README.md`, `docs/README.md`, `DECISIONS.md`, existing pilot
  and readiness reports.
- Active Charter, accepted product/architecture/engineering/roadmap documents,
  and applicable decision records under `docs/governance/decisions/`.
- `config/settings_base.py`, `config/settings_production.py`,
  `config/feature_flags.py`, `render.yaml`.
- `contracts/models.py`, `contracts/permissions.py`, `contracts/tenancy.py`,
  `contracts/middleware.py`, `contracts/urls.py`.
- Contract provenance, document version, document ingestion, import, search,
  audit, obligations, lifecycle and related view/API services.
- Relevant tests, scripts, GitHub workflows and pull-request template.

## Audit boundary

No product code was changed, no migrations were applied, no real customer data
was accessed or loaded, and nothing was merged. This report is the only change
made by this audit.
