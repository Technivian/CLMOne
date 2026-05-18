# BATCH 3 — WORKSPACE MIGRATION PLAN

Date: 2026-05-18
Status: PRE-MIGRATION DECISIONS RESOLVED — CLEARED TO BEGIN
Author: Design Unification Pass
Governing sources: DESIGN_CONSTITUTION.md · DESIGN_ARCHETYPE_PATTERNS.md · DESIGN_ARCHETYPE_MAP.md

---

## HARD RULES FOR THIS BATCH

Before reading any section below, the following rules are non-negotiable:

- NO template migrations until this plan is reviewed and approved.
- NO redesigns. Migrate to canonical, not to new.
- NO new components unless a canonical equivalent does not exist and the gap is documented.
- NO business-logic changes, view changes, or URL changes.
- NO visual experimentation. Strict primitive substitution only.
- NO archetype mixing. Each page migrates to its single assigned archetype.
- ONE page migrated per PR. Never batch two pages in one diff.

---

## BATCH 3 SCOPE SUMMARY

Total templates in scope: **8**
Total lines of template HTML in scope: **1,158**
Archetype split:
- WorkspacePage: 5 templates (dashboard.html, workflow_dashboard.html, repository.html, privacy_dashboard.html, legal_task_board.html)
- ExceptionPage: 3 templates (operations_dashboard.html, deadline_list.html, notification_list.html)

Estimated migration difficulty: **Medium** (see per-page risk scores)
Estimated Batch 3 scope size: **Medium-Large** — 8 pages, significant primitive churn on 3 of them, behavioral complexity on 2
Highest-risk page: **legal_task_board.html** (Kanban AJAX + inline event handlers)
Safest page: **notification_list.html** (55 lines, no JS, clear ExceptionPage pattern)

---

## BATCH 3 PREREQUISITES (must be verified before any edit)

### Pre-migration decisions — RESOLVED 2026-05-18

**Decision 1 — `action-chip` status:** RETIRED. Replace with `btn-ghost` in `dashboard.html`. Remove `action-chip` CSS block from `base.html` after `dashboard.html` migration is validated. Only `dashboard.html` is affected (3 instances). Documented in `DESIGN_CONSTITUTION.md` section 5 under Retired button-adjacent classes.

**Decision 2 — Kanban/BoardView governance:** PROMOTED to WorkspacePage/BoardView subvariant. New primitives `board-track`, `board-col`, `board-card`, `board-col-head` are defined. CSS definitions to be added to `base.html` during `legal_task_board.html` migration. Inline `onclick` handlers replaced with `data-action` attribute binding. Fully documented in `DESIGN_ARCHETYPE_PATTERNS.md` and `DESIGN_CONSTITUTION.md`.

### Checklist

- [x] Decision 1 resolved: `action-chip` → `btn-ghost` replacement documented.
- [x] Decision 2 resolved: Kanban BoardView subvariant promoted and documented.
- [ ] Shell strategy for `base.html` and `base_fullscreen.html` confirmed out of scope for this batch.
- [x] Canonical WorkspacePage wrapper contract locked: `page-wrap`, `page-header`, `page-title`, `page-subtitle`, `panel`, `panel-head`, `panel-title`, `panel-link` — no deviations introduced.
- [x] Canonical ExceptionPage wrapper contract locked: same shell + `badge-sm` + semantic badge variants + canonical filter toolbar.
- [x] `kpi-card` / `stat-card` classes confirmed in base CSS.
- [x] `badge-sm badge-green|blue|yellow|red|gray|purple` confirmed in base CSS.
- [x] `btn-primary-grad`, `btn-ghost`, `btn-soft-primary` confirmed in base CSS.
- [x] `chip` (active/inactive states) confirmed in base CSS — added to base.html during Slice 1.
- [x] `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td` confirmed in base CSS.
- [x] `empty-state` canonical class confirmed in base CSS.
- [x] `page-wrap`, `page-header`, `page-title`, `page-subtitle`, `page-actions` confirmed in base CSS.
- [x] No view-level changes in `contracts/views.py` or `contracts/views_domains/` required for any target page — confirmed template-only.
- [x] `theme/templates/patterns/archetype_wrappers_examples.html` is up-to-date and treated as reference during migration.
- [ ] All Batch 1 and Batch 2 migrations are confirmed visually stable (no regressions introduced).

---

## RECOMMENDED MIGRATION ORDER

Order is safest-first, then by value, with behavioral complexity last.

| Order | Template | Archetype | Lines | Risk | Dependency |
|---|---|---|---|---|---|
| 1 | notification_list.html | ExceptionPage | 55 | Low | None |
| 2 | deadline_list.html | ExceptionPage | 62 | Low-Medium | None |
| 3 | privacy_dashboard.html | WorkspacePage | 92 | Medium | kpi-card / stat-card confirmed |
| 4 | operations_dashboard.html | ExceptionPage | 88 | Low-Medium | None |
| 5 | dashboard.html | WorkspacePage | 466 | Medium | Batches 1–4 stable; action-chip audit |
| 6 | workflow_dashboard.html | WorkspacePage | 178 | Medium | dashboard.html migrated first |
| 7 | repository.html | WorkspacePage | 95 | Medium-High | Preserve drawer JS; repo-* class audit |
| 8 | legal_task_board.html | WorkspacePage | 122 | High | Kanban + AJAX behavior verified |

---

## PER-PAGE ANALYSIS AND MIGRATION SCOPE

---

### PAGE 1 — notification_list.html

**Template:** `theme/templates/contracts/notification_list.html`
**Archetype:** ExceptionPage
**Lines:** 55
**Risk score:** Low

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | ExceptionPage |
| Duplicated primitives | Custom pill-style filter tabs repeated per filter type; not using canonical `chip` primitive |
| Hardcoded utility stacks | Header built with raw `flex items-center justify-between mb-6`; no `page-wrap`/`page-header` |
| Layout drift | No `page-wrap` shell; raw div container |
| Spacing drift | `px-5 py-4` inline on rows; `mb-6` ad-hoc header gap |
| Table/detail inconsistency | N/A — list rows only |
| Status/action inconsistency | "Mark all as read" uses raw gray button `px-3 py-2 bg-gray-100`; "Mark read" inline `text-xs text-blue-600` link |
| Accessibility concerns | Icon-only notification type indicators lack explicit `aria-label`; "Mark read" button is a POST form button with no visible state feedback |
| Responsiveness concerns | Filter chips use `flex flex-wrap gap-2` — acceptable but not canonical; row layout may not stack cleanly at narrow widths |

