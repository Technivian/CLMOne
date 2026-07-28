# Repository Essentials — Phase 1

**Status:** First-slice implementation **Completed** — CSV-assisted import is
implemented behind a committed-default-off flag. Activation remains
**Blocked / Unauthorized**; this document does not authorize activation.

**Implementation baseline:** `main` at
`0d62db10392fe066b43d6f349ac7c66c5ea87f1d`, after the planning baseline and
UI test recovery merged (28 July 2026). Platform Alignment and Pilot Hardening
remain closed. The PayrollMinds demonstration remains a synthetic,
design-partner demonstration only: no real PayrollMinds, client, employee, or
payroll data; no production-readiness claim.

## Purpose and guardrails

Phase 1 closes practical repository gaps that prevent an established contract
platform from being immediately useful, without weakening CLM One's governed
workflow, provenance, audit, or access model. It follows the product spine:
**ingest → record → operate → renew or terminate**.

This roadmap does not reopen completed PARs and does not amend an accepted
decision. In particular, PDR-0008 and Addendum 001 define object-level-read
policy scope only; they do not authorize a search, filter, count, telemetry,
AI, or permission implementation. Any capability that changes external access,
identity, permissions, visibility, automatic processing, or production state
requires its own authorization and release evidence.

Phase 1 must not:

- use real PayrollMinds or client data;
- add a second `Contract`, `Entity`, or `Property` model;
- weaken server-side object access or disclose restricted metadata in results,
  counts, errors, suggestions, or notifications;
- enable AI extraction, add production credentials, or bypass file safety
  checks; or
- deliver anonymous public sharing, OCR, e-signature, or SSO in the first
  slice.

## Verified capability matrix

| Capability | State | Baseline evidence and reusable components | Gap / gate |
|---|---|---|---|
| Bulk contract import and migration | **Ready (default-off implementation)** | `RepositoryCsvImportService` adds a private-workspace template, zero-mutation dry-run, deterministic row diagnostics, create-only duplicate detection, canonical type/counterparty/lifecycle/key-date mapping, signed commit/rollback tokens, immutable provenance/correlation evidence, append-only audit, and compensating archival. Synthetic fixture/reset and tenant-isolation coverage are included. | Activation is **Blocked / Unauthorized**. The flag remains committed off; no operator window, client data, document upload, external access, automatic processing, or production-readiness claim is authorized. |
| Repository metadata, filtering, and dependable search | **Unsafe** | Repository list, `ContractSearchAPIService`, search presets, contract type catalogue, contract key dates, and tenant scoping exist. | Search/list/facet paths are tenant-scoped but not consistently protected by the proposed object-level evaluator. PDR-0008 bars a visibility-changing implementation until separately authorized. Document text search is absent. |
| Renewal, notice, and deadline reminders | **Partial** | `Contract` has renewal/end/notice dates; `Deadline`, obligations workspace, renewal playbook, scheduled jobs, and notification service exist. | Playbook creates unassigned deadline rows; it does not calculate a canonical notice date from contract terms, prove delivery/escalation, or provide reminder policy/version/evidence. Automated delivery requires separate authorization. |
| One e-signature integration | **Partial** | `SignatureRequest`, document-version binding, provider abstraction, simulated null provider, DocuSign/Documenso adapters, webhook reconciliation, and audit helpers exist. | Live provider credentials, OAuth/token rotation, callback/webhook production assurance, signature authority, and provider operational controls are not authorized. PayrollMinds scope explicitly excludes live e-sign. |
| Secure external document sharing | **Unsafe** | Contract-scoped counterparty collaboration supports explicit document flags, expiry, revocation, audit events, revisions, and private-by-default documents. | The portal uses a bearer capability URL plus email confirmation rather than authenticated external identity, and has no accepted external-sharing authorization package. It must not be extended as public/anonymous sharing. |
| Entity and contract-family profiles | **Partial / Blocked** | `Counterparty`, `Contract.parent_contract`, linked contracts, contract types, and tenant-scoped counterparty views exist. | Contract currently stores counterparty text while `Counterparty` is a separate, unlinked legacy shape. Canonical `Entity` ownership, aliases/identifiers, relationship semantics, and migration/backfill rules need a separately accepted decision before schema work. |
| Microsoft SSO | **Partial / Blocked** | Password auth, optional OIDC settings, SAML endpoints, SAML assertion checks, SCIM/group support, MFA handling, and identity audit are present and default off. | No Microsoft Entra-specific configuration/onboarding, provider validation, tenant/issuer policy, or authorization to activate identity integration. Identity changes require the stronger release gate. |
| Polished workspace onboarding | **Partial** | `OnboardingProgress`, `OnboardingService`, onboarding APIs, starter content, registration provisioning, and dashboard checklist components exist. | Steps are generic, mutable via a broad authenticated endpoint, and do not lead a user through import readiness, data boundaries, success evidence, or role-aware recovery. |

