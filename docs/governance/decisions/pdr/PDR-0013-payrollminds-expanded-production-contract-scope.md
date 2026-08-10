# PDR-0013: PayrollMinds Expanded Production Contract Scope

**Status:** Proposed — Product Owner business-scope direction recorded; GitHub decision evidence and technical activation authorization remain pending
**Date:** 2026-08-09
**Owner:** To be designated by the Product Owner through the authorizing GitHub record
**Affected Charter sections:** §16 Repository evidence and release control
**Related ADRs:** ADR-0016; ADR-0019
**Related PDRs:** PDR-0008 (Proposed), PDR-0011 (Proposed), PDR-0012 (Proposed)
**Related package:** [`EXPANDED_PRODUCTION_SCOPE_CHANGE.md`](../../../pilots/payrollminds/EXPANDED_PRODUCTION_SCOPE_CHANGE.md)
**Remote baseline inspected:** `origin/main` at `2b1fe6da1431ed4d63b0afe226d404e4af4aced7`

## Problem

PayrollMinds intends to use CLM One as an operational CLM platform rather than
remain within a three-type controlled pilot. The repository contains two
conflicting historical statements of that three-type limit:

- the 2026-07-20 controlled-pilot release and operations records state MSA,
  NDA and DPA; and
- later proposed PayrollMinds scope records state MSA, Order Confirmation and
  Mutual NDA.

No accepted decision record was found that amends the first list to the
second. Application code, seed data, browser fixtures, UAT evidence and a
live-environment observation are implemented capability/evidence, not
contract-type authorization. Leaving the conflict unresolved makes a route or
flag change appear to decide business scope, contrary to the active Charter.

## Decision

### Product Owner direction recorded on 2026-08-09

The Product Owner has directed that the proposed expanded business scope and
batched technical activation approach be used, with **Order Confirmation** and
**Purchase Order** as the first proposed Batch 2 technical cohort. This is a
business-scope direction only. In accordance with the active Governance
Charter and this record's existing authority boundary, it is not treated as an
Accepted PDR or as authorization to change permissions, expose a route, deploy,
or activate either type until the applicable GitHub review, unchanged-SHA CI,
and release/operator evidence are present.

### Business scope authorization proposed

For **future** PayrollMinds activation, this PDR proposes a broader business
destination scope covering the 21 existing governed `Contract.ContractType`
classifications listed in §6. It expressly supersedes the prior *three-type
contract-type restriction* only if this PDR is accepted through the applicable
GitHub review/evidence process.

This PDR does not retrospectively alter the meaning, status, source SHA or
evidence of any historic document. It does not validate historical use of a
type that was not authorized at that time.

### Technical activation authorization remains separate

Business-scope approval does **not** expose a type, enable an intake path, or
authorize production use. A type becomes production-active only after its
individual technical activation gate passes on the immutable reviewed SHA and
the applicable release/operator evidence exists.

No runtime configuration, middleware allowlist, feature flag, data, role,
permission, lifecycle state, integration, signature, AI setting or deployment
is changed by this decision record.

### Access-policy dependency

The first proposed Batch 2 cohort follows this required sequence:

> PDR-0013 business-scope direction → PDR-0008 access-policy approval →
> separately authorized access implementation → per-type technical activation
> gate.

Order Confirmation and Purchase Order remain **BUSINESS SCOPE APPROVED /
TECHNICAL ACTIVATION BLOCKED** until both the PDR-0008 implementation gate and
their independent evidence gates are green.

### Historical four-type resolution

| Type | Historical authorization finding | Proposed future business status | Technical status |
| --- | --- | --- | --- |
| MSA | Included in the 2026-07-20 approved controlled-pilot operational scope and in the later proposed scope. | BUSINESS APPROVED — TECHNICAL GATE PENDING | Existing dedicated path is capability evidence, not expanded-production readiness. |
| NDA | Included in the 2026-07-20 approved controlled-pilot operational scope and in the later proposed scope. | BUSINESS APPROVED — TECHNICAL GATE PENDING | Existing dedicated path is capability evidence, not expanded-production readiness. |
| DPA | Included in the 2026-07-20 approved controlled-pilot operational scope. It was **not** included in the later proposed PayrollMinds scope materials. | BUSINESS APPROVED — TECHNICAL GATE PENDING | Dedicated privacy path exists; per-type export/browser/security evidence remains required. |
| Order Confirmation | **No formal authorization located.** It appears in PDR-0011, `PILOT_SCOPE.md` and `PILOT_CHARTER.md`, all Proposed, and in generic implementation/configuration. | BUSINESS APPROVED — TECHNICAL GATE PENDING, only if this PDR is accepted | Class B; no production exposure until its individual gate passes. |

