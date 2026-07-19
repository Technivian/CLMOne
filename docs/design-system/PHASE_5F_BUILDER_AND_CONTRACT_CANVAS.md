# Phase 5F: builder generation and contract-canvas consolidation

Status: complete.

Incremental to Phase 5E. Scope: DPA/NDA/MSA builder shell sharing, full
builder→validation→generation→contract-detail E2E, contract-detail canvas
migration to `.dc-ds-workspace--record`, and exact-match CTA/badge remap on
governed workspaces. Command Center, public shell, and unrelated pages remain
out of scope. Legal-document content, document typography, permissions,
validation, workflow state, and audit behaviour are preserved.

## Flows covered

| Flow | Coverage |
|---|---|
| DPA step validation (empty continue) | `client/tests/e2e/dpa-workflow.spec.js` |
| DPA steps 1–4 → review → Generate → workspace | same |
| Workspace → View contract record → `/contracts/<pk>/` | DPA/NDA/MSA E2E |
| Desktop + 390px overflow on generated workspace | DPA E2E |
| Keyboard focus on record link and primary action | DPA E2E |
| Fixture workspace rail/clause-link/390px | `dpa-cockpit.spec.js`, `phase-5c-workspace-shell.spec.js` |
| Blocked / next-action surface on record canvas | contract-detail template + Django record-shell tests |

Generation still lands on `/contracts/workflows/<pk>/` (`workflow_detail`).
The hop to contract-detail is an explicit **View contract record** link when
`workflow.contract` exists.

## Consumer evidence

| Item | Before | After | Decision |
|---|---:|---:|---|
| Shared builder cockpit CSS (`cform-*` / unscoped `arch-workspace-*`) | Inline in NDA (~389 LOC) + MSA (~603 LOC) templates | `global-shell/workflow-builder-cockpit.css` (76 LOC) imported by shell | Extracted only genuinely shared primitives |
| NDA builder template size | 389 lines | 314 lines | Shared CSS removed; route-specific chrome retained |
| MSA builder template size | 603 lines | 525 lines | Shared CSS removed; MSA accordion/preview retained local |
| Contract-detail structural shell tokens (`contract-command-strip`, `contract-workspace-grid`, `contract-surface`, kickers as shell) | 19+ template/CSS structural hits | 0 | Migrated to `dc-ds-workspace--record` + canonical layout/surface hooks |
| Workspace CTA/badge/action tokens (`__cta` / `__badge` / `__action--*` after 5E, or prior `*-ws-cta` / `*-ws-badge`) | Present on DPA/NDA/MSA workspaces | 0 (container `__actions` retained) | Remapped to `dc-ds-button--*` / `dc-ds-badge--*` where semantics matched |

Domain content classes on the record canvas (`contract-finding-*`,
`contract-checklist-*`, dialogs, `contract-command-title` / `-context`) remain
because they encode record-domain structure, not shell layout.

## Selectors removed after zero-consumer verification

- Template structural: `contract-command-strip`, `contract-workspace-grid`,
  `contract-surface` (as surface shell), `contract-surface-kicker`
- Workspace content: `dc-ds-workspace__cta`, `dc-ds-workspace__badge`,
  `dc-ds-workspace__action--secondary`, `dc-ds-workspace__action--accent`
- Matching CSS rules for those hooks from `workspaces.css` / prior casefile
  adapters (already absent after remap)

## Validation

- `npm run build:tailwind` + `build:shell` in `theme/static_src` (compiled CSS only via those commands).
- Focused Django: foundation (incl. Phase 5F), design-system, contract detail record shell, DPA/nav/launch: 226 passed.
- E2E: `dpa-workflow`, `nda-workflow`, `msa-workflow`, `dpa-cockpit`, `phase-5c-workspace-shell` (7) + DPA full path (1).
- Visual baselines regenerated then replayed without update: 5 passed.

## Unresolved decisions

None blocking. DPA four-step intake CSS remains largely local (step-specific
controls); only shared NDA/MSA cockpit primitives were consolidated. Legacy
`btn-cta` / `btn-quiet` / `badge-sm` dual classes remain on contract-detail for
compat sizing hooks and can retire in a later pass once dual-class CSS is gone.

## Recommended Phase 5G

1. Retire residual dual-class button/badge aliases (`btn-cta`, `btn-quiet`,
   `badge-*`) on the record canvas after zero dual-class CSS consumers.
2. Extract remaining DPA intake step chrome into shared builder primitives where
   step UX truly overlaps NDA/MSA.
3. Optionally deepen generation-error and blocked-state Playwright assertions
   beyond the current empty-step validation + record next-action surface.
