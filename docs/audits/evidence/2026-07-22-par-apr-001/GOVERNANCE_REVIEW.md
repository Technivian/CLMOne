# PAR-APR-001 / ADR-0013 — governance review package

**Review date:** 2026-07-22  
**Validation date:** 2026-07-22 (ratification pass)  
**Branch:** `cursor/feat-platform-documentation-alignment-d7f1` @ `c9ae7305` (foundation) · `a97539f2` (governance docs)  
**ADR:** [`docs/governance/decisions/adr/0013-approval-requirement-decision-split.md`](../../../governance/decisions/adr/0013-approval-requirement-decision-split.md)  
**Meeting record:** [`docs/governance/decisions/adr/0013-governance-acceptance-meeting-record-2026-07-22.md`](../../../governance/decisions/adr/0013-governance-acceptance-meeting-record-2026-07-22.md)  
**Ratification report:** [`docs/audits/2026-07-22-adr-0013-ratification-validation.md`](../../../audits/2026-07-22-adr-0013-ratification-validation.md)

---

## 1. Authority chain

| Document | Status | Relevance |
|---|---|---|
| `GOVERNANCE_CHARTER.md` v2.0 | Active | Constitutional authority |
| PDR-0003 | Accepted | Supporting docs adopted |
| `CANONICAL_DOMAIN_MODEL.md` | Accepted | §2.23–2.24 Requirement vs Decision |
| PDR-0001 | Accepted | Finance threshold single entry (unchanged) |
| ADR-0013 | **Pending Ratification** | Submitted; not binding until named approver evidence recorded |
| ADR-0010 | **Proposed** (unchanged) | Not invoked by this review |

---

## 2. Scope under review

### PAR-APR-001 (foundation delivered; closure pending ratification)

**Delivered on continuation branch `c9ae7305`:**

| Deliverable | Evidence |
|---|---|
| Additive `ApprovalRequirement` model | `contracts/models.py`; migration `0110` |
| Additive `ApprovalDecision` model | `contracts/models.py`; migration `0110` |
| Primary dual-write service | `contracts/services/approval_canonical.py` |
| `ApprovalWorkflowService` integration | `contracts/services/approval_workflow.py` |
| Document version binding | FK + `document_version_missing` flag |
| Invalidation on supersession | `invalidate_open_requirements_for_contract()` |
| Legacy mirror | `ApprovalRequirement.legacy_request` OneToOne → `ApprovalRequest` |
| Audit events | `approval.requirement.*`, `approval.decision.recorded` |
| Migration backfill | `migrate-rollback.txt`, `migrate-reforward.txt` |

**Status after ratification validation:**

> **Pending ratification** — canonical foundation delivered at `c9ae7305`; programme closure and ADR-0013 acceptance require named approver evidence. Upon ratification, target closure text: *Closed — canonical foundation delivered and governance accepted; cutover residuals transferred to PAR-APR-002.*

### PAR-APR-002 (opening — planning only)

**Status:**

> Planned — blocked pending owner assignment, cutover plan, and implementation authorization.

ADR-0013 ratification (when complete) would authorize **planning only** — not PAR-APR-002 implementation.

---

## 3. Approver and vote validation

| Required record | Present? |
|---|---|
| Named approver or approved org identifier | **No** |
| Authority basis per approver | **No** |
| Written consent / attendance | **No** |
| Vote timestamp | **No** (date only) |

**Outcome:** ADR-0013 remains **Pending Ratification**. Do not treat draft §1 votes as binding.

---

## 4. Residuals transferred to PAR-APR-002 (upon PAR-APR-001 closure)

1. Legacy `ApprovalRequest` read-path retirement
2. `DPAReviewPack` parallel approval model merge
3. `ApprovalRoute` → runtime requirement mapping
4. `ABSTAIN` / `REVOKE` UI wiring
5. Full-suite regression with zero named residuals
6. Tranche-1 landed on `main` (PR #50 — **not merged**)
7. Cutover plan + owner assignment + implementation authorization

---

## 5. Test and isolation caveats

See [`TEST_RESULTS.md`](TEST_RESULTS.md).

**Programme-level tenant isolation remains unproven until PAR-SEC-003 is resolved.**

Known programme test issues (not PAR-APR regressions):

1. `WorkflowRoutingTests.test_workflow_dashboard_and_detail_surface_routing_endpoints`
2. `ContractIsolationTest.test_list_shows_only_own_org`

---

## 6. Planning-only authorization boundary

| Authorized now | Not authorized |
|---|---|
| PAR-APR-002 checklist maintenance | PAR-APR-002 implementation |
| Owner assignment workshop | Legacy path retirement |
| Cutover plan drafting | Code or migration changes beyond `c9ae7305` foundation |