The historical operational pilot restriction is therefore recorded as
**MSA/NDA/DPA**. The MSA/Order Confirmation/NDA list is a later proposal, not
an accepted amendment. This PDR is the proposed, explicit future replacement;
it does not claim that Order Confirmation was previously approved.

## Authority-chain reconciliation

### Contract-type statements and their evidentiary weight

| Source | Date/version | Authority type | Contract types stated | Supersedes | Superseded by |
| --- | --- | --- | --- | --- | --- |
| `docs/governance/GOVERNANCE_CHARTER.md` | v2.4, 2026-07-25 | Active governing charter | No PayrollMinds list; requires GitHub review/evidence and rejects flag-as-authority | N/A | Not superseded |
| `docs/pilot/CONTROLLED_PILOT_LAUNCH_READINESS.md` | 2026-07-20 | Historical controlled-pilot operational/release record | MSA, NDA, DPA builders; requester may create MSA/NDA/DPA | No predecessor type record located | Proposed future supersession by this PDR, if accepted |
| `docs/pilot/CONTROLLED_PILOT_OPERATIONS.md` | Undated historical operations pack; cites 2026-07-20 verification gate | Historical operational scope/runbook | MSA, NDA, DPA | No predecessor type record located | Proposed future supersession by this PDR, if accepted |
| 2026-07-20 audit/verification reports and their browser evidence | 2026-07-20 | Verification evidence, not a scope decision | MSA, NDA, DPA governed paths | Nothing | Not a decision; remains historical evidence |
| `PDR-0011-payrollminds-controlled-pilot-scope-and-governance.md` | Proposed, 2026-08-02 | Proposed PDR | MSA, Order Confirmation, Mutual NDA | No supersession stated | Proposed future supersession by this PDR, if accepted |
| `docs/pilots/payrollminds/PILOT_SCOPE.md` | Proposed, undated | Proposed scope record subordinate to accepted governance | MSA, Order Confirmation, Mutual NDA | Nothing | Proposed future supersession by this PDR, if accepted |
| `docs/pilots/payrollminds/PILOT_CHARTER.md` | Proposed, undated | Proposed charter; expressly non-authorizing | MSA, Order Confirmation, Mutual NDA | Nothing | Proposed future supersession by this PDR, if accepted |
| `PDR-0012-payrollminds-ai-metadata-suggestion-gate.md` | Proposed, 2026-08-02 | Proposed AI-policy PDR | No type list | Nothing | N/A |
| `PILOT_PRODUCT_PATH_IMPLEMENTATION.md` | Proposed operational record; evidence update 2026-08-02 | Implementation evidence, expressly non-authorizing | No type list; generic clean release validates any enum value | Nothing | N/A |
| `contracts/middleware.py` (`ControlledPilotScopeMiddleware`) and `tests/test_controlled_pilot_scope.py` | Inspected remote-main implementation/test | Runtime exposure control and test evidence, not approval authority | Allows MSA/NDA/DPA builder routes; blocks generic create in pilot mode | Nothing | N/A |
| `PAYROLLMINDS_EXECUTABLE_UAT_MATRIX.md`, evidence and `release-baseline/executable-uat-results.json` | UAT evidence; source SHA `c5f83238` | Test/evidence only | Generic upload/release and an NDA workflow scenario; no approved list | Nothing | N/A |
| `PRODUCTION_TARGET_COMMISSIONING.md` and `release-baseline/production-target-evidence.json` | 2026-08-08 evidence | Production-environment observation/evidence, not contract-type authorization | No type list; reconciles dates/reminders only | Nothing | N/A |
| `docs/pilot/PAYROLLMINDS_DEMO_*` records and demo seed/browser fixtures | 2026-07-25–27 demo material | Synthetic demonstration evidence only | NDA, MSA, SOW and DPA appear in a fictional demo | Nothing | N/A |

### Actual decision chain

1. **Original restriction located:** the 2026-07-20 Controlled Pilot Launch
   Readiness record and the accompanying Operations Pack. They call the
   single-organization pilot approved/locked and explicitly allow MSA, NDA and
   DPA; this is the exact source of the MSA/NDA/DPA statement.
2. **Implemented capability:** dedicated MSA/NDA/DPA builders and their test
   suites were already present. These corroborate what was exercised, but do
   not make a governance decision.
3. **Later conflicting proposal:** PDR-0011 and the proposed pilot
   scope/charter (all dated or introduced around 2026-08-02) substitute Order
   Confirmation for DPA. Each says Proposed or expressly lacks activation
   evidence. None names the 2026-07-20 record as superseded.
4. **No formal amendment located:** no accepted PDR, ADR, Charter amendment,
   submitted GitHub approval record or release record was found that formally
   approved Order Confirmation, removed DPA, or superseded the 2026-07-20
   type list.