## Competitor-gap assessment

Established CLM repositories are useful on day one because teams can migrate
their inventory, find it by business metadata and document content, and act
before renewal or notice dates. CLM One already has stronger lifecycle,
provenance, document-version, workflow, and audit foundations than a simple
repository. The immediate gap is the safe operational bridge from a customer's
spreadsheet to a private, trustworthy repository. The first slice therefore
prioritizes controlled CSV migration and onboarding over broad integrations or
AI-assisted extraction.

## Target behaviour by capability

### 1. Bulk import and migration

- **PayrollMinds problem:** a legal-operations user cannot safely bring a
  spreadsheet inventory into the pilot, inspect row errors, or demonstrate a
  governed repository without manual re-entry.
- **Pilot-ready minimum:** a privileged workspace user downloads a documented
  CSV template, uploads synthetic data, receives a dry-run with row-numbered
  actionable errors and duplicate findings, explicitly confirms a create-only
  import, and can download/see its immutable batch evidence. Map contract
  title/type, counterparty, owner only when an active same-workspace member is
  selected, effective/start, expiry/end, renewal, notice-period, and explicit
  notice date. No document upload is in this slice; every document remains
  private by default.
- **Production-ready:** resumable, idempotent migrations with a governed field
  map, trusted-source controls, batch retention, approved entity resolution,
  document intake/quarantine, reconciliation reports, and a compensating
  rollback workflow.
- **Ownership and access:** create only the canonical `Contract` Record using
  `Contract`, `ContractType`, existing `Counterparty` pending entity ownership
  resolution, and `Deadline` only in a later renewal slice. A workspace owner
  or administrator initiates/commits; an active same-workspace member may only
  see a batch they are authorized to see. No cross-workspace lookup, duplicate
  hint, row error, owner option, or counterparty suggestion may leak data.
- **Audit, failure, rollback:** append batch-created, dry-run, row-rejected,
  duplicate-detected, row-created, commit-completed, and compensating-reversal
  events with correlation IDs and content-minimized summaries. Dry-runs never
  write. Commit is atomic per row with no overwrite; rollback creates a
  compensating archival/reversal record for rows created by that batch and
  never deletes or mutates an independently changed record.
- **Dependencies and acceptance:** reuse lifecycle/provenance services and
  tenant/access checks; introduce no external integration. Test template
  schema, invalid CSV/encoding/dates/lifecycle pairs, every mapping, duplicate
  types, dry-run non-mutation, partial row failures, repeat submission,
  tenant/object isolation, audit append-only behavior, private document
  default, rollback eligibility, and synthetic fixture reset. Migration impact
  is additive only; no historic backfill or destructive migration.

### 2. Repository metadata, filtering, and search

- **PayrollMinds problem:** users need to locate a migrated agreement by
  counterparty, type, owner, lifecycle, and key dates without scanning pages.
- **Pilot-ready minimum:** eligible-only metadata filters and deterministic
  repository search over title, mapped counterparty, canonical type, lifecycle,
  owner, and key dates; clear empty/error states and no document-text search.
- **Production-ready:** policy-safe full-text document search, saved views,
  authorized facets, relationship/date/obligation filters, reindexing and
  content-free health diagnostics.
- **Ownership and access:** Search and Repository Intelligence owns projections;
  `Contract`, document versions, canonical properties, and obligations remain
  sources of truth. Evaluate workspace and accepted object policy before
  ranking, count, facet, pagination, and serialization.
- **Audit, failure, rollback:** record content-free search-policy outcomes and
  index health only. A missing/stale policy evaluator returns generic
  unavailable/empty results; rollback never restores an unfiltered index.
- **Dependencies and acceptance:** blocked on accepted/authorized PDR-0008
  implementation. Require denied-object, facet/count, tenant, Ethical-Wall,
  stale-index, no-leak, accessibility, and rollback tests. Migration impact is
  additive/index-only and rebuildable.