#### What WILL Change

- Wrap page in `page-wrap` > `page-header` > `page-title` + `page-subtitle`.
- Replace raw "Mark all as read" button with canonical `btn-ghost` or `btn-soft-primary`.
- Replace custom pill filter tabs with canonical `chip chip-active` / `chip chip-inactive` primitives.
- Replace `bg-white rounded-xl border border-gray-200` container with `panel`.
- Replace `divide-y divide-gray-100` row separator with canonical `panel` row pattern.
- Replace notification row layout `flex items-start gap-4 px-5 py-4` with canonical `list-row`.
- Replace `w-8 h-8 bg-X-100 rounded-full` type icon badges with canonical icon badge class (or `badge-sm` where applicable).
- Replace empty state `px-5 py-12 text-center text-gray-400` with canonical `empty-state`.
- Add `aria-label` to icon-only notification type indicators.

#### What MUST NOT Change

- POST form behavior for "Mark all as read" and "Mark read" (no JS, POST method, CSRF — preserve exactly).
- Filter URL parameters (`?state=unread`, `?type=SYSTEM`, etc.) — no changes to query string logic.
- `notification.is_read` conditional row background — retain visual distinction for unread; use canonical unread-state token if available, else preserve `bg-blue-50` with a migration comment.
- `notification.notification_type` conditional icon — must preserve per-type icon rendering.
- No removal of the `{% for notification in notifications %}` loop or any context variable access.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`
- `btn-ghost` or `btn-soft-primary`
- `chip chip-active` / `chip chip-inactive`
- `panel`, `list-row`
- `badge-sm` or canonical icon-badge for notification type
- `empty-state`

#### Protected Behaviors

- POST form for mark-read/mark-all-read
- Filter tab URL routing
- Unread visual distinction

---

### PAGE 2 — deadline_list.html

**Template:** `theme/templates/contracts/deadline_list.html`
**Archetype:** ExceptionPage
**Lines:** 62
**Risk score:** Low-Medium

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | ExceptionPage — deadline overdue state is an exception-oriented operational signal |
| Duplicated primitives | Custom pill filter tabs (`px-3 py-1.5 rounded-lg`) not using canonical `chip` |
| Hardcoded utility stacks | Header `flex items-center justify-between mb-6` not using `page-wrap`/`page-header`; primary button `bg-blue-600` hardcoded |
| Layout drift | No `page-wrap` shell; no `panel` surface for table |
| Spacing drift | `mb-4`, `mb-6` ad-hoc spacing on header and filter bar |
| Table/detail inconsistency | Table wraps in `bg-white rounded-xl border border-gray-200 overflow-hidden` not `panel`; thead uses `bg-gray-50` not `tbl-head` |
| Status/action inconsistency | Priority chips are raw `px-2 py-1 rounded-full text-xs` with per-value bg/text; no `badge-sm`; "Complete" is `text-green-600` link, not button variant |
| Accessibility concerns | Action column contains a `<form>` inside `<td>` with a bare `<button type="submit">`; no `aria-label` on inline form buttons |
| Responsiveness concerns | Table does not have horizontal scroll wrapper; may truncate on narrow viewports |

#### What WILL Change

- Wrap page in `page-wrap` > `page-header` > `page-title` + `page-subtitle`.
- Replace `bg-blue-600` primary button with `btn-primary-grad`.
- Replace custom pill filter tabs with `chip chip-active` / `chip chip-inactive`.
- Replace table container with `panel overflow-hidden`.
- Replace `bg-gray-50` thead with `tbl-head`.
- Replace `hover:bg-gray-50` rows with `tbl-row`.
- Replace raw priority `px-2 py-1 rounded-full text-xs bg-X-100 text-X-800` with `badge-sm badge-red|badge-yellow|badge-gray` mapped per priority.
- Replace raw status display with `badge-sm badge-green|badge-red|badge-gray`.
- Add `aria-label` to inline form action buttons.
- Add horizontal scroll wrapper around table for mobile safety.

#### What MUST NOT Change

- POST form for "Complete" action with CSRF token — preserve exactly.
- `deadline.is_overdue` conditional row background (`bg-red-50`) — retain overdue row tinting; use semantic token if available.
- `?show=upcoming|overdue|completed|all` filter URL routing.
- `deadline.days_remaining` display logic.
- `deadline.matter` conditional sub-row.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`
- `btn-primary-grad`
- `chip chip-active` / `chip chip-inactive`
- `panel overflow-hidden`, `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`
- `badge-sm` + semantic badge variants

#### Protected Behaviors

- POST form for complete action
- Filter tab URL routing
- Overdue row background tinting (exception-state signal)

---

### PAGE 3 — privacy_dashboard.html

**Template:** `theme/templates/contracts/privacy_dashboard.html`
**Archetype:** WorkspacePage
**Lines:** 92
**Risk score:** Medium

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | WorkspacePage — policy/compliance multi-panel dashboard |
| Duplicated primitives | Four KPI cards use raw `bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow` instead of `kpi-card` or `stat-card` |
| Hardcoded utility stacks | Entire page built on raw Tailwind; no `page-wrap`, no canonical header, no `panel` |
| Layout drift | Header is raw `mb-6` div; no `page-header` wrapper; action link uses raw gray utility button |
| Spacing drift | `mb-8` on KPI grid, `mb-8` on second grid — ad-hoc vertical rhythm not matching 24-spacing cadence |
| Table/detail inconsistency | DSAR table section uses raw container (`bg-white rounded-xl border border-gray-200 overflow-hidden`), raw thead (`bg-gray-50`), raw rows |
| Status/action inconsistency | Status badges in DSAR table use `px-2 py-1 text-xs rounded-full` with per-value bg/text — not `badge-sm`; conditional `text-red-500 font-medium` for overdue not using semantic badge |
| Accessibility concerns | KPI card links have no `aria-describedby` for the metric value context; icon SVGs have no `aria-hidden="true"` |
| Responsiveness concerns | `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4` uses raw responsive breakpoint utilities not canonical grid helper |

