# Phase 5E: workspace compatibility retirement

Status: complete.

This record is incremental to Phase 5D. It covers only DPA, NDA, and MSA
contract workspace content and JavaScript consumers. Command Center, public
shell, builders, review studio, and domain workflow logic remain out of scope.

## Consumer evidence

Counts use automated scans of the three workspace templates after stripping
Django comment blocks. Content consumers are route-prefixed class tokens that
were not already co-applied with a canonical `dc-ds-workspace__*` hook.

| Item | Before | After | Decision |
|---|---:|---:|---|
| DPA route-prefixed content/JS consumers | 66 | 0 | Migrated to canonical workspace hooks. |
| NDA route-prefixed content/JS consumers | 57 | 0 | Migrated to canonical workspace hooks. |
| MSA route-prefixed content/JS consumers | 90 | 0 | Migrated to canonical workspace hooks. |
| Total | 213 | 0 | Zero-consumer gate met for retirement. |

Canonical content hooks now cover document canvas, risk/approval/audit cards,
KV pairs, rail items, CTAs/actions/badges, MSA summary/drafting/drawer/tabs,
and rail panes. Legal-document rendering is preserved via
`.dc-ds-workspace--workflow` / `.dc-ds-workspace--msa` scoped rules.

## Stable semantic hooks retained for JavaScript

These are not compatibility class aliases; they remain because behaviour
depends on them:

- `data-clause-link` and `.dc-ds-workspace__clause.is-linked`
- `data-workspace-rail-tab` / `data-workspace-rail-pane` (DPA rail)
- `data-workspace-open-governance`, `data-workspace-tab`, `data-workspace-layout` (MSA)
- Element IDs such as `dpa-rail-*`, `msa-governance-drawer`, pane IDs

## Selectors removed after zero-consumer verification

Removed from `global-shell/workspaces.css` and casefile overrides in
`premium.css` (non-exhaustive; all matching route-prefixed workspace content
selectors are gone):

- `.dpa-ws-*`, `.nda-ws-*`, `.msa-ws-*` content/action/badge/drawer/tabs rules
- `.dpa-doc` / `.nda-doc` / `.msa-doc`, `.dpa-clause` / `.nda-clause` / `.msa-clause`
- `.dpa-risk-*` / `.nda-risk-*` / `.msa-risk-*`, approval/audit/KV/rail/field-chip families
- Casefile `:is(.dpa-ws-cta, .nda-ws-cta, .msa-ws-cta)` and action-teal/secondary adapters

Structural co-applied route attributes (`dpa-ws-header`, `nda-ws-card`, and
peers) were also removed from the three templates once their CSS consumers
were already canonical.

## DPA E2E debt

| Item | Status |
|---|---|
| Legacy single-page DPA cockpit E2E | Closed for Phase 5E. Replaced with a governed-workspace interaction test against the deterministic fixture (`/contracts/workflows/1/`) covering rail keyboard use, clause linking, and 390px overflow. |
| Four-step DPA builder generation path | Remains builder-owned. Builders are out of Phase 5E scope; full intake→generate coverage is recommended for Phase 5F. |
| DPA intake heading assertion | Retained; still passes. |

## Validation

- `build:tailwind` and `build:shell`: passed; compiled CSS produced only by those commands.
- `manage.py check` under test settings: passed.
- Focused Django suite (foundation, design-system, DPA, nav workspace, launch setup): 169 passed.
- E2E isolated: DPA heading + governed workspace (rail/clause-link/390px overflow) passed (2);
  Phase 5C desktop/390px/focus/rail keyboard passed (2); NDA and MSA workflow passed (2).
- Visual baselines regenerated after retirement, then replayed without update: 5 passed.

## Unresolved decisions

None for workspace compatibility retirement. Document-canvas visual behaviour
is intentionally preserved under canonical hooks rather than redesigned.

## Recommended Phase 5F

1. Author a deterministic four-step DPA builder→workspace generation E2E
   without relying on retired single-page cockpit IDs.
2. Retire remaining contract-detail route-local canvas families that sit
   beside `.dc-ds-workspace` but were outside this workspace content gate.
3. Optionally map workspace CTA/badge hooks onto shared `dc-ds-button` /
   `dc-ds-badge` where visual parity is already guaranteed.
