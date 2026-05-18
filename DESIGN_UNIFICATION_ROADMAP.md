# DESIGN UNIFICATION ROADMAP - CMS Aegis

Date: 2026-05-18
Horizon: 5 phases
Goal: unify UI into one enterprise-grade product language while reducing implementation drift

## Phase 2 Progress Log

### 2026-05-18 - Classification Pass (Complete Archetype Mapping)

Scope completed:

- Full archetype classification and planning pass across all templates and major UI routes.
- No template migration changes performed in this pass.

Artifacts produced:

- `DESIGN_ARCHETYPE_MAP.md` (complete mapping matrix + route map + priority list)

Coverage and counts:

- Templates scanned: 123
- UI routes classified: 190
- Recommended archetype distribution:
  - QueuePage: 28
  - WorkspacePage: 20
  - CommandPage: 32
  - NetworkPage: 16
  - ExceptionPage: 19
  - Unknown / Needs decision: 8

Top-priority migration candidates identified:

- `theme/templates/dashboard.html`
- `theme/templates/contracts/workflow_dashboard.html`
- `theme/templates/contracts/repository.html`
- `theme/templates/contracts/privacy_dashboard.html`
- `theme/templates/contracts/operations_dashboard.html`
- `theme/templates/contracts/legal_task_board.html`
- `theme/templates/contracts/deadline_list.html`
- `theme/templates/contracts/notification_list.html`

Decisions deferred (not migrated):

- Shell strategy for `theme/templates/base.html` and `theme/templates/base_fullscreen.html`
- Status of `theme/templates/base_redesign.html` (adopt/archive/remove)
- Demo/reference template governance (`styleguide`, `components_demo`, wrapper examples)

Risk level:

- None (planning-only pass, no runtime template edits)

### 2026-05-18 - Batch 1 (List Surface Canonicalization)

Scope completed:

- Canonical page headers
- Canonical form fields
- Canonical table wrappers/rows
- Canonical status badges
- Canonical spacing rhythm alignment

Migrated files:

- theme/templates/contracts/contract_list.html
- theme/templates/contracts/risk_log_list.html
- theme/templates/contracts/budget_list.html
- theme/templates/contracts/trademark_request_list.html

What changed in this batch:

- Removed inline row hover handlers and relied on shared table behavior.
- Replaced ad-hoc status pills with canonical `badge-sm` + semantic badge variants.
- Standardized list pages to shared header primitives (`page-wrap`, `page-header`, `page-title`, `page-subtitle`).
- Standardized table containers to canonical panel surfaces.

Remaining inconsistent areas:

- Additional list/detail templates still use ad-hoc pills and gray utility stacks.
- Several pages still use non-canonical page header structures.
- Some list pages still use mixed table wrappers (`rounded-xl`/raw utility wrappers) instead of canonical panel/table primitives.
- Form constants in `contracts/forms.py` still encode legacy utility strings and require Phase 2 form-primitive migration.

Visual-risk level:

- Low-to-medium
- Reason: visual primitives were normalized without adding new styles or changing data/flow logic.

### 2026-05-18 - Batch 2 (Pattern-First QueuePage Migration)

Strategy completed before migration:

- Defined canonical archetype contracts in `DESIGN_ARCHETYPE_PATTERNS.md`:
  - QueuePage
  - WorkspacePage
  - CommandPage
  - NetworkPage
  - ExceptionPage
- Added reusable wrappers/examples in `theme/templates/patterns/archetype_wrappers_examples.html`.

QueuePage files migrated in this batch:

- theme/templates/contracts/client_list.html
- theme/templates/contracts/matter_list.html
- theme/templates/contracts/document_list.html

What changed in this batch:

- Replaced ad-hoc gray utility stacks with canonical QueuePage wrappers/primitives.
- Standardized page headers to canonical header behavior.
- Standardized filter placement and control primitives.
- Standardized table surfaces and row behavior to canonical table primitives.
- Standardized status chips to canonical badge semantics.

Remaining inconsistent areas:

- Some non-Queue templates still mix archetypes and need explicit archetype mapping before migration.
- Legacy inline event handlers remain in templates not yet in scope.
- Additional queue pages still use mixed local utility styling and await QueuePage conversion.