5. **This PDR:** if accepted, becomes the one explicit source for future
   PayrollMinds business contract-type scope. Per-type technical activation
   remains a subsequent gate.

### Historical divergence and exposure assessment

The repository records an unexplained documentation divergence: later
proposed scope documents selected Order Confirmation while older operational
records and the dedicated builders retained DPA. The inspected evidence does
not record why that substitution was made. It would be improper to infer a
business authorization from implementation, test fixtures, demo seed data or
a proposed PDR.

No evidence was located that the type-list discrepancy itself formally
authorized or activated Order Confirmation, or that it caused a known
Order-Confirmation production intake. There is, however, a separate recorded
production-environment finding: before 2026-08-08,
`CONTROLLED_PILOT_ENABLED` was unset on a live sponsor-only deployment, so
pilot route restrictions were not enforced for an unknown interval. The record
states no known real-user exposure beyond the sponsor; it is not evidence that
Order Confirmation was authorized or used. That operational incident remains
traceable in `PRODUCTION_TARGET_COMMISSIONING.md` and is not rewritten here.

## Users and roles affected

This PDR adds no role, permission, membership state, workflow responsibility
or authority. Existing `OWNER`, `ADMIN` and `MEMBER` roles continue to be
necessary but insufficient for protected reads. Product Owner, Engineering
and Security approval evidence must be independent for production activation
as required by the active Charter.

## Lifecycle impact

Every activated type must use the canonical Contract Record lifecycle:

> Contract → Document → immutable DocumentVersion → Workflow → Audit → controlled Export

An imported record may exist without a workflow only where the canonical
provenance and approved import design permit it; this is not a shortcut for a
Class C path. Published workflow versions remain immutable and live workflows
remain pinned. No new status, stage, type or lifecycle object is introduced.

## Permissions and access behavior

Private-by-default and server-side authorization remain unchanged. Each
activation must demonstrate owner/private access, cross-workspace denial,
revoked-access denial, search/count/facet non-disclosure, document access,
audit access and controlled export. A UI card, generic route, existing enum or
feature flag never substitutes for these checks.

## Terminology

Use **business scope authorization** for Product Owner authority to plan a
type as a destination capability. Use **technical activation authorization**
only for the evidence-backed approval to expose that individual type in a
named environment. `OTHER` remains the existing unmapped classification, not
a new “Custom agreement” object. Upload and import are origins/paths, not new
contract types.

## 21-type business-scope and activation inventory

Required evidence shorthand: **G** = all per-type technical gate evidence:
canonical lifecycle; Document/DocumentVersion/provenance; private access;
cross-workspace and search denial; workflow and required metadata; audit;
controlled export; browser path; rollback. **R** = Class C remediation before
G, including removal of separate/legacy unsafe behavior.

| Contract type | Class | Proposed business-scope status | Technical readiness | Required evidence | Activation batch |
| --- | --- | --- | --- | --- | --- |
| Non-Disclosure Agreement (NDA) | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready for expanded production | G | Batch 2 |
| Non-Compete / Non-Solicitation | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Master Service Agreement (MSA) | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready for expanded production | G | Batch 2 |
| Statement of Work (SOW) | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; scope/deliverable metadata and relationship decision | Batch 2 |
| Subcontractor SOW | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Consulting / Independent Contractor | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Employment Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; high-risk workflow evidence | Batch 2 |
| Lease Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; high-risk workflow evidence | Batch 2 |
| License Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; high-risk workflow evidence | Batch 2 |
| SaaS Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; security/data-processing workflow evidence | Batch 2 |
| Terms of Service / Terms & Conditions | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Vendor Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; procurement/high-risk workflow evidence | Batch 2 |
| Purchase Order | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Order Confirmation | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready; never formally authorized previously | G | Batch 2 |
| Partnership Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; high-risk workflow evidence | Batch 2 |
| Referral / Reseller / Channel Partner Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G | Batch 2 |
| Settlement Agreement | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; dispute/high-risk workflow evidence | Batch 2 |
| Amendment | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; parent relationship and approval-reset evidence | Batch 2 |
| Data Processing Agreement (DPA) | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready for expanded production | G; privacy workflow evidence | Batch 2 |
| Business Associate Agreement (BAA) | B | BUSINESS APPROVED — TECHNICAL GATE PENDING | Not ready | G; dedicated privacy configuration/workflow evidence | Batch 2 |
| Other / Custom (`OTHER`) | C | BUSINESS APPROVED — REMEDIATION REQUIRED | Deferred; explicit unmapped bucket is not a governed custom-type activation path | R + G | Batch 3 |

## Activation batches

The classification in the scope-change package found no additional Class A
type: shared storage alone does not prove an identical governed lifecycle.
Consequently, the batches are intentionally unequal.