### 3. Renewal, notice, and deadline reminders

- **PayrollMinds problem:** renewal/notice commitments can be missed when a
  contract is imported or becomes active.
- **Pilot-ready minimum:** show imported key dates in Contracts and create
  accountable, auditable in-app deadline work manually or via an explicitly
  authorized default-off scheduler; no claim that notice was sent.
- **Production-ready:** validated term/notice calculation, reminder policy,
  assignment/escalation, delivery preferences, delivery evidence, recurrence,
  and My Work/notification integration.
- **Ownership and access:** `Contract` owns terms; Obligations and Renewals
  owns `Deadline`/future canonical Obligation and Reminder schedules. Only
  authorized users can view or act on source contracts and their reminders.
- **Audit, failure, rollback:** audit calculation source, schedule, send,
  acknowledgement, failure, retry, escalation, and cancellation. Fail closed
  on ambiguous terms; stop schedules and preserve evidence on rollback.
- **Dependencies and acceptance:** depends on dependable import key dates,
  ownership and notification policy. Test date boundaries/time zones,
  idempotency, assignment, access revocation, delivery failure, and no false
  “sent” state. No destructive migration.

### 4. Entity and contract-family profiles

- **PayrollMinds problem:** related MSAs, SOWs, amendments, and counterparties
  are hard to understand as one commercial relationship.
- **Pilot-ready minimum:** a read-only relationship/profile view of imported
  same-workspace records, using approved existing ownership and explicit
  unknown/unlinked states.
- **Production-ready:** canonical entity profiles with aliases, identifiers,
  contacts, parent/subsidiary relationships, approved matching, and governed
  contract-family relationship types.
- **Ownership and access:** the accepted domain assigns this to Entities and
  Relationships. Reuse `Counterparty` only after a decision resolves its
  relationship to canonical `Entity`; reuse `Contract.parent_contract` only
  for its current master/governing meaning. Do not add a parallel Entity or
  Contract-family model.
- **Audit, failure, rollback:** audit profile/relationship proposals, merges,
  approvals, and reversals. Ambiguous matches remain unlinked; rollback
  removes only a governed newly-created relationship.
- **Dependencies and acceptance:** blocked on canonical ownership/migration
  decision. Require cross-tenant, duplicate-resolution, relationship-cycle,
  restricted-metadata, provenance, and reversal tests. Any backfill is
  separately approved, reversible, and verified.

### 5. Secure external sharing

- **PayrollMinds problem:** a counterparty needs a bounded way to receive or
  return selected contract documents without access to the internal workspace.
- **Pilot-ready minimum:** none in Phase 1 without a separate external-access
  authorization. Existing collaboration remains out of the first slice.
- **Production-ready:** authenticated, recipient-bound, time-limited,
  revocable access to explicit immutable document versions with download/view
  audit, malware/type checks, watermark/retention policy where required, and
  non-leaking failures.
- **Ownership and access:** Documents owns document/version access;
  Access-Control evaluates recipient and object policy; Integrations/Identity
  owns external identity when used. Private is the default; no public anonymous
  links.
- **Audit, failure, rollback:** invitation, verification, grant, view,
  download, upload, revocation, expiry, and denial events are append-only.
  Policy failure denies access. Revoke immediately; preserve evidence.
- **Dependencies and acceptance:** external access, permissions, malware
  scanning and identity assurance need separate authorization and independent
  Product/Engineering/Security reviews. Test token/session theft, expiry,
  revocation, cross-tenant/document, privilege, upload safety, and metadata
  leakage. Migration only after an approved retention plan.

### 6. One e-signature integration

- **PayrollMinds problem:** signing should be traceable from the approved
  document version through execution evidence.
- **Pilot-ready minimum:** keep the null/simulated provider only; do not send
  external signature requests in this programme slice.
- **Production-ready:** one approved provider with scoped secrets, OAuth/JWT
  rotation, signed/replay-protected webhooks, idempotent send/retry/DLQ,
  provider outage handling, document-version binding, execution certificate,
  signer ordering, and wet-sign fallback.
- **Ownership and access:** Signature owns `SignatureRequest`/future canonical
  Signature Packet and Evidence; Documents owns immutable versions; Integrations
  owns connection/secrets. Sending/cancelling is server-authorized and tenant
  scoped.
