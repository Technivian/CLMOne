# DocClad Frontend Architecture

Status: canonical Phase 1 foundation; Phase 2 (badges/status/empty states) and
Phase 3 (settings and administration) complete — see the phase audit notes
below. Phase 3 landed before Phase 2 in build order; both are done now.
Authority: `DESIGN_CONSTITUTION.md` (the DocClad Governance Charter)

## Authority and ownership

1. The Governance Charter is authoritative when code, screenshots, audits, or
   older documentation conflict with it.
2. `theme/static/css/docclad-tokens.css` is the single source of truth for
   brand and semantic colours, type, spacing, grid, radii, shadows, surfaces,
   focus rings, motion, and chart colours.
3. `theme/static_src/src/design-system/components.css` and the Django
   primitives in `theme/templates/design_system/` form the canonical reusable
   component API. Shared component classes use the `.dc-ds-*` namespace.
4. `theme/static_src/src/design-system/premium.css` is a temporary
   compatibility bridge. It may adapt legacy markup but is not an API for new
   frontend work.
5. `theme/static/css/command-center.css` and `.cc-v3-*` are dashboard-route
   implementation details. They must not be copied into unrelated pages or
   promoted into shared primitives. The approved in-house Command Center is
   frozen unless a task explicitly authorizes a redesign.

## Compatibility policy

The `--ds-*` custom properties are deprecated compatibility aliases. Their
definitions live beside their replacements in `docclad-tokens.css`; every
alias comment names the canonical replacement. Existing consumers continue to
work, but new code must use canonical tokens directly. An alias may be deleted
only after a repository-wide search confirms zero consumers.

The following load-bearing namespaces remain supported until deliberately
migrated:

- `.arch-*`
- `.cform-*`
- `.crs-*`
- legacy `.panel`, `.kpi-card`, `.wq-*`, `.badge-*`, button, and form classes

`.cw-*` was retired by the Contract List design-system migration: its only
production consumer (`contract_list.html`) moved to canonical `.dc-ds-*`
controls, and a repository-wide search confirmed zero remaining consumers.
It is no longer a supported namespace and must not be reintroduced.

Compatibility does not make these namespaces valid for new component design.
Touching a legacy page does not authorize replacing its entire styling system.

## Rules for new frontend work

New work must:

- use canonical tokens instead of raw colour values or page-local tokens;
- reuse `.dc-ds-*` primitives for shared buttons, surfaces, tables, badges,
  forms, alerts, empty states, and page scaffolds;
- use semantic status tokens and the existing status mapping helpers;
- use the canonical focus ring and retain visible keyboard focus;
- keep layout CSS scoped to its page or component contract;
- preserve workspace isolation, RBAC, law-firm mode, and existing behavior.

New work must not introduce:

- page-local colour systems;
- another button, card, table, badge, form, or status-colour system;
- unscoped global CSS;
- `.cc-v3-*` classes outside `dashboard.html` and `command-center.css`;
- broad compatibility-layer deletion without a verified zero-use inventory.

## Verified Phase 1 audit notes

Repository verification on 2026-07-12 found 244 templates, 67 of which contain
style blocks. The audit's count of 185 total templates is therefore stale,
although its conclusion about fragmentation remains correct.

Authentication no longer contains the audit's historical `#315EF6`, but it
still used the older green `#1B7F5A`. Phase 1 maps authentication to canonical
teal through shared tokens without changing the authentication layout or
behavior.

The dashboard stylesheet remains route-scoped and is referenced only by
`dashboard.html`. That template also contains the deliberately preserved
law-firm dashboard branch, so `.cc-v3-*` is technically dashboard-route scoped
rather than exclusively in-house-Command-Center markup. This is existing
architecture drift, not permission to reuse the namespace elsewhere; removing
it requires a separately approved law-firm dashboard migration.

The audit's workflow-layer ownership is also stale. `.arch-*` is defined in
`theme/static_src/src/components.css`; `.cform-*` remains in contract and
workflow-builder templates; and `.crs-*` remains in the Review Studio preview.
`.cw-*` was confined entirely to `contract_list.html`'s own page-local styles
(not `premium.css`, contrary to the original audit) and has since been
retired by the Contract List migration. Phase 1 preserves the remaining
distribution rather than silently beginning a further workflow page
migration.

