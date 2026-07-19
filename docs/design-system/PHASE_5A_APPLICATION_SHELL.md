# Phase 5A: application-shell compatibility cleanup

Status: complete, pending Phase 5 review.

This record is incremental to Phase 4B. It covers the authenticated shell in
`base.html` and its compiled shell source only. Contract-detail workspaces,
workflow builders, review studios, dashboards, public pages, and legal-document
rendering remain outside the phase.

## Canonical shell contract

`base.html` now co-applies the canonical hooks below while retaining the
existing structural names as explicitly deferred compatibility hooks:

| Canonical hook | Shell responsibility |
|---|---|
| `.dc-ds-shell` | Authenticated sidebar/main application frame |
| `__sidebar`, `__main` | Navigation rail and scrollable work surface |
| `__topbar`, `__content` | Sticky page chrome and main content region |
| `__mobile-toggle`, `__scrim` | Mobile navigation control and modal barrier |
| `__page-context`, `__page-title`, `__page-subtitle` | Shell-owned route context |

`shell-primitives.css` is imported after the preserved compatibility source.
It declares the canonical desktop and responsive shell contract, including the
900px drawer and 640px compact top-bar states. The title-promotion script now
targets `__content`, not the legacy content alias. Existing IDs, ARIA state,
keyboard handlers, navigation entries, permission-driven navigation data, and
route behavior are unchanged.

## Consumer and deletion evidence

Counts use automated `rg` searches over runtime templates, JavaScript, and
source CSS; generated CSS, documentation, and tests are excluded unless noted.

| Item | Before | After | Result |
|---|---:|---:|---|
| Canonical shell hooks in authenticated `base.html` | 0 | 10 | Canonical shell API is now present on every authenticated route. |
| `.sidebar-footer-org` runtime consumers | 0 | 0 | Definition removed from foundations. |
| `.sidebar-footer-collapse` runtime consumers | 0 | 0 | Definition and pseudo selectors removed from foundations. |
| `.theme-toggle-btn` runtime consumers | 0 | 0 | Definition and hover selector removed; the product remains intentionally light-only. |
| Dead shell selector definitions | 6 | 0 | Zero-consumer removal gate satisfied. |
| Legacy late subtitle override in `legacy-layout.css` | 1 | 0 | Behavior is now owned by `.dc-ds-shell__page-subtitle`. |

The legacy structural aliases (`.main-layout`, `.sidebar-container`,
`.main-area`, `.top-bar`, `.main-content-pad`, and associated navigation
classes) remain co-applied. They have non-zero consumers in `base.html`,
`command-center.css`, and route-local repository CSS. Removing them would
alter dashboard or repository systems outside this scope, so they are a
documented compatibility exception rather than a partial deletion.

## Validation and visual decision

- `build:tailwind` and `build:shell`: passed; generated CSS was produced only
  by the configured Tailwind v4/PostCSS commands.
- `manage.py check`: passed.
- Focused Django suites: 32 passing tests for shell foundation and workspace
  navigation, including active-navigation and permission coverage.
- `phase-5a-app-shell.spec.js`: 2 passing tests for desktop active navigation
  and focus plus 390px drawer, Escape close, ARIA state, and overflow.
- `git diff --check`: passed.
- The existing Phase 2B.5 baseline replay used `--update-snapshots=none`.
  Both images retain only the previously classified 550-pixel (0.01%) sidebar
  glyph raster variance; no baseline, tolerance, or snapshot was changed.

## Deferred work

No business, permission, accessibility, or security decision is unresolved.
Phase 5B should separately scope the retained structural aliases and
Command Center/repository shell consumers, then migrate their selectors before
the aliases are eligible for zero-consumer deletion.
