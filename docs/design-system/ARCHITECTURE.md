# DocClad Frontend Architecture

Status: canonical Phase 1 foundation
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
- `.cw-*`
- `.cform-*`
- `.crs-*`
- legacy `.panel`, `.kpi-card`, `.wq-*`, `.badge-*`, button, and form classes

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
`theme/static_src/src/components.css`, but `.cw-*` is split between
`premium.css` and `contract_list.html`; `.cform-*` remains in contract and
workflow-builder templates; and `.crs-*` remains in the Review Studio preview.
Phase 1 preserves this distribution rather than silently beginning a workflow
page migration.

## Migration order

1. **Phase 1 — foundation:** canonical tokens, deprecated aliases,
   authentication alignment, shared focus behavior, and architecture
   documentation.
2. **Phase 2 — low-risk primitives:** converge badges, semantic status
   presentation, and empty states while retaining adapters.
3. **Phase 3 — settings and administration:** migrate lower-risk pages already
   close to `.dc-ds-*`.
4. **Phase 4 — Repository, Approvals, and DPA Reviews:** migrate shared queue
   and table patterns after they are proven.
5. **Phase 5 — core contract workflows:** migrate Contract List, Contract
   Detail, workflow builders, and review surfaces incrementally and last.

The approved Command Center is a visual-quality reference, not a component
source to generalize.