## Verified Phase 2 audit notes (badges, semantic status, empty states)

Repository verification found two parallel legacy badge systems, not one:
`base.html`'s inline `.badge-{green,blue,yellow,red,purple,gray}` (388
occurrences across 52 templates, driven almost entirely by the 14
`*_badge_class` filters in `contracts/templatetags/docclad_format.py`), and a
near-unused second set (`.badge-{success,warning,danger,info,neutral}` in
`theme/static_src/src/components.css`, ~6 occurrences, demo-page only).
`.dc-ds-badge--*` was already the more complete canonical API design-wise
(7 tone names) but was only reached by 22 includes across 10 files, confined
to settings/admin/identity surfaces.

Canonical semantic vocabulary (8 names, mapped onto the 6 existing
`--status-*-fg/-bg` token pairs — no new colours introduced):

| Semantic | Token pair | `.dc-ds-badge--*` tone | Legacy `.badge-*` |
|---|---|---|---|
| success | `--status-positive-*` | `--success` (alias `--trust`) | `badge-green` |
| information | `--status-progress-*` | `--progress` | `badge-blue` |
| warning | `--status-pending-*` | `--attention` | `badge-yellow` |
| danger / blocking | `--status-danger-*` | `--danger` | `badge-red` |
| neutral | `--status-neutral-*` | `--neutral` (new) | `badge-gray` |
| pending | `--status-pending-*` | `--attention` (shared with warning) | `badge-yellow` |
| inactive | `--status-neutral-*` | `--neutral` (shared with neutral) | `badge-gray` |
| not applicable | `--status-neutral-*` | `--neutral` (shared with neutral) | `badge-gray` |

This lives in code as `LEGACY_BADGE_CLASS` / `CANONICAL_BADGE_TONE` in
`contracts/templatetags/docclad_format.py`, plus the `semantic_badge_tone`
filter for future migrations. `.dc-ds-badge--special` and `--phase` are
retained outside this 8-name vocabulary for existing rare/escalated and
brand-teal lifecycle consumers respectively — `--phase` resolves to `--seal`
(brand teal), not green; it is not a duplicate of `--success`.

All six legacy `.badge-*` colour pairs (plus the unused `.badge-expiring` and
the near-unused `.badge-{success,warning,danger,info,neutral}` set) now
resolve to the same canonical `--status-*-fg/-bg` tokens instead of separately
hardcoded hex — one source of colour, zero template changes, zero page
migrations. An unrelated malformed CSS fragment (a selector-less declaration
block immediately after `.badge-expiring` in `base.html`) was also removed;
it was dead on arrival (invalid CSS, silently dropped by the parser) and
directly adjacent to code already being edited.

Three separate empty-state patterns remain, by design: `.dc-ds-empty` is the
canonical component (13 templates reached); `.empty-state` (34 templates) and
`.wq-empty` (4 shared work-queue partials, rendered on many pages) are
retained adapters, now token-consistent rather than duplicated/hardcoded.
22 additional templates hand-roll empty-state markup that uses none of the
three — cataloged as a migration target, not touched, since fixing them means
editing major list pages (Contract List, Matter List, Client List, Document
List, and others) that later phases own.

`.cc-v3-*` does not exist in the current tree (the Command Center redesign
referencing it is uncommitted, stashed work) — this phase made no changes to
Command Center CSS or markup.

## Migration order

1. **Phase 1 — foundation:** canonical tokens, deprecated aliases,
   authentication alignment, shared focus behavior, and architecture
   documentation. Complete.
2. **Phase 2 — low-risk primitives:** converge badges, semantic status
   presentation, and empty states while retaining adapters. Complete — see
   audit notes above.
3. **Phase 3 — settings and administration:** migrate lower-risk pages already
   close to `.dc-ds-*`. Complete (landed before Phase 2).
4. **Phase 4 — Repository, Approvals, and DPA Reviews:** migrate shared queue
   and table patterns after they are proven.
5. **Phase 5 — core contract workflows:** migrate Contract List, Contract
   Detail, workflow builders, and review surfaces incrementally and last.

The approved Command Center is a visual-quality reference, not a component
source to generalize.