#### What WILL Change

- Wrap page in `page-wrap` > `page-header` > `page-title` + `page-subtitle`.
- Replace "Export evidence CSV" with canonical `btn-ghost` or `btn-soft-primary`.
- Replace raw KPI grid `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8` with `dash-grid dash-grid-4`.
- Replace raw `bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow` KPI cards with `kpi-card` or `stat-card`.
- Replace second grid `grid grid-cols-1 md:grid-cols-3 gap-4 mb-8` with `dash-grid dash-grid-3`.
- Replace smaller summary cards with `stat-card`.
- Replace DSAR table container with `panel overflow-hidden`.
- Replace raw panel header (`px-5 py-3 border-b border-gray-100 h2`) with `panel-head` > `panel-title`.
- Replace `bg-gray-50` thead with `tbl-head`, `hover:bg-gray-50` rows with `tbl-row`.
- Replace raw status pills with `badge-sm` + semantic badge variants.
- Add `aria-hidden="true"` to decorative icon SVGs.

#### What MUST NOT Change

- All URL routing for KPI card links — preserve `href` attributes exactly.
- `legal_hold_count > 0` conditional red highlighting — preserve as a semantic indicator using `badge-red` or canonical alert token.
- `dsar_overdue > 0` conditional text — preserve intent; map to `badge-sm badge-red`.
- `{% if recent_dsars %}` conditional block — preserve exactly; no change to context variable access.
- No changes to view context variables.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`
- `btn-ghost` or `btn-soft-primary`
- `dash-grid dash-grid-4` / `dash-grid dash-grid-3`
- `kpi-card` / `stat-card`
- `panel overflow-hidden`, `panel-head`, `panel-title`
- `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`
- `badge-sm` + semantic badge variants

#### Protected Behaviors

- KPI card navigation links
- Conditional urgency indicators (overdue, legal holds)
- Conditional DSAR table presence

---

### PAGE 4 — operations_dashboard.html

**Template:** `theme/templates/contracts/operations_dashboard.html`
**Archetype:** ExceptionPage
**Lines:** 88
**Risk score:** Low-Medium

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | ExceptionPage — job health and exception-like operational states |
| Duplicated primitives | Four KPI cards use raw `rounded-xl border border-gray-200 bg-white p-5` — not `kpi-card` |
| Hardcoded utility stacks | Entire page built on raw Tailwind under `max-w-6xl` wrapper (not `page-wrap`) |
| Layout drift | No `page-wrap`; uses `max-w-6xl` constraint div; back button is raw utility not `btn-ghost` |
| Spacing drift | `mb-6` ad-hoc gaps throughout; 2-col grid uses raw `grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6` |
| Table/detail inconsistency | Job list is custom `space-y-3` div stack with `rounded-lg border border-gray-100 p-4` items — no `panel`/`tbl-*` |
| Status/action inconsistency | Job status uses `text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700` — no `badge-sm` |
| Accessibility concerns | `<pre>` code block has no ARIA role; job list items have no semantic role for screen readers |
| Responsiveness concerns | KPI grid uses raw `grid-cols-1 md:grid-cols-2 xl:grid-cols-4` — no canonical helper |

#### What WILL Change

- Replace `max-w-6xl` wrapper with `page-wrap` > `page-header` > `page-title` + `page-subtitle`.
- Replace back button `px-4 py-2 rounded-lg border border-gray-300 text-sm` with `btn-ghost`.
- Replace raw KPI grid with `dash-grid dash-grid-4`.
- Replace raw `rounded-xl border border-gray-200 bg-white p-5` KPI cards with `kpi-card` or `stat-card`.
- Replace inner 2-col grid with `dash-grid dash-grid-2`.
- Replace sub-grid job count panels `rounded-lg bg-gray-50 p-4` with canonical `stat-card` or panel inner sections.
- Replace job list items `rounded-lg border border-gray-100 p-4` with `panel` + `list-row` pattern.
- Replace raw job status chip with `badge-sm badge-gray|badge-green|badge-red`.
- Add `role="region"` and `aria-label` to `<pre>` drill command block.

#### What MUST NOT Change

- No changes to `scheduler`, `database`, `alerts`, `request_metrics`, `job_counts`, `drill_state`, `recent_jobs` context access.
- `<pre>` command block content — preserve exactly.
- Job `error_message` conditional rendering.
- No JS present — none to preserve.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`
- `btn-ghost`
- `dash-grid dash-grid-4`, `dash-grid dash-grid-2`
- `kpi-card` / `stat-card`
- `panel`, `list-row`
- `badge-sm` + semantic badge variants

#### Protected Behaviors

- No interactive behavior on this page
- Drill command pre block

---

### PAGE 5 — dashboard.html

**Template:** `theme/templates/dashboard.html`
**Archetype:** WorkspacePage
**Lines:** 466
**Risk score:** Medium

> Note: This is the highest-traffic page. It is already partially migrated with canonical primitives but retains several non-canonical patterns. This is the most visible page in the product — changes must be surgical.

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | WorkspacePage — primary multi-panel operating surface |
| Duplicated primitives | `action-chip` used for page-level CTAs instead of canonical button variants; these are custom classes not in the canonical button system |
| Hardcoded utility stacks | Alert banner section uses raw `flex gap-3 mb-6 flex-wrap` wrapper — not `panel` nor canonical alert primitive; `alert-banner alert-banner-red alert-link-fill` are custom and not in the canonical primitive list |
| Layout drift | Page header action area uses `action-chip` — not `btn-primary-grad`/`btn-ghost`; `alert-banner` styles are custom and outside the canonical badge/alert system |
| Spacing drift | Many panels already canonical but `flex gap-3 mb-6` around alert banners uses raw utility not canonical spacing token |
| Table/detail inconsistency | Already using canonical `list-row`, `item-row`, `item-title`, `item-meta`, `panel`, `panel-head` |
| Status/action inconsistency | `audit-action` class is not in the canonical badge set; recommendation section uses `text-[12px]` and `text-[13px]` — raw arbitrary text sizes violating typography rules |
| Accessibility concerns | SVG icons in `action-chip` buttons have no `aria-hidden`; `sr-only` spans present on some but not all chip actions |
| Responsiveness concerns | Dashboard is mostly responsive but `progress-bar-bg/fill` uses JS-injected width — preserved but noted |