Visual-risk level:

- Low-to-medium
- Reason: migration was pattern-constrained with no route/data/logic modifications.

### 2026-05-18 - Batch 3 Pre-Migration Planning (WorkspacePage + ExceptionPage Dashboards)

Scope completed:

- Full per-template analysis of all 8 Batch 3 candidates.
- No template migration changes performed in this pass.
- Strict execution checklist created with per-page inconsistency mapping, migration scope, validation requirements, and risk scores.

Artifact produced:

- `BATCH3_WORKSPACE_MIGRATION_PLAN.md`

Batch 3 target templates (8 total):

WorkspacePage (5):
- theme/templates/dashboard.html
- theme/templates/contracts/workflow_dashboard.html
- theme/templates/contracts/repository.html
- theme/templates/contracts/privacy_dashboard.html
- theme/templates/contracts/legal_task_board.html

ExceptionPage (3):
- theme/templates/contracts/operations_dashboard.html
- theme/templates/contracts/deadline_list.html
- theme/templates/contracts/notification_list.html

Total template lines in scope: 1,158

Key findings per template:

- dashboard.html: Partially canonical; `action-chip` non-canonical CTA; `audit-action` non-canonical badge; arbitrary text sizes. Pre-migration decision required on `action-chip` status.
- workflow_dashboard.html: Entirely raw Tailwind utility stack; hardcoded `bg-teal-600` primary action; inline `onclick` filter toggle; no canonical primitive present.
- repository.html: Custom JS controller (`cms-aegis-repository.js`); partially canonical table; KPI cards non-canonical; inline `onclick` handler; all `id` and `data-*` attributes must survive migration.
- privacy_dashboard.html: Entirely raw Tailwind; no `page-wrap`, no `panel`, no `badge-sm`; raw KPI grid with responsive breakpoints.
- operations_dashboard.html: Entirely raw Tailwind; no `page-wrap`, no canonical KPI cards; no JS.
- legal_task_board.html: Has canonical header blocks; Kanban board body raw; AJAX `updateTaskStatus()` with inline `onclick` handler; keyboard accessibility gap; highest risk in batch.
- deadline_list.html: Entirely raw; inline POST form in action column; no JS.
- notification_list.html: Entirely raw; simplest template; no JS; safest start.

Recommended migration order: notification_list → deadline_list → privacy_dashboard → operations_dashboard → dashboard → workflow_dashboard → repository → legal_task_board

Highest-risk page: legal_task_board.html
Safest page: notification_list.html
Templates requiring JS changes: repository.html, legal_task_board.html (scoped inline handler removal only)
Templates requiring pre-migration decisions: dashboard.html (action-chip audit), legal_task_board.html (Kanban subvariant decision)

Risk level:

- None for this planning pass (no template changes)
- Batch 3 execution estimated: Medium overall; High for legal_task_board.html

### 2026-05-18 - Batch 3 Slice 1 (ExceptionPage + WorkspacePage — 4 templates)

Scope completed:

- notification_list.html → ExceptionPage (55 lines migrated)
- deadline_list.html → ExceptionPage (62 lines migrated)
- privacy_dashboard.html → WorkspacePage (92 lines migrated)
- operations_dashboard.html → ExceptionPage (88 lines migrated)

New primitive added to base.html during this slice:

- `.chip`, `.chip-active`, `.chip-inactive` — canonical filter tab controls; token-backed; light/dark variant defined; needed by notification_list and deadline_list filter toolbars.

What changed per template:

**notification_list.html:**
- Applied `page-wrap`, `page-header`, `page-title`, `page-subtitle`.
- Replaced raw gray button with `btn-ghost` in `page-actions`.
- Replaced raw pill filter tabs with `chip chip-active` / `chip chip-inactive`.
- Replaced raw container with `panel`.
- Replaced raw rows with `list-row`.
- Added `aria-label` to notification type icon badges; `aria-hidden="true"` to icon SVGs.
- Replaced empty state with `empty-state`.
- Used `c-primary`, `c-muted`, `item-meta`, `c-link` for body text hierarchy.
- Preserved POST forms for mark-read / mark-all-read, filter URL parameters, and `is_read` conditional background signal.

