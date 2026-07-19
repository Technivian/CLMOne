# Phase 5C: complex contract-detail and workflow-workspace scaffolds

Status: complete, pending Phase 5 review.

This record is incremental to Phase 5B. It covers only the shared shell
structures of contract detail and the DPA, NDA, and MSA workflow workspaces.
Workflow builders, review studios, dashboard, public shell, and legal-document
canvas styling remain outside this phase.

## Canonical workspace contract

`components.css` now defines `.dc-ds-workspace` and structural elements for
the header, title/subtitle, action zone, metadata grid, timeline, main/rail
layout, surfaces, and DPA rail tabs. The contract-detail, DPA, NDA, and MSA
templates co-apply those hooks to every shared structural element. The
canonical source owns the common responsive, focus-visible, overflow, and
surface contract; route-specific documents, risk cards, drawers, and status
logic are unchanged.

The route-prefixed classes remain explicitly deprecated compatibility APIs.
Their four existing template-local compatibility stylesheets still own
document-canvas and specialised governance content, so their runtime consumer
count is non-zero and no local selector was deleted.

## Consumer and deletion evidence

Counts use automated `rg` scans against the four target templates and shared
source; generated CSS, test output, and documentation are excluded.

| Item | Before | After | Decision |
|---|---:|---:|---|
| Canonical workspace hooks in target runtime templates | 0 | 192 | Contract detail, DPA, NDA, and MSA now consume one shared scaffold API. |
| DPA/NDA structural adapter references in `premium.css` | 23 | 0 | Replaced by canonical workspace selectors. |
| Route-local structural compatibility references | 327 | 327 | Retained: each still has template and local-style consumers. |

The removed adapter set includes the old DPA/NDA title row, actions, header,
metadata, timeline, track, grid, and surface selectors. No route-local alias
is eligible for removal until its template and compatibility-style counts are
both zero.

## Validation and baseline decision

- `build:tailwind` and `build:shell`: passed; generated CSS was rebuilt only
  through the configured build scripts.
- `manage.py check`: passed.
- Focused foundation/DPA/NDA/MSA Django suite: 100 passed; two existing DPA
  service expectation failures remain outside this phase
  (`test_clean_submission_creates_no_signals` and
  `test_scc_fallback_toggle_changes_transfer_position_copy`). No contract or
  service code changed in this phase.
- Fresh deterministic E2E: NDA and MSA workspace workflows passed (2); the
  Phase 5C desktop/390px/focus/rail-keyboard/overflow suite passed (2).
- The DPA cockpit E2E remains blocked before workspace navigation by the
  out-of-scope builder heading-name expectation (`New DPA Draft` versus the
  rendered `New DPA DPA intake · Step 1 of 4`).
- Existing Phase 1 visual baselines were replayed with no update. All five
  differ against the current deterministic fixture (dashboard 726 px; list
  15,430; form 33,226; workspace 11,157; detail 52,501). The unaffected
  dashboard/list/form routes and the diff content show stale fixture/text
  baselines rather than a Phase 5C-only visual conclusion. No baseline or
  tolerance was changed.

## Deferred work

No workflow, permission, document-rendering, or status decision is unresolved.
Phase 5D should separately approve deterministic replacement of the obsolete
Phase 1 baselines, then extract the remaining route-local workspace
compatibility styles into shared source and delete aliases only after the
document-canvas boundary has a zero-consumer path.