#### What WILL Change

- Replace all 3 `action-chip` instances in `.page-actions` with `btn-ghost`. Decision resolved: `action-chip` is RETIRED — see `DESIGN_CONSTITUTION.md` section 5.
- After `dashboard.html` migration is validated: remove `.action-chip` CSS block from `base.html` (lines 493–500).
- Replace raw `flex gap-3 mb-6 flex-wrap` alert banner wrapper with canonical panel alert band; `alert-banner`, `alert-banner-red`, `alert-banner-yellow`, `alert-link-fill` are defined in `base.html` — these are considered semi-canonical and are preserved.
- Replace `audit-action` badge class on governance activity log with `badge-sm badge-green|badge-blue|badge-red|badge-gray`.
- Replace `text-[12px]` and `text-[13px]` arbitrary font sizes with `item-meta` (11px metadata) or `text-desc-sm` (13px) canonical text classes.
- Ensure all SVG icons inside actionable controls have `aria-hidden="true"`.
- Ensure all icon-only actions that lack visible labels have `aria-label`.

#### What MUST NOT Change

- All `page-wrap`, `page-header`, `page-title`, `page-subtitle`, `panel`, `panel-head`, `panel-title`, `panel-link`, `badge-sm`, `kpi-card`, `dash-grid`, `list-row`, `item-row`, `item-title`, `item-meta` canonical usage — already correct, do not touch.
- `progress-bar-fill` JS behavior — preserve `data-width` attribute injection exactly.
- `kpi-card`, `kpi-glow`, `kpi-icon`, `kpi-value`, `kpi-label`, `kpi-sub` — these appear canonical for the KPI strip; do not change.
- `status-dot` conditional color logic — preserve per-status dot class mapping.
- `empty-state` blocks — already canonical; preserve.
- Dutch-language strings (`Welkom terug`, `Geen urgente opvolging`, etc.) — preserve exactly; these are product copy.
- All URL routing and context variable access.
- `alert-banner alert-banner-red alert-link-fill` classes — if confirmed canonical, preserve; if not, flag for decision but do not change in this pass.

#### Pre-Migration Decision — RESOLVED

- `action-chip` → **RETIRED**. Replace with `btn-ghost`. (3 instances in `.page-actions`.) Remove CSS after migration.
- `alert-banner*` → **SEMI-CANONICAL** (defined in `base.html`, token-backed, used only in `dashboard.html`). Preserved as-is for this batch.

#### Components / Primitives to Standardize

- `btn-ghost` (replacing `action-chip`, 3 instances)
- `badge-sm` + semantic variants (replacing `audit-action`)
- `item-meta` or `text-desc-sm` (replacing `text-[12px]` / `text-[13px]`)

#### Protected Behaviors

- All KPI JS (progress bar width injection)
- All panel navigation links
- All empty-state fallbacks
- Status dot logic

---

### PAGE 6 — workflow_dashboard.html

**Template:** `theme/templates/contracts/workflow_dashboard.html`
**Archetype:** WorkspacePage
**Lines:** 178
**Risk score:** Medium

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | WorkspacePage — operational orchestration dashboard with filters and workflow states |
| Duplicated primitives | Every structural element uses raw Tailwind utilities — no canonical primitive is present |
| Hardcoded utility stacks | Header: raw `flex items-center justify-between`; primary CTA: `bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-md` (hardcoded teal violates token rules); secondary buttons: raw gray utility |
| Layout drift | No `page-wrap`, no `page-header`, no `panel`; entire page is raw `space-y-6` stack |
| Spacing drift | `space-y-6` root wrapper, `p-6` filter grid, `px-6 py-3` table headers — all ad-hoc |
| Table/detail inconsistency | Table: `bg-white rounded-lg border border-gray-200 overflow-hidden` not `panel`; `bg-gray-50` thead not `tbl-head`; `hover:bg-gray-50` rows not `tbl-row` |
| Status/action inconsistency | Stage badges: long raw utility string `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium` with per-stage bg/text — not `badge-sm`; status dots: raw `w-3 h-3 rounded-full` inline — not `status-dot` |
| Accessibility concerns | Filter toggle button uses `onclick="toggleFilters()"` (inline handler — Constitution violation); "Start workflow" link has no `aria-label`; filter panel has no ARIA disclosure role |
| Responsiveness concerns | Filter grid `grid grid-cols-1 md:grid-cols-4 gap-4` is raw; pagination `flex items-center justify-between` raw |

#### What WILL Change

- Wrap page in `page-wrap` > `page-header` > `page-title` + `page-subtitle`.
- Replace `bg-teal-600` primary CTA with `btn-primary-grad`.
- Replace raw secondary/tertiary buttons with `btn-ghost`.
- Replace filter toggle `onclick` attribute with canonical filter panel disclosure (data-attribute driven or CSS toggle via canonical wrapper, no inline JS).
- Replace filter container with canonical filter toolbar structure.
- Replace `input-field` labels `block text-sm font-medium text-gray-700 mb-1` with canonical form label primitive.
- Replace table container with `panel overflow-hidden`.
- Replace `bg-gray-50` thead with `tbl-head`, table headers with `tbl-th`.
- Replace `hover:bg-gray-50` rows with `tbl-row`.
- Replace raw stage badge string with `badge-sm` + mapped semantic badge variant per stage.
- Replace raw `w-3 h-3 rounded-full` status dot with `status-dot`.
- Replace progress bar `w-full bg-gray-200 rounded-full h-2 mr-2` with canonical progress bar class or preserve `progress-bar-bg/fill` pattern from dashboard.
- Replace pagination with canonical pagination pattern.
- Remove `function toggleFilters()` inline JS; replace with declarative toggle pattern (data-attribute or CSS-only hidden toggle).

