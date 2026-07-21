# Platform Alignment Roadmap

**Created:** 2026-07-21  
**Authority:** Gap audit `docs/audits/2026-07-21-platform-gap-audit.md` · Charter · PDR-0003  
**Branch:** `cursor/feat-platform-documentation-alignment-d7f1`  

Statuses: Completed · Blocked · Deferred by approved decision · Future roadmap · Cancelled with rationale

---

## Completed this programme

| ID | Title | Class | Notes |
|---|---|---|---|
| PAR-WF-001 | Enforce published template mutate gates | Foundation | UpdateView + Admin locked |
| PAR-AUD-001 | Admin published immutability | Foundation | Bundled with PAR-WF-001 |
| PAR-WF-002 | Govern live instance template migration | Foundation | Reason + AuditLog; Proposed ADR-0010 |
| PAR-WF-003 | Default new templates unpublished | Foundation | Model + migration 0105 |
| PAR-WF-005 | Workflow invariant tests | Foundation | `tests/test_platform_workflow_invariants.py` |
| PAR-NAV-001 | Data Manager + Entities nav | Pilot hardening | Hub + Counterparty as Entities |
| PAR-SEC-001 | Auth redirect / isolation defects | Pilot hardening | Legacy list aliases require login; activity tenant check |
| PAR-WORK-001 | My Work vs Command Center boundaries | Pilot hardening | `docs/product/MY_WORK_AND_COMMAND_CENTER_BOUNDARIES.md` |

---

## Proposed decisions (awaiting approval)

| ID | Title | Status |
|---|---|---|
| ADR-0010 | Workflow instance version pinning interim | **Proposed** — `docs/governance/decisions/adr/0010-workflow-instance-version-pinning-interim.md` |

---

## Blocked (external / governance)

| Item | Why |
|---|---|
| Charter v3 activation | Human governance approval required (PDR-0003) |
| Production Definition/Version cutover | Needs Accepted ADR + ops window |
| External IdP production credentials | External dependency |
| Commercial vuln-scan SaaS evidence | External tooling |

---

## Future roadmap (Core / Enterprise — not claimed complete)

| ID | Title | Class | Decision needed |
|---|---|---|---|
| PAR-WF-010 | Workflow Definition aggregate | Core | ADR |
| PAR-OBL-001 | First-class Obligation | Core | ADR/PDR |
| PAR-OBL-002 | Reminder object | Core | — |
| PAR-EXC-001 | Governed Exception | Core | PDR |
| PAR-CORE-001 | Complete remaining PDR-0002 UI/test drift | Pilot hardening | — |
| PAR-CORE-003 | Contract Record provenance completeness | Core | — |
| PAR-ID-001 | Role Definition reconciliation | Core | ADR |
| PAR-DATA-001 | Property Definition CRUD | Core | PDR/ADR |
| PAR-AI-001 | AI Suggestion provenance | Core | — |
| PAR-APR-001 | Approval Requirement/Decision split | Core | — |
| PAR-ENT-001 | Entity Relationship graph | Enterprise | — |
| PAR-INT-001 | Generic Integration Connection | Enterprise | — |
| PAR-DOC-001 | Document Version entity harden | Core | — |

---

## Item detail (completed)

### PAR-WF-001 / PAR-AUD-001 — Completed
Published templates cannot be edited via UpdateView or Admin; must clone/unpublish via product paths.

### PAR-WF-002 — Completed
`migrate_workflows_to_template` requires `reason`, emits AuditLog `workflow_instance_template_migrated`; management command requires `--migration-reason`.

### PAR-WF-003 — Completed
`WorkflowTemplate.is_active` default `False`; migration `0105_workflowtemplate_is_active_default_false.py`.

### PAR-WF-005 — Completed
Invariant suite covers defaults, mutate gate, simulation dry-run, migration audit, publish validation block.

### PAR-NAV-001 — Completed
Nav: Data Manager → `/contracts/data-manager/`; Entities → counterparties list. Hub documents Property Definition gap.

### PAR-SEC-001 — Completed
`ContractListView` / `DeadlineListView` authenticate before alias redirect; `workflow_template_activity` tenant-checks before redirect.

### PAR-WORK-001 — Completed
Boundary doc published; no semantic merge.

---

## Progress log

| Timestamp (UTC) | Event |
|---|---|
| 2026-07-21 | Audit + roadmap authored; foundation + pilot slices implemented and verified (74 tests OK) |
