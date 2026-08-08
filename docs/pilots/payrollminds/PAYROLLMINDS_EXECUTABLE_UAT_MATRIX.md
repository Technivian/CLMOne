# PayrollMinds executable UAT matrix

**Status:** Draft, executable. This matrix is implemented, not aspirational —
every scenario below is a real `TestCase` method in
`tests/test_payrollminds_executable_uat.py` and is driven through the same
HTTP views / service-layer entrypoints a real pilot user or the pilot's
governed intake path would use. No scenario here bypasses the acceptance
action itself with a direct model write (fixture setup for actors,
organizations, and cross-workspace comparison data is the only direct-model
use, consistent with the rest of this repository's security test suite).

This is **not production authorization**. See
`PAYROLLMINDS_EXECUTABLE_UAT_EVIDENCE.md` for the recommendation.

## Legend

- **Actor** — the synthetic user role driving the scenario.
- **Maps to** — the corresponding scenario ID in the historical
  `UAT_SCRIPT.md` (PR #152), where one exists, for traceability. `NEW` marks
  a scenario with no historical analog.

## Scenarios

| ID | Business purpose | Actor | Maps to |
|---|---|---|---|
| PM-UAT-001 | Authorized synthetic user authenticates and reaches only the permitted pilot workspace/navigation. | owner | UAT-01 (partial) |
| PM-UAT-002 | Contract intake: quarantine → clean scan → explicit release atomically creates canonical Contract, Document, immutable DocumentVersion, and provenance. | owner | UAT-01, UAT-11 |
| PM-UAT-003 | Metadata/review: released contract carries human-entered, non-authoritative-suggestion metadata and a DocumentReviewRun the user can inspect. | owner | UAT-07/08/09 |
| PM-UAT-004 | Workflow progression: the correct, version-pinned NDA self-serve template governs the instance; the required Legal Review step is present and correctly evaluated; a valid human action (section confirmation) progresses the workflow; an invalid progression (submitting a step the risk tier does not require) is rejected. | owner | UAT-10 (progression half) |
| PM-UAT-005 | Authorized search finds the released contract; a second, unrelated ordinary member's identical query returns zero results, facets, and counts. | owner, member-b | UAT-12–15 |
| PM-UAT-006 | Operational tracking: a renewal/notice deadline is recorded against the contract, appears on the obligations workspace, and is audit-evidenced. | owner | UAT-16–18 (data-model half) |
| PM-UAT-007 | Controlled export: owner exports the organization activity CSV (audit-logged, purpose-bound); an ordinary member is denied; a second workspace's export never contains this workspace's rows. | owner, member-b | UAT-19/20 |
| PM-UAT-008 | Private access: a second ordinary member who neither owns nor created the contract cannot view, search, or directly access it despite active, non-privileged membership in the same workspace. | member-b | UAT-12 |
| PM-UAT-009 | Cross-workspace access: a synthetic user in a wholly separate organization cannot discover or access the contract by any surface. | outside-org user | UAT-13 |
| PM-UAT-010 | Direct identifier access: knowing the Contract/Document primary key does not bypass authorization for an unrelated member. | member-b | UAT-12 (direct-URL half) |
| PM-UAT-011 | Access revocation: deactivating a member's workspace membership immediately removes visibility of a record that member previously owned. | member-b | UAT-14 |
| PM-UAT-012 | External AI: contract-extraction AI is refused (403, manual-fallback message, provider never called) even when `GEMINI_AI_ENABLED`/`GEMINI_API_KEY` are configured, because the controlled-pilot boundary is fail-closed by design. | owner | UAT-10 (negative half) |
| PM-UAT-013 | Inbound email ingestion: no URL, view, or `DocumentIngestionAttempt` source exists for email-derived intake; the only ingestion entrypoint is the governed upload API. | n/a (structural) | NEW |
| PM-UAT-014 | Signature: with no `ESIGN_PROVIDER` configured (the pilot's actual deployment posture), signature dispatch resolves to the inert null provider — no live external delivery call is made. | owner | NEW |
| PM-UAT-015 | External portal/integration: no `WebhookEndpoint` exists and no `WebhookDelivery` is ever created for the pilot workspace across the full UAT run. | n/a (structural) | NEW |
| PM-UAT-016 | Invalid/malicious file: a scanner-flagged malicious upload is quarantined, never releasable, and never becomes a canonical Document/Contract. | owner | UAT-05/06 |
| PM-UAT-017 | Audit chain: every material action on the happy-path contract (intake release, document/version creation, section confirmation, export) produces an append-only, hash-chained `AuditLog` entry with actor, workspace, object identity, and timestamp. | owner | UAT-20 |
| PM-UAT-018 | Isolation/cleanup: the UAT workspace (`payrollminds-uat`) is a dedicated synthetic namespace distinct from other fixtures (`payrollminds-pilot`, `payrollminds-demo`, browser E2E seed data); UAT records are invisible from every other workspace's queries; per-test transactional rollback and temporary storage directories leave no residue between runs. | n/a (structural) | NEW |

## Deliberately excluded (infrastructure-blocked, not executable as a Django `TestCase`)

Carried forward, unresolved, from `UAT_ACCEPTANCE_SHEET.md` — these require a
real isolated pre-production environment, not a unit-test process, and this
suite does not claim to close them:

| Historical ID | Scenario | Why excluded here |
|---|---|---|
| UAT-22 | Backup/restore | Requires a real PostgreSQL + object-store restoration drill against isolated infrastructure. |
| UAT-23 | Production-like deployment | Requires an isolated pre-production environment with real TLS/IAM/worker/monitoring. |
| UAT-24 | Offboarding/export rehearsal | Requires an authorized target-environment rehearsal with real customer terms; no such environment exists for this pilot yet. |

Also out of scope by pilot charter, not by test limitation: payroll/employee
data processing, external portals/e-signature *product activation* (as
opposed to the technical inert-default proof in PM-UAT-014/015), SAML/SCIM,
and any change to roles, permissions, or canonical workflow authority. See
`PILOT_SCOPE.md`.

## Synthetic actors

All actors are created fresh per test method (Django `TestCase`, one DB
transaction per test, rolled back automatically):

- **owner** — `OrganizationMembership.Role.OWNER` in `payrollminds-uat`.
- **member-b** — `OrganizationMembership.Role.MEMBER` in `payrollminds-uat`; owns and creates nothing.
- **outside-org user** — `OWNER` of a wholly separate organization, `payrollminds-uat-other`.

No real name, email, or credential is reused between runs; every identifier
carries a `payrollminds-uat` prefix so accidental collision with seeded demo
data, browser E2E fixtures, or other security suites is structurally
impossible (see PM-UAT-018).
