# ADR-0013: Approval Requirement and Approval Decision split

- Status: **Pending Ratification**
- Date: 2026-07-22
- Effective date: **Pending** — requires named approver evidence (see meeting record §10)
- Deciders: Pending — governance package submitted for ratification
- Related: PAR-APR-001 (foundation delivered; closure pending ratification), PAR-APR-002 (Planned), PAR-DOC-001, CANONICAL_DOMAIN_MODEL §2.23–2.24, PDR-0001
- Meeting record: [`0013-governance-acceptance-meeting-record-2026-07-22.md`](0013-governance-acceptance-meeting-record-2026-07-22.md)
- Ratification validation: [`../../../audits/2026-07-22-adr-0013-ratification-validation.md`](../../../audits/2026-07-22-adr-0013-ratification-validation.md)

## Approval metadata

| Field | Value |
|---|---|
| **Submitted for ratification** | 2026-07-22 |
| **Ratification status** | **Pending** — insufficient approver evidence (see validation report) |
| **Required before Accepted** | Named approvers or delegated org identifiers; authority basis; written consent or attendance record; vote timestamp |
| **Proposed acceptance scope** | Canonical foundation (additive schema, governed write path, vocabulary mapping, audit events). **Would not authorize** PAR-APR-002 implementation or legacy cutover. |
| **Evidence** | `docs/audits/evidence/2026-07-22-par-apr-001/` |

## Context

Accepted domain documentation requires:

- **Approval Requirement** — why approval is needed, who must approve, authority basis, conditions, sequence.
- **Approval Decision** — immutable outcome tied to specific contract state and Document Version.

CLM One previously collapsed both into mutable `ApprovalRequest` rows.

PAR-DOC-001 delivered `DocumentVersion` binding for signatures; approvals lacked version binding (gap G-DOM / traceability row).

## Alternatives considered

| Alternative | Why not adopted |
|---|---|
| Retain collapsed `ApprovalRequest` only | Violates CANONICAL_DOMAIN_MODEL §2.23–2.24; no immutable decision bound to document version |
| Status-only split on `ApprovalRequest` | Does not provide immutable Decision entity or governed append-only outcomes |
| Big-bang legacy removal | Too risky; dual-write additive path preferred with PAR-APR-002 cutover |

## Decision (proposed — pending ratification)

### 1. Canonical entities (implemented additively on `c9ae7305`)

| Entity | Role |
|---|---|
| `ApprovalRequirement` | Open need for approval; binds contract + document version at open |
| `ApprovalDecision` | Immutable outcome (`APPROVED`, `REJECTED`, `RETURNED`, `REVOKED`, `ABSTAINED`) |

`ApprovalRequest` remains as **legacy compatibility mirror** linked via `ApprovalRequirement.legacy_request` OneToOne until PAR-APR-002 cutover completes.

### 2. Governed write path

- **Create requirement:** `create_approval_requirement()` (+ `ApprovalRequest.save` idempotent fallback)
- **Record decision:** `record_approval_decision()` via `ApprovalWorkflowService._decide`
- **Invalidate on material doc change:** `invalidate_open_requirements_for_contract()` from document supersession path

### 3. Binding rules

- Requirement captures `contract_status_at_open`, `contract_lifecycle_stage_at_open`, `document_version_id` (or `document_version_missing=True`)
- Decision captures state + version at decision time
- Material FINAL/EXECUTED document supersession invalidates open requirements (`REVOKED` decision + legacy `CHANGES_REQUESTED`)

### 4. Vocabulary mapping

| Legacy `ApprovalRequest.status` | Canonical decision outcome | Requirement status |
|---|---|---|
| `PENDING` / `ESCALATED` | (none yet) | `OPEN` |
| `APPROVED` | `APPROVED` | `SATISFIED` |
| `REJECTED` | `REJECTED` | `REJECTED` |
| `CHANGES_REQUESTED` | `RETURNED` | `RETURNED` |

`CHANGES_REQUESTED` char value retained on legacy row; canonical uses `RETURNED`.

### 5. Audit events

| Event | When |
|---|---|
| `approval.requirement.created` | New requirement |
| `approval.requirement.invalidated` | Material state/doc change |
| `approval.decision.recorded` | Immutable decision appended |
| Legacy `approval.approved` / `approval.rejected` / `approval.returned` | Retained on `ApprovalRequest` path |

### 6. Explicit non-goals / residuals (PAR-APR-002)

- `DPAReviewPack.approval_status` — separate model; not merged in foundation slice
- `ApprovalRoute` template rows — configuration only; not runtime requirements
- `ABSTAIN` / explicit `REVOKE` UI actions — outcome exists; UI wiring deferred
- Removal of `ApprovalRequest` — deferred to **PAR-APR-002** (Planned)

## Mandated by accepted documentation (no ADR needed)

- Requirement vs Decision separation (CANONICAL_DOMAIN_MODEL §2.23–2.24)
- Decision references evaluated state/document version (invariant §277)
- Server-side authorization and tenant isolation (SECURITY_PRIVACY_ACCESS_AND_AUDIT)
- Finance threshold single entry (PDR-0001 — unchanged)

## Consequences (upon ratification)

- PAR-APR-001 would close as foundation delivered; cutover residuals transfer to PAR-APR-002.
- PAR-APR-002 remains **Planned** — blocked pending owner, cutover plan, and separate implementation authorization.
- ADR acceptance would authorize **planning** for PAR-APR-002 only; not implementation.
- Programme-level tenant isolation remains **unproven** until PAR-SEC-003 resolves `ContractIsolationTest.test_list_shows_only_own_org`.
- ADR-0010 remains **Proposed** and is not amended by this decision.

## Approval

**Pending Ratification** as of 2026-07-22. Prior draft meeting record did not include named approvers or written consent evidence. Do not treat as Accepted until ratification validation passes.