#### What MUST NOT Change

- URL routing: `workflow_create`, `workflow_template_list`, `workflow_detail pk`.
- Filter GET parameter names: `search`, `status`, `contract_type`.
- `is_paginated`, `page_obj` pagination context.
- `workflow.progress_percentage` value — preserve `data-width` attribute injection for progress bar JS.
- `workflow.contract.title`, `workflow.current_stage`, all context variable access.
- Workflow status conditional class mapping — preserve logic, replace class output only.

#### Pre-Migration Decision Required

- Confirm canonical toggle pattern for filter panel visibility (data-attribute vs CSS toggle) before writing any JS.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`
- `btn-primary-grad`, `btn-ghost`
- `panel overflow-hidden`, `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`
- `badge-sm` + semantic badge variants
- `status-dot`
- Canonical filter toolbar
- Canonical pagination

#### Protected Behaviors

- Progress bar JS (`data-width` attribute pattern)
- Filter GET parameters
- Pagination context

---

### PAGE 7 — repository.html

**Template:** `theme/templates/contracts/repository.html`
**Archetype:** WorkspacePage
**Lines:** 95
**Risk score:** Medium-High

> This page has a custom JavaScript controller (`cms-aegis-repository.js`) that drives live search, sorting, pagination, drawer preview, saved views, bulk actions, and status filtering. The JS controller MUST NOT be touched. Template changes must preserve all `id` attributes, `data-*` attributes, and custom class names consumed by the JS.

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | WorkspacePage — repository browser with live search, drawer, and bulk ops |
| Duplicated primitives | KPI row uses `rounded-xl p-5 border card-surface` (mixed) not `kpi-card`; no `dash-grid` |
| Hardcoded utility stacks | KPI card grid is raw `grid grid-cols-4 gap-4 mb-6`; saved-views section uses raw `rounded-xl border p-4 mb-4 card-surface`; filter area uses raw `flex items-center gap-3 mb-4 flex-wrap` |
| Layout drift | Header is raw `flex items-center justify-between mb-6` — no `page-wrap`/`page-header` |
| Spacing drift | `mb-6` gaps throughout; `mb-4` between filter rows — ad-hoc |
| Table/detail inconsistency | Table outer is `rounded-xl border overflow-hidden card-surface` — mixed; `tbl-head` is already used for thead (partially canonical); th cells have inline `px-5 py-3 text-xs font-semibold uppercase tracking-wide c-muted` — not `tbl-th` |
| Status/action inconsistency | `stat-card-amber` is semi-canonical but rest of KPI cards use `card-surface` not `kpi-card`; `btn-ghost-secondary` is used — confirm canonical |
| Accessibility concerns | `onclick="window.cmsAegisRepository.saveCurrentView()"` is an inline handler (Constitution violation) — must be replaced with `data-action="save-view"` consumed by JS; `#select-all` checkbox has no `aria-label`; bulk action bar has no ARIA live region for selection count |
| Responsiveness concerns | Filter row uses `flex-1 min-w-0` on search input — acceptable; KPI grid `grid-cols-4` has no breakpoint override — may collapse badly on tablet |

#### What WILL Change

- Wrap page in `page-wrap` > `page-header` > `page-title` + `page-subtitle` with `page-actions`.
- Replace raw KPI grid with `dash-grid dash-grid-4` (confirm breakpoint behavior).
- Replace raw `rounded-xl p-5 border card-surface` KPI cards with `kpi-card` or `stat-card`.
- Replace `stat-card-amber` with `kpi-card` using canonical amber token.
- Replace saved-views container `rounded-xl border p-4 mb-4 card-surface` with `panel`.
- Replace raw filter toolbar with canonical filter toolbar structure.
- Replace table outer `rounded-xl border overflow-hidden card-surface` with `panel overflow-hidden`.
- Replace inline `px-5 py-3 text-xs font-semibold uppercase tracking-wide c-muted` on th cells with `tbl-th`.
- Replace `onclick="window.cmsAegisRepository.saveCurrentView()"` with `data-action="save-view"` — update `cms-aegis-repository.js` to bind via `querySelectorAll('[data-action="save-view"]')` instead of inline handler.
- Add `aria-label="Select all"` to `#select-all` checkbox.
- Add `aria-live="polite"` to `#selected-count` bulk action count.

#### What MUST NOT Change

- `id="search-input"`, `id="sort-select"`, `id="contracts-table"`, `id="contracts-tbody"`, `id="pagination-container"`, `id="details-drawer"`, `id="saved-views"`, `id="filter-chips"`, `id="bulk-action-bar"`, `id="selected-count"`, `id="select-all"`, `id="repo-bulk-status"`, `id="repo-bulk-assign"`, `id="repo-bulk-export"` — ALL `id` attributes consumed by `cms-aegis-repository.js` must be preserved exactly.
- `data-status-filter` attributes on filter buttons — preserve exactly.
- `repo-mini-btn`, `repo-status-filter`, `repo-bulk-bar`, `repo-drawer` custom class names — consumed by JS; must remain.
- `{% static 'js/cms-aegis-repository.js' %}` script tag — preserve exactly.
- `btn-primary-grad` on Upload Document — already canonical; preserve.
- `btn-ghost-secondary` on Templates link — preserve if canonical; confirm before changing.

#### JS Update Required (Scoped)

The inline `onclick` handler removal requires one targeted update to `cms-aegis-repository.js`:
- Find the "Save current view" button event binding.
- Change from `onclick` attribute to `addEventListener` on `[data-action="save-view"]`.
- This is the ONLY JS change permitted in this migration.

#### Components / Primitives to Standardize