- **Audit, failure, rollback:** audit draft/send/provider receipt/webhook,
  transition/retry/cancel/evidence verification; never mark signed from an
  unverified callback. Disable provider dispatch and preserve pending packets
  on rollback.
- **Dependencies and acceptance:** separate live-integration authority plus
  security review. Require webhook signature/replay/idempotency, cross-tenant,
  access, outage, duplicate event, evidence, and provider sandbox tests. No
  credentials in code or migrations.

### 7. Microsoft SSO

- **PayrollMinds problem:** pilot users need a familiar, managed sign-in path
  without weakening membership or MFA assurance.
- **Pilot-ready minimum:** document an Entra configuration checklist only;
  no tenant is connected or SSO flag enabled.
- **Production-ready:** an Entra OIDC or SAML connection with issuer/audience,
  redirect URI, signing-key rotation, verified domain/tenant policy, JIT/SCIM
  lifecycle rules, MFA assurance mapping, logout/session revocation, and
  identity audit.
- **Ownership and access:** Identity and Workspace owns authentication and
  membership; SSO proves identity but never grants a workspace role or bypasses
  active membership/object policy.
- **Audit, failure, rollback:** audit configuration, login, provision,
  deprovision, assurance, failure, and logout without leaking assertions.
  Disable the connection, invalidate sessions as applicable, retain password
  recovery/break-glass only under approved policy.
- **Dependencies and acceptance:** identity integration and privilege change
  require separate authorization and independent review. Test issuer/tenant
  confusion, signature failure, expired assertion, domain mismatch, inactive
  membership, MFA, logout, provisioning, and audit. No production credentials
  or data migration in this phase.

### 8. OCR enrichment and advanced search

- **PayrollMinds problem:** scanned and native contract text should be
  discoverable and reviewable without claiming AI extraction is authoritative.
- **Pilot-ready minimum:** none. Existing native-text extraction remains
  observational/manual-review only and must not be enabled or surfaced as a
  Phase 1 promise.
- **Production-ready:** malware/type-checked document intake, local or approved
  OCR, source/page provenance, confidence, human verification queue, encrypted
  text/index retention, current object-policy checks, and failure-safe reindex.
- **Ownership and access:** Documents owns versions; Search and Repository
  Intelligence owns index/OCR queue; AI Orchestration is only involved under a
  separately approved non-authoritative policy.
- **Audit, failure, rollback:** audit queue/extract/verify/reject/index/fail
  with content-free operational evidence. Failed OCR stays pending/manual;
  disable the index and remove derived data under retention policy rather than
  exposing stale content.
- **Dependencies and acceptance:** blocked on PDR-0008 enforcement, document
  classification/retention, malware handling, and a separately authorized OCR
  design. Test scanned/native/corrupt files, isolation, revocation/index lag,
  no content logging, verification, and purge/rebuild. Derived-data migrations
  must be rebuildable and reversible.

## Delivery sequence and living roadmap

| Order | Capability / slice | Owner | Current state | Dependencies | Acceptance evidence | Risk | Status |
|---:|---|---|---|---|---|---|---|
| 1 | CSV-assisted private-workspace import | Product + Engineering + Security | **Completed** | Existing lifecycle/provenance and scoped import authorization satisfied for default-off code only | Synthetic fixture, dry-run, duplicate, isolation, audit, compensation, exact-SHA CI and rollback evidence | Medium | **Implementation Completed; activation Blocked / Unauthorized; flag off** |
| 2 | Repository metadata, filters, and policy-safe search | Product + Engineering + Security | Blocked | Accepted/authorized PDR-0008 enforcement | Object-policy/no-leak/facet tests and rollback drill | High | Deferred |
| 3 | Renewal/notice/deadline reminders | Product + Engineering | Partial | Import dates, ownership, notification policy | Time-boundary, idempotency, delivery/audit tests | Medium | Deferred |
| 4 | Entity and contract-family profiles | Product + Engineering + Security | Blocked | Canonical ownership/migration decision | Relationship, isolation, reversal tests | High | Deferred |
| 5 | Secure external sharing | Product + Engineering + Security | Unsafe | External-access authorization, identity, file safety | Recipient/revocation/no-leak tests | High | Deferred |
| 6 | One e-signature integration | Product + Engineering + Security | Partial | Provider approval and integration security | Webhook/retry/evidence sandbox tests | High | Deferred |
| 7 | Microsoft SSO | Product + Engineering + Security | Blocked | Identity authorization and Entra tenant policy | Federation/MFA/provisioning tests | High | Deferred |
| 8 | OCR enrichment and advanced search | Product + Engineering + Security | Blocked | Search enforcement, OCR/classification/retention design | OCR/index/verification/no-leak tests | High | Deferred |

