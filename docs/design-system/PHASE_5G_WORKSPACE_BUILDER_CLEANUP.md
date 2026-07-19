# Phase 5G: workspace and builder compatibility cleanup

Status: complete.

Incremental to Phase 5F. Scope: dual-class `btn-*` / `badge-*` retirement on the
contract-detail record canvas and MSA builder guard hook, shared DPA intake /
review chrome extraction into `workflow-builder-cockpit.css`, and deepened
Playwright coverage for failed validation, governance blocked findings, signature
routing blockers, and review-without-intake recovery. Command Center, public
shell, and unrelated page systems remain out of scope. Generation logic,
workflow state, permissions, audit events, and legal-document rendering are
unchanged.

## Consumer evidence

| Item | Before | After | Decision |
|---|---:|---:|---|
| `contract_detail.html` dual-class `btn-cta` / `btn-quiet` / `btn-soft-primary` | 23 dual-token hits | 0 | Stripped; canonical `dc-ds-button--*` only |
| `contract_detail.html` dual-class `badge-sm` / `badge-*` colors | Included in those hits | 0 | Remapped via `dc-ds-badge--{tone}` / `legacy_badge_tone` |
| `workspaces.css` dual-class combinators (`.btn-cta`, `.btn-quiet`, `.badge-sm`) | 5 | 0 | Selectors now pure `dc-ds-button` / `dc-ds-badge` |
| MSA `.btn-cta.is-guarded` | 1 local rule | 0 | Moved to shared `.dc-ds-button--primary.is-guarded` |
| DPA builder shared field/panel/review chrome | ~127 LOC inline | In `workflow-builder-cockpit.css` | Extracted overlapping intake chrome |
| DPA builder template LOC | 478 | 439 | Unique nav / step3–4 / pickers retained local |
| DPA review inline `<style>` | Present | 0 | Review card chrome shared with builder system |

Global `.btn-cta` / `.badge-*` aliases in `premium.css` / `shared-components.css`
are **retained** — other page families still consume them (zero-consumer gate not
met repository-wide).

## Selectors removed (scoped)

- Template dual classes on contract-detail: `btn-cta`, `btn-quiet`, `btn-soft-primary`,
  `badge-sm`, `badge-yellow|red|blue|green|gray` (as co-classes)
- Record CSS combinators requiring those dual classes in `workspaces.css`
- MSA local `.btn-cta.is-guarded`
- DPA review template `<style>` block (moved, not deleted behaviour)

## Flows covered (Playwright)

| Flow | Spec |
|---|---|
| Step 3 empty continue → errors → recover to step 4 | `phase-5g-builder-errors.spec.js` |
| Governance “Blocked” finding + Back to edit recovery | same |
| Deterministic signature blockers on `/contracts/1/` (desktop + 390px + focus) | same |
| Review without intake → redirect + recovery message | same |
| Full generate happy path (retained) | `dpa-workflow.spec.js` |

## Validation

- `npm run build:tailwind` + `build:shell`
- Focused Django: foundation (incl. 5G), design-system, contract detail, DPA: 154 passed
- E2E: `phase-5g-builder-errors` (4), plus prior dpa/5c cockpit suite green in session
- Visual baselines: fresh E2E DB regen + replay (5 passed)

## Unresolved decisions

Global `btn-*` / `badge-*` CSS aliases remain until a repository-wide zero-consumer
pass (lists, matters, privacy, review studio, etc.). Review-page generate with
invalid session still redirects silently without flash — coverage uses the
documented empty-review GET recovery path instead.

## Recommended next phase (Command Center)

Begin a dedicated Command Center shell/compatibility phase: inventory CC
route-local canvas and dual-class consumers, map to canonical shell/workspace
primitives where semantics match, and keep CC operating-surface behaviour and
live due-date semantics unchanged.