**deadline_list.html:**
- Applied `page-wrap`, `page-header`, `page-title`, `page-subtitle`.
- Replaced `bg-blue-600` primary button with `btn-primary-grad`.
- Replaced raw pill filter tabs with `chip chip-active` / `chip chip-inactive`.
- Replaced raw table container with `panel overflow-hidden` + `overflow-x-auto` wrapper for mobile safety.
- Applied `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`.
- Replaced raw priority/status pills with `badge-sm badge-red|badge-yellow|badge-gray|badge-green`.
- Added `aria-label` to inline form Complete button.
- Used `c-primary`, `item-meta` for title/meta hierarchy.
- Preserved POST form for complete action, overdue row background tinting, filter URL parameters, `days_remaining` display.

**privacy_dashboard.html:**
- Applied `page-wrap`, `page-header`, `page-title`, `page-subtitle`.
- Replaced raw gray link with `btn-ghost` in `page-actions`.
- Replaced raw 4-col KPI grid with `dash-grid dash-grid-4`.
- Replaced raw KPI card containers with `kpi-card kpi-card-link` (canonical link-card pattern).
- Replaced raw 3-col grid with `dash-grid dash-grid-3`.
- Added `aria-hidden="true"` to all decorative icon SVGs.
- Replaced DSAR table container with `panel overflow-hidden`.
- Applied `panel-head`, `panel-title` for DSAR table header.
- Applied `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`.
- Replaced raw status pills with `badge-sm badge-green|badge-red|badge-yellow`.
- Preserved all URL hrefs, `legal_hold_count > 0` urgency signal, `dsar_overdue > 0` signal, `{% if recent_dsars %}` conditional block.

**operations_dashboard.html:**
- Replaced `max-w-6xl` wrapper with `page-wrap`, `page-header`, `page-title`, `page-subtitle`.
- Replaced raw border button with `btn-ghost` in `page-actions`.
- Replaced raw 4-col KPI grid with `dash-grid dash-grid-4`, raw KPI cards with `kpi-card`.
- Replaced raw 2-col grid with `dash-grid dash-grid-2`, panels with `panel` + `panel-head` + `panel-inner`.
- Replaced job count sub-panels with `stat-card-lg` + `kpi-value` + `item-meta`.
- Replaced job list items with `list-row`.
- Replaced raw job status chip with `badge-sm badge-gray`.
- Added `role="region"` + `aria-label="Drill command"` to `<pre>` block.
- Preserved all context variable access, drill command pre block content, error_message conditional.

Validation:

- `manage.py check`: 0 issues.
- Template parse test (all 4): OK.
- `manage.py test contracts`: 3/3 passed.
- Inline handler scan: 0 violations found.

Remaining inconsistent areas after Slice 1:

- Batch 3 Slice 2 templates (dashboard.html, workflow_dashboard.html, repository.html, legal_task_board.html) remain unmigrated.
- `contracts/forms.py` form utility class constants still pending canonical form primitive migration.

Risk level:

- Low
- No business logic or route changes; no new visual systems; strict primitive substitution only.

## Phase 1 - Foundation and Governance (Week 1)

Task 1. Define design source-of-truth boundaries

- Why it matters: prevents token and component drift across shell/template/static layers.
- Affected files: theme/templates/base.html, theme/templates/base_fullscreen.html, theme/static_src/src/theme.css, theme/static_src/src/base.css, theme/static_src/src/components.css
- Impact: very high
- Difficulty: medium
- Risk: low

Task 2. Freeze new ad-hoc style additions

- Why it matters: prevents debt growth while migration is in progress.
- Affected files: all template files under theme/templates
- Impact: high
- Difficulty: low
- Risk: low

Task 3. Publish constitution and pull-request checklist gate

- Why it matters: enforces consistency as a delivery requirement, not a preference.
- Affected files: DESIGN_CONSTITUTION.md, QA_CHECKLIST.md, docs/ACTIVE_TODO.md
- Impact: high
- Difficulty: low
- Risk: low

## Phase 2 - Core Primitive Standardization (Week 2)

Task 1. Unify button system to 5 semantic variants