- `page-wrap`, `page-header`, `page-title`, `page-subtitle`, `page-actions`
- `dash-grid dash-grid-4`
- `kpi-card` / `stat-card`
- `panel overflow-hidden`, `tbl-th`
- Filter toolbar structure

#### Protected Behaviors

- Live search, sort, pagination driven by `cms-aegis-repository.js`
- Drawer preview behavior
- Saved views
- Bulk action bar
- Status filter buttons

---

### PAGE 8 — legal_task_board.html

**Template:** `theme/templates/contracts/legal_task_board.html`
**Archetype:** WorkspacePage
**Lines:** 122
**Risk score:** High

> This is the highest-risk page in Batch 3. The Kanban board now has a canonical pattern: WorkspacePage/BoardView subvariant, defined in `DESIGN_ARCHETYPE_PATTERNS.md` and `DESIGN_CONSTITUTION.md`. Use `board-track`, `board-col`, `board-col-head`, `board-card` primitives (to be added to `base.html` during this migration). The `updateTaskStatus()` AJAX function drives task state transitions. Any template change that breaks card `data-task-id` attributes, column structure, or filter targeting will cause silent JS failures. Migrate last.

#### Current Inconsistencies

| Category | Finding |
|---|---|
| Archetype | WorkspacePage — Kanban task board with filter and AJAX status updates |
| Duplicated primitives | Task card priority badges use raw `inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-X-100 text-X-700` — not `badge-sm` |
| Hardcoded utility stacks | Filter bar `bg-white rounded-lg border border-gray-200 p-4` not `panel`; Kanban columns `w-80 bg-gray-100 rounded-lg p-4 flex-shrink-0` not any canonical primitive |
| Layout drift | Uses `{% block page_title %}` and `{% block page_actions %}` blocks (canonical shell blocks); board body still in `space-y-6` raw wrapper |
| Spacing drift | `space-x-4 overflow-x-auto p-2` on Kanban track — custom; column `p-4` spacing ad-hoc |
| Table/detail inconsistency | N/A — Kanban board, not a table |
| Status/action inconsistency | "Complete" button is `onclick="updateTaskStatus({{ task.id }}, 'DONE')"` (inline handler — Constitution violation); "Edit" link is `text-blue-600 hover:text-blue-800 text-xs` not canonical link style |
| Accessibility concerns | `onclick` inline handler; task cards are `div` elements — not keyboard accessible; column count badges `bg-gray-200 text-gray-700 text-xs px-2 py-1 rounded-full` not canonical `badge-sm`; no ARIA roles on Kanban column containers |
| Responsiveness concerns | Kanban track `flex space-x-4 overflow-x-auto` is the correct horizontal scroll pattern; column `w-80` is fixed width; mobile users must scroll — acceptable but should be preserved |

#### What WILL Change

- Retain `{% block page_title %}` and `{% block page_actions %}` — already canonical.
- Add `board-*` CSS to `base.html` before this migration: `.board-track`, `.board-col`, `.board-col-head`, `.board-card` per the definitions in `DESIGN_CONSTITUTION.md` section 5.
- Replace filter bar `bg-white rounded-lg border border-gray-200 p-4` with `panel`.
- `chip chip-inactive` on priority select — `chip` IS canonical (defined in `styles.css` and used in `cms-aegis-repository.js`). Keep as-is.
- Replace Kanban track `div.flex.space-x-4.overflow-x-auto.p-2` with `div.board-track`.
- Replace each column `div.w-80.bg-gray-100.rounded-lg.p-4.flex-shrink-0` with `div.board-col` (retains `data-status` attribute).
- Replace column header row with `div.board-col-head`: title `<h3>` + `badge-sm badge-gray` count.
- Replace each task card `div.bg-white.rounded-lg.p-4.shadow-sm...` with `div.board-card` (retains `data-task-id` and `data-priority` attributes).
- Replace task card priority badges `inline-flex...bg-X-100 text-X-700` with `badge-sm badge-red|badge-yellow|badge-green`.
- Replace "Edit" link `text-blue-600 hover:text-blue-800 text-xs` with `c-link` class.
- Replace `onclick="updateTaskStatus({{ task.id }}, 'DONE')"` with `data-action="complete-task"` attribute — `data-task-id` already present on the card. Update scoped `<script>` to bind via `querySelectorAll('[data-action="complete-task"]').forEach(btn => btn.addEventListener('click', ...))`.
- Add `role="region"` and `aria-label="[Status column name]"` to each `.board-col`.
- Add `role="article"` to each `.board-card`.

#### What MUST NOT Change

- `data-task-id="{{ task.id }}"` attribute — must be preserved for JS binding.
- `data-priority="{{ task.priority }}"` attribute — must be preserved for filter JS.
- `data-status="{{ tasks.0.status }}"` attribute on column containers — must be preserved.
- `id="priority-filter"` and `id="task-search"` — must be preserved for filter JS.
- AJAX `fetch()` call to `/contracts/legal-tasks/${taskId}/update-status/` — preserve exactly (URL, method, headers, body, CSRF handling).
- Filter JS functions `filterTasks()` — preserve; only move inline handlers to `addEventListener`.
- Kanban column layout (`flex space-x-4 overflow-x-auto p-2`, `w-80 flex-shrink-0`) — preserve for scroll behavior.
- `btn-primary shadow-sm` on "New Task" in `{% block page_actions %}` — confirm canonical.

#### Pre-Migration Decision — RESOLVED

- Kanban pattern: **PROMOTED** to WorkspacePage/BoardView subvariant. Documented in `DESIGN_ARCHETYPE_PATTERNS.md` and `DESIGN_CONSTITUTION.md`. Use `board-*` primitives.
- Column background: replace `bg-gray-100 rounded-lg` with `board-col` (uses `var(--surface)` token — equivalent, but now token-backed and theme-aware).

#### Components / Primitives to Standardize

- `panel` (filter bar)
- `badge-sm` + semantic badge variants (task priority, column counts)
- `c-link` (edit link)
- ARIA roles on board structure

#### Protected Behaviors

