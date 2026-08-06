# Shared workflow and Contract Record repair

Status: **Proposed / NO-GO**. This is repair evidence, not approval to merge,
deploy, activate production access, or create a release exception.

## Source and boundaries

- Remote main recorded at task start: `4d194dcc0663b94accf4eb892c508fe70cf2d3a7`.
- Repair branch: `codex/payrollminds-shared-workflow-repair`.
- Validated implementation SHA: `361e4739aabc1de38ca51e500d1eae6a2b23d865`
  (initial repair `50aae7d4f090e36eff08a1a0b19ad747373185c6`).
- Foundation: PR #153 runner repair, PR #158 dependency remediation, PR #159
  MSA fixture/postback repair, and PR #161 critical repair.
- E2E uses a fresh local SQLite database and synthetic fixtures only. External
  AI is disabled; no real customer data, production credentials, signatures,
  inbound email, portals, or live providers were used.
- PR #162 is recorded as an unrelated, isolated draft security capability. It
  is not an ancestor of this branch and was not cherry-picked, rebased, merged,
  activated, or otherwise included. Authentication code and configuration were
  not changed by this repair, and no MFA activation occurred.

## Exact repaired records

| Test ID | Route | Scenario and expected behavior | Actual cause | Canonical service | Cluster |
| --- | --- | --- | --- | --- | --- |
| `d3423a6dec4bff43ec8a-bc0c98de23428e11624e` | Contract workflow tab | Render structured deterministic review, including overdue dates | Shared renderer reduced structured data to one text string | `contract_ai_assistant` / contract detail renderer | D-SHARED-WORKFLOW |
| `d3423a6dec4bff43ec8a-1a9217ac4de00eb7548d` | Contract workflow tab | Policy rejection is explicit and the action recovers | Retired review-panel expectation | `contract_ai_assistant` policy path | D-SHARED-WORKFLOW |
| `d3423a6dec4bff43ec8a-2c017268bc8dcf22decf` | Contract workflow tab | Duplicate review submissions are prevented | Retired selector plus a fast-response re-enable race | `contract_ai_assistant` client guard | D-SHARED-WORKFLOW |
| `0815266e2b373abe5480-1597233b7e54ae6ff2f7` | `/contracts/workflows/1/` | DPA drafting workspace remains accessible and contained | Retired broad-text/layout selector | DPA workflow workspace | D-SHARED-WORKFLOW |
| `f0fb41fd16ce65710d14-ce229ae95d14323a4755` | MSA workflow and Contract Record | Focusable real action and current record shell | Retired hidden action and inaccessible fixture identity | MSA workflow / Contract Detail | D-SHARED-WORKFLOW |
| `f0fb41fd16ce65710d14-6b0484165e5db34bfedd` | `/contracts/workflows/1/` | DPA tabs work by keyboard at 390px | Retired drafting marker selector | DPA workflow workspace tabs | D-SHARED-WORKFLOW |
| `b2b658ee7428d119be23-7f0f365fa78e5284615b` | Contract Record workflow tab | Truthful signature-routing prerequisite remains visible | Retired presentation-only blocker list and seed-order assumption | `get_signature_routing_blockers` / Contract Detail | D-SHARED-WORKFLOW |

The canonical path was traced as Workflow Definition → immutable Workflow
Version → Workflow Instance → Contract Record, with Document/DocumentVersion,
approval, work-item, provenance, authorization, and audit services inspected
where each surface uses them. No workflow instance/version binding, record
provenance, document immutability, workflow transition, permission, or audit
path was changed.

## Corrections and invariants

The primary application defect was the workflow-tab renderer: it discarded the
structured, tenant-local response already returned by the governed review
endpoint. The corrected renderer creates Summary, Key dates, Risks,
Recommendations, and field-evidence sections with DOM text APIs. It does not
alter the response, send data externally, make suggestions authoritative, or
change the existing audit event.

CI then exposed a fast-response duplicate-submit race hidden by the initial
local timing. A successful review is now idempotent for the unchanged prompt;
editing the prompt enables a new review, while a failed review still enables
immediate recovery. This changes no server-side workflow or record state.

The other six records used stale selectors, retired presentation assumptions,
or a fixture identity outside the authenticated E2E workspace. They now test
the permission-aware repository row, the canonical workflow tab, visible DPA
clause link, native tab roles, and truthful signature requirement. The
lower-level `test_workflow_operations` fixture was also made valid:
`IN_PROGRESS + INTERNAL_REVIEW`; the workflow queue remains `ACTIVE`.

Published versions remain immutable and pinned; blocking prerequisites still
prevent progression; Contract Record provenance, immutable DocumentVersions,
authorized assignment/approval, server-side authorization, and append-only
audit behavior are unchanged. No migration is required. Rollback is a revert
of commits `361e4739` and `50aae7d4`; it is stateless apart from normal
test-created local data.

## Validation on the implementation SHA

| Selection | Result |
| --- | --- |
| Exact seven records | 7 passed, 0 failed, 0 skipped |
| Four affected Playwright files | 11 passed |
| Workflow/version/record/provenance/assignment/approval/audit/negative-auth selection | 229 passed |
| `tests.test_workflow_operations` regression | 6 passed |
| PayrollMinds verification | 17 passed |
| PR #161 category-B collection | 16 passed |
| Duplicate-submit race stress | 20/20 passed |
| Unfiltered Playwright collection | 90 collected; 59 passed; 31 failed; 0 skipped; 0 interrupted |
| Full Django baseline | 2,627 run; inherited 35 failures / 13 errors / 32 skipped (foundation: 35 failures / 19 errors) |
| Configuration and schema | Django check passed; no migration drift |
| Design and security | Anti-drift, contrast, Bandit high, pip-audit, and both npm audits passed |

The unfiltered run's 31 failed identifiers are all pre-existing unresolved
shared-UI or visual-baseline identifiers; no B or D-SHARED-WORKFLOW identifier
failed and no new identifier appeared. The 26 shared-UI classifications and
snapshot classifications were not modified.

## Security, audit, and release posture

Focused authorization-negative coverage passed in the 229-test selection,
including cross-tenant Contract and AI-context denial. The repair has no
authorization, tenancy, export/download, storage, encryption, retention, or
permission impact. The deterministic review invocation continues to emit the
existing audit event; the render-only correction does not mutate Contract
Record state.

The full unit comparison and local security/design checks are recorded above.
The first CI run exposed the duplicate-submit race and the final SHA is awaiting
fresh CI. An attached-server unfiltered rerun was discarded because stdout
backpressure stalled requests; it is not used as product evidence. The
authoritative isolated CI shards remain the bounded path for full-browser
evidence. The complete browser collection also retains unrelated shared-UI and
visual-baseline failures. Therefore the required recommendation remains
**NO-GO** pending final-SHA CI, while this branch stays independently reviewable
from PR #162 and all authentication work.
