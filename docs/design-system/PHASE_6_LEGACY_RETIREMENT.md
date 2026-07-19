# Phase 6: final legacy retirement and anti-drift enforcement

Status: **complete** for the authenticated app. Public-shell and legal-document
boundaries remain approved exceptions. Command Center CSS stays route-local
(optional `static_src` move deferred — no visual change).

## Consumers before → after (authenticated templates)

| Family | Before | After |
|---|---:|---:|
| `btn-*` / `badge-*` in `class=` attrs | 100+ dual-class files | **0** |
| List / matter / privacy page families | dual `dc-ds-*` + legacy | pure `.dc-ds-button` / `.dc-ds-badge` |
| Command Center CTAs / setup lists | Phase 5H dual/legacy | pure `.dc-ds-*` (hero expression kept) |
| Global `.btn-*` / `.badge-*` CSS definitions | Present | **Retained** for public/legal exceptions |
| Dead `.cc-v3-*` (zero html/js consumers) | 23+ orphan families | **Purged** from `command-center.css` |

## Selectors / files removed or gated

- Authenticated template dual classes retired repository-wide
- Dead CC layers purged (e.g. `hero-grid/pills/fact`, `score-detail/signals`,
  `portfolio-signals`, `rail-quick-actions`, `head/kicker`, empty-hero remnants)
- Prior 5H removals retained (`empty-hero-*`, `actions-empty`, setup-copy/icon/arrow, …)
- Migration helper: `scripts/phase6_retire_btn_badge_dual_classes.py`
- CC → `static_src` build move: **deferred**

## Enforcement added

| Check | Path |
|---|---|
| Anti-drift (deprecated classes, local `<style>` bans, owned `--dc-ds-*` tokens, dist-only edits) | `scripts/check_design_system_drift.sh` |
| Colour contrast (WCAG UI 3:1 on status/CTA token pairs) | `scripts/check_design_system_contrast.sh` |
| CI workflow | `.github/workflows/design-system-guardrails.yml` |
| Foundation Phase 6 consumer gate | `tests/test_design_system_phase1_foundation.py` |

## Validation evidence

- Template compile sweep: **0** `TemplateSyntaxError` across `theme/templates`
- Full Django suite: **1982 passed**, 32 skipped
- Guardrails: `check_design_system_drift.sh` OK; `check_design_system_contrast.sh` OK
- Representative E2E (`phase-5a`, `phase-5c`, `phase-5h`): **8 passed**
- Visual baselines: CI compares with `--update-snapshots=none`
  (`.github/workflows/visual-regression.yml`); never auto-regenerates

## Approved exceptions (remain)

- Public shell: `landing.html`, `legal_front_door.html`, `registration/*`,
  error pages, `base_fullscreen.html` (and landing `lp-btn-*` family)
- Legal-document typography / content classes outside shell APIs
- Global CSS alias definitions until public shell is migrated
- Route-private builder step chrome (`dpa-step-*`, pickers) as unique local CSS
- CC expressive hero / score / stage-risk chips (not flattened)

## Final completion recommendation

**Ship Phase 6** as the authenticated-app completion gate. Optional follow-on
(Phase 6.1 / public shell): see
[`PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md`](PHASE_6_1_PUBLIC_SHELL_FOLLOWUP.md) —
does not block release. ADR/PDR
[`0008`](../adr/0008-frontend-design-system-phase-1.md) records effective
completion on 2026-07-19.