- AJAX task status update (full fetch cycle)
- Filter JS (priority + search)
- `data-task-id`, `data-priority`, `data-status` attributes
- Kanban scroll layout

---

## MIGRATION ORDER — DEPENDENCY GRAPH

```
notification_list.html     ← no deps, safest start
      ↓
deadline_list.html         ← no deps, ExceptionPage establishes pattern
      ↓
privacy_dashboard.html     ← kpi-card/stat-card confirmed from earlier pages
      ↓
operations_dashboard.html  ← kpi-card/stat-card confirmed; no JS
      ↓
dashboard.html             ← highest traffic; action-chip decision required first
      ↓
workflow_dashboard.html    ← full primitive replacement; no JS complexity
      ↓
repository.html            ← requires JS audit; cms-aegis-repository.js scoped update
      ↓
legal_task_board.html      ← highest risk; all earlier patterns validated
```

---

## VALIDATION CHECKLIST (per page, run before PR merges)

### Visual Validation

- [ ] Page renders without broken layout at default desktop viewport (1280px).
- [ ] Page header matches canonical `page-header` spacing and alignment.
- [ ] KPI cards (if present) align to `dash-grid` rhythm.
- [ ] Panel surfaces render with correct border/radius/shadow per canonical token.
- [ ] All badges use `badge-sm` with semantic color variants.
- [ ] No raw hardcoded hex or `bg-gray-*` / `text-gray-*` utility strings remain in migrated sections.
- [ ] Before/after screenshot captured and attached to PR.

### Interaction Validation

- [ ] All links navigate to correct routes.
- [ ] All form POST actions complete correctly (confirm CSRF token present).
- [ ] All filter parameters submitted and preserved in URL.
- [ ] Filter tabs reflect active state correctly.
- [ ] Empty states render when no data is present.
- [ ] For repository.html: live search, sort, drawer preview, saved views, bulk actions all function.
- [ ] For legal_task_board.html: Kanban filter works; AJAX status update completes; page reloads correctly after status change.
- [ ] For workflow_dashboard.html: filter panel toggle works without inline JS.

### Responsive Validation

- [ ] Layout renders correctly at 768px (tablet) viewport.
- [ ] Layout renders correctly at 375px (mobile) viewport.
- [ ] Tables have horizontal scroll wrapper on narrow viewports.
- [ ] Kanban board scroll is preserved at mobile viewport.
- [ ] Filter chips wrap correctly at narrow viewports.

### Accessibility Validation

- [ ] All interactive controls are keyboard reachable (Tab order correct).
- [ ] All buttons and links have visible focus state.
- [ ] All icon-only actions have `aria-label`.
- [ ] All form inputs have associated labels.
- [ ] All decorative SVG icons have `aria-hidden="true"`.
- [ ] WCAG AA contrast passes for all text and badge combinations (spot check).
- [ ] No inline `onclick`/`onchange`/`onmouseover` attributes remain in migrated template.
- [ ] Screen reader announces notification count / selection count where applicable.

### Regression-Sensitive Areas

- [ ] `dashboard.html`: KPI values, work queue, contract list, audit log — all data still rendering.
- [ ] `repository.html`: `cms-aegis-repository.js` loads without console errors after template changes.
- [ ] `legal_task_board.html`: task AJAX update completes without 400/500 error.
- [ ] `deadline_list.html`: deadline complete form POST succeeds.
- [ ] `notification_list.html`: mark-read POST form succeeds.
- [ ] `workflow_dashboard.html`: filters apply and table refreshes correctly.
- [ ] `privacy_dashboard.html`: conditional DSAR table renders when `recent_dsars` has items.
- [ ] `operations_dashboard.html`: drill state and job list render correctly.

---

## RISK SCORES

| Template | Risk | Reason |
|---|---|---|
| notification_list.html | **Low** | 55 lines; no JS; simple list pattern; POST form is simple and self-contained |
| deadline_list.html | **Low-Medium** | 62 lines; no JS; table pattern straightforward; inline POST form in action cell requires care |
| privacy_dashboard.html | **Medium** | 92 lines; no JS; fully raw utility stack requires complete primitive swap; conditionals must be preserved |
| operations_dashboard.html | **Low-Medium** | 88 lines; no JS; ExceptionPage pattern; `pre` block and drill state are sensitive display areas |
| dashboard.html | **Medium** | 466 lines; highest-traffic page; partially canonical; `action-chip` audit needed; progress bar JS must survive; any visual regression immediately user-facing |
| workflow_dashboard.html | **Medium** | 178 lines; completely raw Tailwind; full primitive replacement effort; filter toggle JS must be replaced with non-inline pattern |
| repository.html | **Medium-High** | Custom JS controller; `id` and `data-*` attributes must survive; one targeted JS change required; `repo-*` custom class audit needed |
| legal_task_board.html | **High** | AJAX status update behavior; inline event handler removal requires JS refactor; Kanban layout is a unique non-canonical structure; keyboard accessibility gap |

---

## EXPECTED UX IMPACT IF BATCH 3 SUCCEEDS

If all 8 pages are migrated without regression:

1. **Visual coherence**: The top 5 highest-traffic workspace and operational surfaces (dashboard, workflow, repository, privacy, legal task board) will share a single visual language — same spacing rhythm, same panel surfaces, same badge semantics.
2. **Reduced cognitive load**: Users navigating across these surfaces will experience predictable headers, consistent KPI card formats, and uniform status badge colors instead of page-by-page inconsistency.
3. **Accessibility baseline**: Inline event handlers eliminated; ARIA roles added to Kanban and notification structures; keyboard navigation improved across batch.
4. **Developer confidence**: With 20 WorkspacePage templates, 5 migrated in Batch 3 represents 25% of WorkspacePage coverage — a meaningful anchor for the remaining 15.
5. **Technical debt reduction**: Hardcoded teal/blue/gray utility stacks replaced by token-backed canonical primitives — future token updates will cascade correctly to these pages.
6. **Risk exposure if batch fails**: A regression on `dashboard.html` or `repository.html` is immediately user-visible. This is why migration order (safest-first) and per-PR validation are mandatory.

