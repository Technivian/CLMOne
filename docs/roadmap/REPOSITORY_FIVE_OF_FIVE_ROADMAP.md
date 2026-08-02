# Contracts Repository — Path to 5/5 Maturity

**Status:** Proposed — planning only; this document does not authorize
capabilities, production activation, schema changes, permissions, or data
migration.

**Scope:** The Contracts repository at `/contracts/repository/`, its record
discovery, import, bulk operations, key-date operation, and supporting
repository intelligence. It is not a plan to turn My Work into a second
repository or to add external sharing, live e-signature, SSO, OCR, or AI to
the first implementation tranche.

**Companion:**
[`REPOSITORY_ESSENTIALS_PHASE_1.md`](REPOSITORY_ESSENTIALS_PHASE_1.md) remains
the detailed baseline and first-slice boundary. This document sequences the
full maturity path and defines what evidence is required before a 5/5 claim.

## 1. Outcome and maturity definition

A **5/5 repository** is a production-proven, access-safe contract system of
record. An authorized legal-operations user can:

1. bring an inventory in through a governed, reversible migration path;
2. find authorized records by reliable operational metadata and document
   content without leaking restricted existence or metadata;
3. understand the record's provenance, lifecycle, relationship, documents,
   key dates, and accountable next action;
4. make governed bulk changes that respect lifecycle and access rules; and
5. demonstrate operational evidence for performance, recovery, audit,
   security, and support.

The repository will remain the complete accessible inventory. My Work remains
the personal action queue, Command Center remains the organization-wide
portfolio surface, and specialist workspaces retain deep operational work.

## 2. Starting point

The current repository is a **3/5 controlled-demo and pilot surface**, with:

- a canonical tenant-scoped list, filters, sorting, pagination, column
  controls, saved views, export, and record navigation;
- lifecycle-guarded status and stage bulk changes;
- key-date, document-state, assignee, and activity projections; and
- focused repository tests and synthetic PayrollMinds fixtures.

It is not 5/5 because import is not yet a privileged end-user workflow,
search/facets are not yet protected by an authorized object-level policy
evaluator, full-text discovery and canonical relationships are absent, and
production scale, restore, and release evidence are incomplete. The focused
repository suite is green, including regression coverage for compact sticky
columns and distinct Stage/Status sorting.

## 3. Sequenced delivery tranches

Each tranche is separately planned, reviewed, tested, and released. Later
tranches do not start merely because an earlier feature flag exists.

| Tranche | Objective | Main delivery | Explicit boundary | Exit evidence |
|---|---|---|---|---|
| R0 — Foundation | Make the existing inventory dependable and coherent | Green focused suite; stage/status language audit; repository design-system cleanup; accessible loading, empty, error, and no-access states | No new business capability or permission change | Reviewed SHA, green CI, desktop/mobile/keyboard screenshots, accessibility checks |
| R1 — Governed import | Make an empty private workspace useful on day one | Default-off, create-only CSV import with template, dry-run, mapping, diagnostics, duplicates, confirmation, provenance, audit, and compensating reversal | Synthetic data only; no documents, sharing, AI, OCR, SSO, e-sign, or automatic reminders | Import isolation/authorization/no-mutation/duplicate/lifecycle/audit/reversal tests and named-environment operator record |
| R2 — Access-safe repository intelligence | Make metadata discovery trustworthy | Authorized policy evaluation before list, ranking, counts, facets, pagination, saved views, export, and autocomplete; deterministic metadata search and health behavior | No document text or semantic search until derived-data design is approved | Denied-object, facet/count, Ethical-Wall, stale-policy, export, and no-leak negative tests; security review |
| R3 — Relationship and data-quality foundation | Make records understandable as commercial relationships | Approved entity/contract-relationship decision; canonical relationship projection; data completeness, conflict, stale-value, and duplicate indicators | No parallel Entity, Contract, or Property model; no unapproved backfill | ADR/PDR approval, additive migration/reversal plan, relationship-cycle/isolation/provenance tests |
| R4 — Time-bound operation | Make dates actionable and accountable | Canonical renewal/notice/key-date calculation, owned obligations, reminder policy, escalation, delivery evidence, and My Work linkage | Automation stays default-off until release authority is satisfied | Boundary/time-zone/idempotency/revocation/delivery-failure tests, schedule audit, operator runbook |
| R5 — Document discovery and scale | Make discovery complete and dependable at target volume | Approved document classification, malware-safe intake, rebuildable index, access-filtered full-text search, source citations, reindex/retention health | AI/OCR remains non-authoritative and separately authorized | Index/revocation/retention/no-content-log tests, performance SLO results, reindex and rollback drill |
| R6 — Production proof | Demonstrate reliable operation, not just feature completeness | Monitoring, support procedures, backup/restore, deployment/rollback rehearsals, and release package | No live activation based on a flag alone | Independent Product, Engineering, and Security PR approvals; green CI on unchanged SHA; deployment and operator evidence |

## 4. Detailed acceptance criteria

### R0 — Foundation

- Resolve the sticky-column test drift and define a stable test assertion that
  checks the intended selected/title column relationship.