| Batch | Types | Rule | Proposed action |
| --- | --- | --- | --- |
| Batch 1 — Class A | **None** | No type has complete evidence of the same proven canonical lifecycle. | No activation. Do not relabel Class B types merely to populate this batch. |
| Batch 2 — Class B | NDA, Non-Compete, MSA, SOW, Subcontractor SOW, Consulting, Employment, Lease, License, SaaS, Terms of Service, Vendor, Purchase Order, Order Confirmation, Partnership, Reseller, Settlement, Amendment, DPA, BAA | Configuration/workflow completion plus G for each individual type. | The first proposed technical cohort is **Order Confirmation and Purchase Order**, but neither is active until it independently passes G. Subsequent Batch 2 types require a new evidence decision; they are not auto-enabled. |
| Batch 3 — Class C | Other/Custom (`OTHER`) and the associated generic/legacy upload, quarantine-without-workflow-handoff, repository CSV, inbound and integration import paths | R before G. | Remediation required; no type or path is eligible for activation now. |

## Activation governance

For every newly activated type, the immutable candidate SHA must show:

1. an authorized typed intake/create path and invalid-type rejection;
2. canonical Contract/type-catalogue creation;
3. Document/immutable DocumentVersion and locked provenance where a document
   is used;
4. owner/private access, unrelated-member denial, cross-workspace denial and
   access-revocation denial;
5. permission-aware search, counts and facets with no restricted disclosure;
6. a published immutable workflow version, required metadata and invalid
   transition rejection;
7. append-only audit for creation, transition and export;
8. permission-controlled, audit-logged export;
9. an automated browser happy path with disposable-workspace cleanup; and
10. an operator-tested rollback that removes new exposure without deleting
    records, document versions or audit evidence.

Class C cannot be activated until remediation removes the alternate/legacy
behavior and the replacement passes the same gate. AI, inbound email,
signatures, external collaboration and integrations remain default-off unless
separately approved.

## Alternatives considered

### Treat the later proposed list as a completed amendment

Rejected. PDR-0011, `PILOT_SCOPE.md` and `PILOT_CHARTER.md` are explicitly
Proposed and do not identify a completed supersession.

### Treat code, tests or live observations as authority

Rejected. They demonstrate implementation or observation, not Product Owner
or release authority.

### Enable all existing enum values now

Rejected. It would expose untested Class B/C paths, weaken the controlled
release process and violate the governing principle that flags do not grant
authority.

### Preserve the original three types indefinitely

Rejected as the destination business decision, but retained as the historical
record until this PDR is accepted and per-type technical gates pass.

## Consequences and trade-offs

This resolves future business scope without manufacturing a retrospective
approval. It permits planning across all existing classifications while
requiring evidence one type at a time. The trade-off is deliberately slower
activation, beginning with no Class A types and a narrow Batch 2 technical
cohort.

## Migration and compatibility

This planning record creates no migration, model, field, enum, data backfill,
permission, route, flag or deployment change. Any later implementation must
be additive/reversible and must include a migration or compensating-action
plan where applicable.

## Acceptance criteria

- The historical MSA/NDA/DPA operational restriction and later proposed
  MSA/Order Confirmation/NDA list remain traceable and are not rewritten.
- The authorizing GitHub record accepts or rejects this PDR and names the
  exact first technical cohort.
- No type is exposed solely because it is in business scope.
- Each activated type supplies G, and every Class C path supplies R + G, on
  the immutable reviewed SHA.
- Required production gates have independent Product, Engineering and
  Security reviews, green CI, release record and named-environment operator
  evidence as required by the active Charter.

## Metrics and evidence

Record evidence as GitHub reviews/checks for the immutable SHA and the
applicable deployment/operator record. Track only content-minimized
operational measures (activation attempted/completed, gate failures, rollback
invoked). Do not recreate editable approval votes or timestamps here.

## PRODUCT OWNER DECISION

The Product Owner must make one selection in the authorizing GitHub PR/review
and release record; this blank section is a decision prompt, **not** approval
evidence.

- [ ] **APPROVE EXPANDED BUSINESS SCOPE + BATCHED TECHNICAL ACTIVATION**
- [ ] **APPROVE SPECIFIC TYPES ONLY**
- [ ] **DEFER**
- [ ] **REJECT**

Record through the authoritative GitHub/release evidence system:

- **Approver:**
- **Decision date:**
- **Approved destination scope:**
- **Approved first activation batch/cohort:**
- **Deferred types:**
- **Conditions and required evidence:**
- **Rollback authority:**
- **Authorizing GitHub PR/review and immutable SHA:**
- **Named-environment operator/release record:**

## Approval

Proposed only. Acceptance and any technical activation require the applicable
submitted GitHub reviews, green CI for the unchanged immutable SHA, and the
operator/release evidence required by the active Charter. This PDR alone does
not authorize production activation.