---

## BATCH 3 SCOPE ESTIMATES

| Metric | Value |
|---|---|
| Templates in scope | 8 |
| Total template lines | 1,158 |
| WorkspacePage templates | 5 |
| ExceptionPage templates | 3 |
| Templates with zero canonical primitives | 4 (workflow_dashboard, privacy_dashboard, operations_dashboard, deadline_list) |
| Templates partially canonical | 3 (dashboard, repository, notification_list) |
| Templates with canonical header blocks only | 1 (legal_task_board) |
| Templates requiring JS changes | 2 (repository, legal_task_board) |
| Templates requiring pre-migration decisions | 2 (dashboard action-chip audit; legal_task_board Kanban subvariant decision) |
| Estimated PRs | 8 (one per template) |
| Estimated migration difficulty | Medium overall; High for legal_task_board |
| Highest-risk page | legal_task_board.html |
| Safest page | notification_list.html |
| Recommended first page | notification_list.html |
| Recommended last page | legal_task_board.html |

---

## BATCH 3 PRE-MIGRATION DECISIONS — RESOLVED

**Status: CLEARED TO BEGIN**
Date resolved: 2026-05-18
Both pre-migration blockers identified in this plan have been formally decided and documented.

### Decision 1 — `action-chip` disposal

| Field | Value |
|---|---|
| Verdict | RETIRED |
| Affects | `dashboard.html` only (3 instances in `.page-actions`) |
| Canonical replacement | `btn-ghost` |
| CSS cleanup | Remove `.action-chip` block from `base.html` after `dashboard.html` migration is validated |
| Constitution update | Section 5 — Retired button-adjacent classes |
| Rationale | Single-template usage, missing 3 required states (focus/active/disabled), `btn-ghost` already covers the semantic need |

**dashboard.html before/after (action-chip → btn-ghost):**
```html
<!-- BEFORE -->
<a href="{% url 'contracts:contract_create' %}" class="action-chip">
    <svg class="w-4 h-4">...</svg>
    New Contract
    <span class="sr-only">New Contract</span>
</a>

<!-- AFTER -->
<a href="{% url 'contracts:contract_create' %}" class="btn-ghost">
    <svg aria-hidden="true" class="w-4 h-4">...</svg>
    New Contract
</a>
```
Note: remove redundant `sr-only` span when visible label text already provides the accessible name.

---

### Decision 2 — Kanban / BoardView governance

| Field | Value |
|---|---|
| Verdict | PROMOTED to WorkspacePage/BoardView subvariant |
| Affects | `legal_task_board.html` (only Kanban surface in codebase) |
| New canonical classes | `board-track`, `board-col`, `board-col-head`, `board-card` |
| CSS location | Add to `base.html` during `legal_task_board.html` migration PR |
| Constitution update | Section 5 — Board/Kanban surfaces |
| Archetype Patterns update | WorkspacePage/BoardView Subvariant section added |
| Rationale | Pattern is clean, token-backed, reusable in CLM domain (stage boards, approval pipelines); defining it prevents ad-hoc drift on future board surfaces |

**Board primitive CSS (add to `base.html` during legal_task_board migration):**
```css
.board-track { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px; }
.board-col   { width: 320px; flex-shrink: 0; background: var(--surface); border-radius: 10px; padding: 16px; }
.board-col-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.board-card  { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 16px; transition: box-shadow 0.15s; }
.board-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
```

---

### Batch 3 migration is now cleared to begin

- `notification_list.html` — first. Safest. Pure ExceptionPage. No JS.
- `deadline_list.html` — second.
- `privacy_dashboard.html` — third.
- `operations_dashboard.html` — fourth.
- `workflow_dashboard.html` — fifth.
- `dashboard.html` — sixth. Apply action-chip → btn-ghost replacement. Validate. Then remove `.action-chip` from `base.html`.
- `repository.html` — seventh.
- `legal_task_board.html` — last. Add `board-*` CSS to `base.html`. Apply BoardView pattern. Update JS handlers.


---

## Slice 2 — Step 1 Complete: dashboard.html (2026-05-18)

**Template:** `theme/templates/dashboard.html`
**Archetype:** WorkspacePage
**Status:** ✅ Migrated

### Changes Applied

| Change | Detail |
|---|---|
| `action-chip` × 3 → `btn-ghost` | All 3 page-actions CTAs replaced with `inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border btn-ghost` |
| Redundant `sr-only` removed | `<span class="sr-only">New Contract</span>` removed from "New Contract" action (visible text already provides accessible name) |
| `audit-action` → `badge-sm` | Governance activity log action label replaced with canonical `badge-sm` + semantic variant |
| `aria-hidden="true"` added | All decorative SVGs throughout the template: alert banner icons, KPI icons, panel-link chevrons, empty-state illustrations, nav-row icons and chevrons |
| `.action-chip` CSS removed from `base.html` | 3-line block + comment removed after dashboard.html validation passed |

### What Was NOT Changed (Preserved)

- `alert-banner`, `alert-banner-red`, `alert-banner-yellow`, `alert-link-fill` — semi-canonical, defined in base.html, token-backed; preserved
- `text-[12px]`, `text-[13px]` arbitrary sizes in workflow recommendation section — not replaced (no canonical text-desc-sm class exists; deferred)
- All KPI primitives (`kpi-card`, `kpi-glow`, `kpi-icon`, `kpi-value`, `kpi-label`, `kpi-sub`)
- Progress bar JS behavior (`data-width` injection)
- All context variables, URL routing, Dutch-language strings
- All `sr-only` spans that provide supplemental (non-duplicate) accessible context

### Validation

- `manage.py check`: 0 issues
- Template parse: OK
- `manage.py test contracts`: 3/3 passed
- Inline handler/style scan: 0 violations
- `action-chip` scan in all templates: 0 remaining references

### Slice 2 Remaining Steps

| Template | Status |
|---|---|
| `workflow_dashboard.html` | Not started — can begin now |
| `repository.html` | Not started |
| `legal_task_board.html` | Not started — requires `board-*` CSS added to base.html first |