- Why it matters: buttons are the most visible inconsistency driver.
- Affected files: theme/templates/base.html, theme/static_src/src/components.css, high-traffic templates in theme/templates/contracts
- Impact: very high
- Difficulty: medium
- Risk: medium

Task 2. Unify form control system and migrate Python form constants

- Why it matters: forms are frequent and trust-sensitive in legal workflows.
- Affected files: contracts/forms.py, theme/templates/base.html, theme/static_src/src/components.css, form-heavy templates
- Impact: very high
- Difficulty: medium
- Risk: medium

Task 3. Standardize typography and spacing scale usage

- Why it matters: improves scanability and perceived professionalism quickly.
- Affected files: theme/templates/base.html, theme/static_src/src/base.css, key page templates
- Impact: high
- Difficulty: medium
- Risk: low

## Phase 3 - High-Impact Surface Migration (Weeks 3-4)

Task 1. Migrate dashboard and contract list to canonical components

- Why it matters: these pages anchor first and frequent impressions.
- Affected files: theme/templates/dashboard.html, theme/templates/contracts/contract_list.html
- Impact: very high
- Difficulty: medium
- Risk: medium

Task 2. Migrate workflow, repository, privacy dashboards

- Why it matters: demonstrates consistency in operational and governance contexts.
- Affected files: theme/templates/contracts/workflow_dashboard.html, theme/templates/contracts/repository.html, theme/templates/contracts/privacy_dashboard.html
- Impact: high
- Difficulty: medium
- Risk: medium

Task 3. Standardize auth/fullscreen experience with core shell language

- Why it matters: removes major visual disconnect between public and app surfaces.
- Affected files: theme/templates/base_fullscreen.html, theme/templates/registration/login.html, theme/templates/registration/register.html, theme/templates/registration/logout.html, theme/templates/contracts/saml_select.html, theme/templates/landing.html
- Impact: high
- Difficulty: medium
- Risk: medium

## Phase 4 - State, Feedback, and Interaction Consistency (Week 5)

Task 1. Canonicalize empty/loading/error/success states

- Why it matters: state quality strongly affects user confidence and recoverability.
- Affected files: dashboard + list/detail templates with empty and alert patterns
- Impact: high
- Difficulty: medium
- Risk: low

Task 2. Standardize badges, pills, and alerts

- Why it matters: status semantics must be instantly readable across workflows.
- Affected files: theme/templates/base.html and status-heavy templates
- Impact: high
- Difficulty: medium
- Risk: low

Task 3. Remove inline event handlers and centralize JS patterns

- Why it matters: improves maintainability, accessibility testing, and behavior consistency.
- Affected files: templates using onclick/onmouseover/onmouseout/onchange; shared JS modules
- Impact: high
- Difficulty: medium
- Risk: medium

## Phase 5 - Hardening and Continuous Governance (Week 6)

Task 1. Add visual regression snapshots for canonical pages

- Why it matters: protects consistency from future drift.
- Affected files: client/tests and Playwright specs; representative templates
- Impact: high
- Difficulty: medium
- Risk: low

Task 2. Add design lint checks for banned patterns

- Why it matters: blocks reintroduction of ad-hoc classes and inline handlers.
- Affected files: CI scripts, lint scripts, docs
- Impact: high
- Difficulty: medium
- Risk: low

Task 3. Complete migration of remaining tier-2 and tier-3 templates

- Why it matters: closes long-tail inconsistency and finalizes system adoption.
- Affected files: theme/templates/contracts/*, theme/templates/registration/*, theme/templates/landing.html
- Impact: medium-high
- Difficulty: high
- Risk: medium

## Priority Matrix (Execution Order)

1. Shell/token authority definition
2. Buttons and form controls
3. Table system
4. Status and feedback states
5. Inline behavior extraction
6. Long-tail template migration

## Exit Criteria

- One canonical shell and one canonical component primitive set in active use.
- No new inline style blocks in templates.
- No new inline event handlers in templates.
- All tier-1 pages migrated and visually consistent.
- Forms and tables conform to constitution.
- Visual regression tests passing on core pages.

## Milestone Outcome

When Phases 1-5 are complete, CMS Aegis should present as one coherent enterprise product with predictable interaction patterns, stronger trust signals, and lower implementation entropy.