## First authorized implementation PR: proposed scope

The first implementation PR may begin only after this planning PR merges and
normal low-risk review/green CI is recorded. It is a create-only,
default-off CSV-assisted import into one private workspace. It includes the
template, validation preview, duplicate policy, explicit confirmation, mapped
contract/counterparty/key-date data, correlation/provenance/audit evidence,
compensating rollback, synthetic fixtures, and focused tests. It excludes
documents, sharing, e-signature, SSO, OCR, AI, background automatic reminders,
external credentials, real data, and any permission-model change.

Likely affected files are `contracts/services/inbound_import.py`,
`contracts/services/contract_import_lifecycle.py`, a new import application
service and additive migration(s), the import API or a new tenant-scoped view,
`contracts/urls.py`, import templates/forms, `contracts/models.py` only if an
approved additive batch/evidence record is justified, synthetic demo fixtures,
and focused tests. It reuses `Contract`, `ContractType`, `Counterparty`,
`AuditLog`, `persist_contract_with_imported_lifecycle`, contract provenance,
`TenantScoped*` mixins, `get_user_organization`, and
`can_access_contract_action`/organization-management checks; it does not add
another contract, entity, or property model.

## First-slice implementation and operations

The first slice implements a workspace-owner/administrator HTML workflow at a
feature-gated repository route. `REPOSITORY_CSV_IMPORT_ENABLED` is committed
`false`. When enabled in an authorized non-production environment, the
workflow provides:

- a UTF-8 CSV template with contract title, canonical contract type, exact
  same-workspace active counterparty, canonical lifecycle position, and key
  dates;
- a read-only dry-run with deterministic row/field/code errors and a signed,
  time-limited token bound to the exact CSV bytes, workspace, actor, and opaque
  correlation ID;
- an explicit commit that revalidates under a workspace lock, creates canonical
  `Contract` rows only, and refuses in-file or same-workspace duplicates;
- immutable `IMPORT_CSV` provenance and canonical append-only audit events for
  batch start/completion and each created row; and
- a signed compensating rollback that remains callable after the exposure flag
  is turned off, archives every unchanged contract from the batch, and refuses
  the whole rollback if any imported record changed.

The slice creates no document, external share, signature request, identity
connection, reminder, AI/OCR output, credential, new permission, or production
activation. Imported records are workspace-scoped and have no document or
external-access object. Counterparties are never auto-created or resolved
outside the active workspace.

Abort before commit by leaving the preview page or switching the feature flag
off. After commit, preserve the returned rollback token and correlation ID,
switch the feature flag off, and apply compensating rollback while the imported
records remain unchanged. Rollback preserves the records, provenance, and audit
chain by moving them to the canonical `ARCHIVED` /
`OBLIGATION_TRACKING` position; it never deletes them.

## Release-governance gap

GitHub currently permits a pull request to merge while checks are still
running because required-check enforcement is not configured. This
implementation does not attempt a repository-setting change. Until that
control is separately supported and authorized, release evidence must include
a manual verification that every required check is green for the unchanged
head SHA, followed by the repository owner's exact-SHA attestation in GitHub.
The PR must not merge based on mergeability status alone. Any source or
metadata scope change after attestation invalidates the attestation and
requires another full CI run and exact-SHA attestation.

## Implementation PR prompt

> Implement only the approved first slice from `docs/roadmap/REPOSITORY_ESSENTIALS_PHASE_1.md`: a default-off, create-only CSV-assisted bulk contract import into a private workspace. Reuse `Contract`, `ContractType`, `Counterparty`, lifecycle/provenance services, tenant checks, and append-only audit. Provide a downloadable template, synthetic-only dry-run, row-level errors, duplicate detection with no silent overwrite, title/type/counterparty/owner/key-date mapping, explicit commit, immutable correlation evidence, and compensating rollback. Keep documents private and out of scope; do not implement sharing, e-sign, SSO, OCR, AI, external credentials, automatic reminders, or permission-model changes. Add migration/rollback notes and focused tests for isolation, authorization, dry-run non-mutation, duplicates, lifecycle/provenance, audit, rollback, and fixture reset.