- Replace repository-local inline styling with approved design-system
  primitives and shared token-backed styles; introduce no new inline styles or
  one-off visual components.
- Confirm table sorting, selected rows, row menus, column visibility, filter
  controls, loading, empty, error, and no-access states using keyboard and
  screen-reader semantics.
- Keep `Stage` (workflow position) and `Status` (record state) distinct in
  labels, sorting, filters, help text, and exported fields.

### R1 — Governed import

- A workspace owner or authorized administrator downloads a documented CSV
  template and receives only same-workspace member choices.
- A dry-run validates encoding, schema, dates, lifecycle pairs, ownership,
  duplicates, and mapped values without writing records.
- Commit is explicit, create-only, idempotent against the declared duplicate
  policy, and emits content-minimized audit/provenance events under one
  correlation ID.
- Each failure is row-numbered and actionable; no error, duplicate hint, or
  selection leaks another workspace's data.
- Reversal is compensating and limited to unchanged records created by the
  import. It never silently deletes or overwrites independently changed data.

### R2 — Access-safe discovery

- Object policy is evaluated before every repository projection—not only when
  opening a record.
- Restricted records cannot affect result order, totals, facets, saved-view
  results, exports, autocomplete, error messages, or predictable URLs.
- A missing, stale, or failed policy/index path fails closed with a useful,
  non-leaking recovery message.
- Search health is content-free and observable; query text and document content
  are not put in operational logs.

### R3 — Relationships and quality

- Entity and Contract Relationship ownership is resolved through a decision
  record before new storage or backfill work.
- Relationship types are canonical, auditable, cycle-safe, and reversible.
- Repository quality indicators distinguish missing, conflicting, unverified,
  stale, invalid, orphaned, and duplicate data without misrepresenting
  confidence.

### R4 — Operational dates

- The source, timezone, and confidence for renewal and notice dates are shown
  or explicitly marked as unknown.
- Every reminder and escalation has a policy, owner, recipient, schedule,
  delivery outcome, and audit event.
- Failed or ambiguous calculation never claims a notice was sent; it creates
  visible accountable work instead.

### R5 — Document search and performance

- Document discovery returns citations to the source document version and page
  or span where available.
- Derived text/index data has classification, encryption/retention behavior,
  current object-policy filtering, reindexing, deletion, and revocation paths.
- Define and prove tenant-volume and concurrency SLOs before release. The
  target volume and p95 list/filter/search/export latency must be agreed in
  the tranche PDR rather than assumed in this roadmap.

### R6 — Production proof

- Dashboards expose repository availability, policy/index health, import
  outcomes, queue failures, and key-date/reminder delivery failures without
  exposing contract content.
- Support has documented recovery, reindex, import reversal, access-denial,
  and data-correction procedures.
- Backup/restore and rollback are rehearsed in the target environment with
  retained operator evidence.

## 5. Mandatory decision and release gates

| Before | Required authority/evidence |
|---|---|
| R1 implementation | Normal low-risk planning/implementation review and green CI; any new persistent import-batch concept requires an ADR/PDR confirming canonical ownership and migration/reversal behavior |
| R2 access enforcement or new visibility behavior | Accepted and authorized object-level access decision, threat review, Security review, and no-leak test corpus |
| R3 entity or relationship schema/backfill | ADR/PDR for canonical ownership, relationship semantics, migration, and reversal |
| R4 automatic reminders or schedule activation | Product/Engineering/Security authorization, reversible default-off controls, named-environment operator record |
| R5 OCR, document text indexing, or AI | Data classification, retention, malware/file-safety, access, and non-authoritative AI authorization package |
| R6 production activation | Independent Product, Engineering, and Security GitHub approvals; green CI for the unchanged reviewed SHA; deployment/recovery evidence and release record |

Feature flags only control exposure; they never grant authority.

## 6. Work package template

Every repository PR or delivery package must include:

1. User problem, surface boundary, canonical terminology, and explicit
   non-goals.
2. Object ownership, permission path, audit events, data classification,
   migration, and rollback/abort behavior.
3. UI state coverage: loading, empty, error, success, and no-access; plus
   keyboard, focus, contrast, and responsive verification.
4. Unit, integration, end-to-end, tenant/object-isolation, and negative-path
   tests appropriate to the tranche.
5. Performance and operational evidence where the tranche changes data volume,
   indexing, scheduling, or exports.
6. GitHub review/CI/release evidence required by the applicable gate.

## 7. Finalization checklist

This roadmap may be marked **finalized as planning** when:

- [x] it preserves the accepted product spine and canonical object ownership;
- [x] it keeps Contracts, My Work, Command Center, and specialist workspaces
  within their approved responsibilities;
- [x] it preserves the current safe Phase 1 boundary;
- [x] it identifies authorization dependencies instead of treating them as
  implementation details;
- [x] every tranche has measurable acceptance evidence and a rollback/abort
  path; and
- [x] it is indexed in `docs/README.md` and reviewed through normal repository
  governance.

Actual **5/5 product maturity** is achieved only after all R0–R6 exit evidence
has been completed and the final production release gate has passed. This
planning document does not make that claim.
