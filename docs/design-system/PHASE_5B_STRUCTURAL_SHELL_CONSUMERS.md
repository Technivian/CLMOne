# Phase 5B: structural shell consumer migration

Status: complete, pending Phase 5 review.

This record is incremental to Phase 5A. It scopes only the authenticated
structural shell consumers in the dashboard and repository systems. It does
not change their layout, navigation, page content, or behaviour.

## Migration decision

Dashboard Command Center and repository selectors now consume the canonical
authenticated shell hooks: `.dc-ds-shell`, `__sidebar`, `__main`, `__topbar`,
`__content`, `__mobile-toggle`, and `__scrim`. The authenticated shell markup
no longer co-applies its structural compatibility aliases. Source CSS was
moved to the canonical selector before each alias was deleted.

The public-shell `.top-bar` at `base.html` remains intentionally unchanged.
It is a public-rendering concern outside this phase; it has one public runtime
consumer and is not an authenticated compatibility adapter. Dashboard and
repository CSS no longer select it.

## Consumer and deletion evidence

Counts use automated `rg` searches over runtime templates and source CSS.
Generated CSS, documentation, and tests are excluded from the removal gate.

| Item | Before | After | Decision |
|---|---:|---:|---|
| Authenticated structural alias consumers (`main-layout`, `sidebar-container`, `main-area`, `main-content-pad`, `sidebar-scrim`, `mobile-nav-toggle`) | 6 | 0 | Six alias families removed after zero-consumer scan. |
| Authenticated `.top-bar` compatibility consumer | 1 | 0 | Dashboard/repository rules use `__topbar`; base shell is canonical-only. |
| Dashboard/repository direct legacy structural selector occurrences | 23 | 0 | Command Center and repository CSS migrated without visual-rule changes. |
| Public `.top-bar` runtime consumer | 1 | 1 | Retained explicitly as a public-shell boundary. |

The zero-consumer scan confirmed no remaining target alias occurrence in
authenticated templates or source CSS. The generated `global-shell.css` and
`styles.css` were rebuilt through their existing build commands only.

## Validation and visual decision

- `npm --prefix theme/static_src run build:tailwind` and `build:shell`:
  passed.
- `manage.py check`: passed.
- Focused Django shell/navigation suites: 34 passed.
- `phase-5a-app-shell.spec.js`: 3 passed, covering desktop active navigation
  and keyboard focus, 390px drawer/Escape/overflow, and dashboard shell use.
- `git diff --check`: passed.
- The existing Phase 2B.5 no-update visual-baseline replay retains the
  previously classified 550-pixel (0.01%) sidebar-glyph raster variance in
  each snapshot. No baseline, tolerance, or snapshot was regenerated.

## Deferred work

No business, permission, accessibility, or security decision is unresolved.
Phase 5C can separately decide the public-shell boundary and remaining
top-bar/navigation presentation aliases before any public selector removal.
