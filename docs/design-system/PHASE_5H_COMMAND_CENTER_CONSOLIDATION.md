# Phase 5H: Command Center consolidation

Status: complete.

Scope: inventory and consolidate Command Center route-local tokens, dual-class
surfaces, and compatibility selectors onto canonical `.dc-ds-*` APIs for shared
shell/surface/button/toolbar/list patterns. Preserve the expressive portfolio
hero, score ring, KPI strip, governance row, matters table, and rail
operational behaviour. Out of scope: public shell, builders, workspaces, legal
document rendering, and unrelated routes. No content hierarchy redesign.

## Consumers before → after

| Item | Before | After |
|---|---:|---:|
| Hero CTAs (`is-primary` / `is-secondary`) | 4 template + CSS modifiers | 0; `dc-ds-button--primary` / `--link` |
| Section head “View all” / calendar links | bare `<a>` | `dc-ds-button--link` |
| Setup lists (`cc-v3-setup-list` dual) | dual-class | `dc-ds-setup-list` only; CC spacing scoped under `.cc-v3` / rail |
| Surfaces / metrics | already dual `dc-ds-surface*` / `dc-ds-metric*` | unchanged (kept) |
| Stage / risk chips | local `cc-v3-stage` / `cc-v3-risk` | unchanged (not flattened to badges) |
| Legacy `btn-*` / `badge-*` on CC | 0 | 0 |

## Selectors removed (zero-consumer verified)

- Template: `is-primary`, `is-secondary`, `cc-v3-setup-list`
- CSS: `.cc-v3-empty-hero-*`, `.cc-v3-actions-empty`, `.cc-v3-hero--empty`,
  `.cc-v3-setup-copy|icon|arrow`, `.cc-v3-action-icon`, `.cc-v3-rail-footer`,
  `.is-primary` / `.is-secondary` CTA modifiers
- Retargeted: portfolio/hero CTAs → `.dc-ds-button--*`; setup anchors →
  `.dc-ds-setup-action` under `.cc-v3-rail-card` / deadlines

## Validation

- Viewports: 1440, 1280, 390 (overflow + focus on primary CTA / section link)
- Empty/setup: rail-state / setup-action / matters empty remain operable
- Foundation: `test_phase_five_h_command_center_uses_canonical_controls`
- E2E: `client/tests/e2e/phase-5h-command-center.spec.js`
- Visual: Phase 1 dashboard baseline (mask live dates) after regen on fresh E2E DB

## Unresolved decisions (at Phase 5H close)

> **Superseded by Phase 6 (2026-07-19).** Dead `.cc-v3-*` purge and
> repository-wide `btn-*`/`badge-*` retirement are recorded in
> [`PHASE_6_LEGACY_RETIREMENT.md`](PHASE_6_LEGACY_RETIREMENT.md). Stage/risk
> chips remain CC-local by approved exception. `command-center.css` remains
> route-local (optional move tracked in
> [`PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md`](PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md)).

- ~~Broad historical dead `.cc-v3-*` chrome~~ → purged in Phase 6 after
  zero-consumer verification
- Stage/risk chips stay CC-local (badge flatten deferred to avoid visual drift)
- `command-center.css` remains route-local (not postcss/`static_src`) by design

## Recommended Phase 6 scope

> **Completed.** See [`PHASE_6_LEGACY_RETIREMENT.md`](PHASE_6_LEGACY_RETIREMENT.md)
> and ADR/PDR [`0008`](../adr/0008-frontend-design-system-phase-1.md).

Repository-wide retirement of remaining `btn-*` / `badge-*` aliases; optional
Command Center CSS extraction into `static_src` with a thin build step; purge
remaining verified-dead `.cc-v3-*` historical layers; list/matter/privacy page
families onto pure `.dc-ds-*` without dual-class bridges.
