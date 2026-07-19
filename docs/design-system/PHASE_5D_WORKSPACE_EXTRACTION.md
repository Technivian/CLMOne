# Phase 5D: workspace-source extraction and entry-gate decisions

Status: approved entry gates completed; Phase 5D implementation in progress.

This is incremental to Phase 5C. It covers DPA, NDA, and MSA contract
workspace sources only. Command Center, public shell, builders, review studio,
and legal-document rendering remain outside this record.

## Entry-gate decisions

| Gate | Classification and evidence | Decision |
|---|---|---|
| DPA service: former `test_clean_submission_creates_no_signals` | Stale test contract. `contracts/services/dpa_workflow.py` intentionally creates the mandatory `dpa_review_required` signal for every DPA, including otherwise clean data. | Fixed the assertion to verify the required signal; no product change or test debt. |
| DPA service: former `test_scc_fallback_toggle_changes_transfer_position_copy` | Stale test contract. Rendered transfer language is governed by the explicit `transfer_mechanism`; `include_scc_fallback` is independently a risk-signal input. | Fixed the test to compare confirmed SCC with no confirmed safeguard; no product change or test debt. |
| DPA intake heading E2E | Stale accessible-name matcher. The current authenticated builder renders `New DPA` plus its intake-step text, rather than the retired `New DPA Draft` name. | Fixed only the matcher to accept the stable `New DPA` heading prefix. The builder is untouched. No test debt. |

The two service expectations and heading matcher are fixed, not deferred: they
contradicted the current intentional service and rendered semantics. A further
E2E discovery during that repair is recorded below rather than hidden.

| Test debt | Owner | Risk | Rationale | Expiry |
|---|---|---|---|---|
| Legacy single-page DPA cockpit E2E | Contracts workflow team | Medium: end-to-end coverage of the full DPA generation path is temporarily absent. | The test asserts the retired one-page intake’s `AI Smart Questions`, live-preview, and submission IDs. The current approved four-step builder has different, intentional interaction and confirmation stages. Rewriting that workflow test is builder-specific work, outside Phase 5D. It is explicitly skipped with this record. | 2026-08-15 |

The stable heading and intake-navigation assertion replaces the broken first
screen expectation so the current accessible page contract remains covered.

## Deterministic baseline replacement approval

Decision status: **approved before regeneration** on 2026-07-18.

Decision authority: the CLM One design-system approver, through the Phase 5D
instruction to “document and approve replacement of the five stale Phase 1
baselines using deterministic fixtures.” The existing replay, recorded in
Phase 5C, showed dashboard 726 px, list 15,430 px, form 33,226 px, workspace
11,157 px, and detail 52,501 px differences. The diffs track the seeded,
deterministic fixture content and prior approved scaffold/form changes; they
are not evidence of a new DPA/NDA/MSA workspace regression.

Approved replacement targets, all from `visual-baselines.spec.js` at the fixed
1440 x 1000 viewport with animations disabled and the standard deterministic
E2E database setup:

| Snapshot | Reason for obsolescence | Approval |
|---|---|---|
| `phase-1-dashboard-darwin.png` | Seeded dashboard content and renderer glyph output differ from the pre-Phase-1 capture. | Approved replacement. |
| `phase-1-list-darwin.png` | Deterministic repository fixture and approved list scaffold changed. | Approved replacement. |
| `phase-1-form-darwin.png` | Deterministic form fixture and approved form scaffold changed. | Approved replacement. |
| `phase-1-workspace-darwin.png` | Deterministic workspace fixture and approved workspace shell changed. | Approved replacement. |
| `phase-1-detail-darwin.png` | Deterministic record fixture and approved detail scaffold changed. | Approved replacement. |

Snapshots will be regenerated only by the configured Playwright update command
after this approval record exists, then replayed without update. No tolerance
will be changed to make a test pass.

During the approved refresh, the first dashboard replay crossed a calendar-day
boundary. Its only changed pixels were the live relative due-date and activity
age labels (`2 days`/`1 day`, `Due tomorrow`/`Due today`). The fixture records
are deterministic, but those labels correctly derive from the runtime clock.
The visual helper therefore masks only those three live-label regions on the
dashboard; the deterministic record content, layout, colours, and all other
text remain asserted. This is an approved test-fixture stabilization, not a
production Command Center change or a tolerance increase. The dashboard
snapshot is replaced again only after this evidence was recorded.

The workspace capture also contained the existing `reveal-stagger` entrance
treatment. A replay observed it mid-animation before Playwright applied its
screenshot-only animation disabling. The helper now emulates the supported
reduced-motion preference before navigation and the final-state readiness
assertion; this preserves the already-approved final visual state and makes
the capture deterministic.

## Phase 5D source and compatibility evidence

`global-shell/workspaces.css`, imported after the existing shell sources,
becomes the active shared source for DPA, NDA, and MSA workspace structure and
their route-owned workspace content. The templates contain no runtime style
element. Deprecated `dpa-ws-*`, `nda-ws-*`, and `msa-ws-*` class attributes
remain co-applied where they name legal-document, risk, drawer, or test-facing
content; they are compatibility attributes, not removable aliases in this
phase until each has a verified zero-runtime-consumer path.

## Consumer, deletion, and validation evidence

Automated scans strip Django comment blocks before counting template runtime
output. The three targeted templates changed from three local runtime style
blocks to zero. Remaining route-prefixed workspace tokens are DPA 66, NDA 57,
and MSA 90; they name document-canvas, risk, drawer, action, and test-facing
content, so no compatibility alias was eligible for deletion. The structural
`dpa-ws-*`, `nda-ws-*`, and `msa-ws-*` selector definitions now have zero
active CSS definitions outside the shared source’s route-owned content rules.

The retired structural source was replaced by canonical
`.dc-ds-workspace--workflow`, `.dc-ds-workspace--msa`, and `__*` element
selectors in `global-shell/workspaces.css`. Three route-local runtime style
elements were removed from execution; no live compatibility class was deleted
while its runtime count is non-zero.

- Tailwind and shell builds passed; compiled files were produced only by the
  configured build commands.
- Focused design-system, foundation, DPA, NDA, and MSA Django suite passed:
  129 tests. `manage.py check` and `git diff --check` passed.
- DPA heading, NDA, MSA, and Phase 5C desktop/390px/focus/overflow E2E tests
  passed in isolated deterministic runs (5 passed, 1 documented DPA skip).
- All five approved visual baselines were regenerated and replayed without
  update individually: dashboard, list, form, workspace, and detail passed.
  A combined Playwright run intermittently closed a browser context after a
  prior test; isolated reruns passed and no application regression was found.
