# Design Archetype Patterns - CMS Aegis

<!-- markdownlint-disable MD032 -->

Date: 2026-05-18
Source of truth: DESIGN_CONSTITUTION.md
Purpose: pattern-first migration contracts for Phase 2

## Global Rules

- No independent page redesigns.
- No new visual styles or styling systems.
- Preserve business logic, routing, and data behavior.
- Use canonical primitives from base shell and shared component classes.
- Prefer semantic classes over ad-hoc utility composition.

## 1) QueuePage

Use for: searchable/filterable queues with tabular or list records.

Layout structure:
- page-wrap
- page-header (title/subtitle + primary action)
- optional KPI strip (dash-grid)
- filter toolbar
- canonical table/list surface (panel + table or panel + list rows)
- pagination block

Spacing rhythm:
- section cadence: 24 between major sections
- internal card/table spacing follows canonical panel/table classes
- no one-off vertical spacing values

Header behavior:
- page-title + page-subtitle only
- primary action is right aligned in page-header
- secondary actions sit adjacent to primary action only if operationally required

Filter placement:
- single filter toolbar directly above results
- left: tabs/quick filters; right/flex: search and structured filters
- preserve submitted query parameters

Table/list behavior:
- table wrapper: panel overflow-hidden stat-card or panel overflow-hidden table-card
- headers: tbl-head / tbl-th
- rows: tbl-row + border-b transition-colors
- cells: tbl-td where applicable

Primary action placement:
- top-right of page-header
- uses canonical primary button treatment

Density rules:
- compact table density for operational scanning
- avoid mixed row densities within same queue

Empty/loading/error states:
- Empty: icon + short title + one next action link
- Loading: skeleton/spinner in table area (when async)
- Error: concise error copy + retry/clear-filters path

Mobile behavior:
- header stacks naturally within page-header
- filter controls wrap using flex-wrap
- tables remain horizontally scrollable when needed via canonical wrapper

## 2) WorkspacePage

Use for: multi-panel operational workspaces combining context, details, and tasks.

Layout structure:
- page-wrap
- page-header
- 2-column or stacked panel layout using canonical grid helpers
- primary workspace panel + secondary context panel(s)

Spacing rhythm:
- 24 between header and workspace body
- 16-20 between stacked panels

Header behavior:
- title/subtitle + optional primary action
- avoid dense action clusters; overflow actions move to panel headers

Filter placement:
- context-local filters inside owning panel header
- global workspace filters beneath page-header only when needed

Table/list behavior:
- panel-contained lists/tables only
- no free-floating table blocks outside panel surface

Primary action placement:
- top-right header for workspace-level action
- panel-level actions in panel-head

Density rules:
- relaxed density for mixed content; compact only for row-heavy subpanels

Empty/loading/error states:
- each panel owns its state treatment
- no global empty state replacing whole workspace unless all panels are empty

Mobile behavior:
- collapse to single column
- preserve panel ordering by operational priority

### WorkspacePage/BoardView Subvariant

Use for: status-column task boards and workflow stage boards within a WorkspacePage context.

Criteria for use (all must be true):
- Content is divided into discrete status columns (e.g. To Do / In Progress / Done).
- Users need to see all column states simultaneously.
- Cards within columns share a consistent shape and set of actions.

Layout structure:
- page-wrap
- page-header (title + optional primary action using `btn-primary-grad` or `btn-ghost`)
- optional filter bar using `panel` (canonical `chip` for filter controls, `form-input` for search)
- board-track (horizontal scroll flex container)
  - board-col (one per status, fixed width, flex-shrink-0)
    - board-col-head (column title + badge-sm item count)
    - board-card (one per item)
      - card title, optional card body text
      - badge-sm for priority/status
      - card footer: assignee, due date metadata using `item-meta` class
      - card actions using `c-link` or `btn-ghost`

Spacing rhythm:
- 24px between page-header and board-track
- 16px gap between board columns (board-track gap)
- 16px padding inside board-col
- 12px gap between board-cards inside a column

Primitive classes:
- `board-track`: horizontal scroll flex container (defined in base.html when first board page migrates)
- `board-col`: fixed-width column surface using `var(--surface)` background token
- `board-col-head`: column header row with title and count badge
- `board-card`: card surface using `var(--card-bg)` and `var(--card-border)` tokens

Column count badge:
- Use `badge-sm badge-gray` only (neutral, not semantic — the column title communicates status)

Card priority/status badges:
- Use `badge-sm` with semantic variants: `badge-red` (high/urgent), `badge-yellow` (medium), `badge-green` (low/done), `badge-gray` (default)

Card action rules:
- Edit/open actions: `c-link` style (`<a>` element)
- State-transition actions (e.g. Complete): `data-action` attribute bound to JS via `addEventListener` — never inline `onclick`
- At most 2–3 actions per card; overflow actions should be in a detail page

JavaScript binding rules:
- All card interactivity is data-attribute driven: `data-task-id`, `data-priority`, `data-status`
- Status update fetch calls are initiated by `addEventListener` on `[data-action="..."]` elements
- Filter JS reads `data-priority` and `data-status` attributes from card and column elements respectively
- No inline event handlers (`onclick`, `onchange`, `onmouseover`) permitted

ARIA requirements:
- Each `board-col` element: `role="region"` and `aria-label="[Column Name]"`
- Each `board-card` element: `role="article"`
- Board filter controls: standard accessible form controls (label + input association)
- Card action buttons: visible focus ring and `aria-label` if icon-only

Accessibility expectations:
- All card actions keyboard reachable and operable via Enter/Space
- Column regions navigable via Tab (do not rely on mouse-only interactions for status transitions)
- Card count badges update when JS re-renders column

Responsive behavior:
- board-track uses `overflow-x: auto` — horizontal scroll on narrow viewports is the expected behavior
- Column width is fixed (320px); do not collapse columns to < 260px
- Filter bar above the board wraps using flex-wrap; search input remains usable at 320px viewport

Empty column state:
- Use canonical `empty-state` inside `board-col` when no cards exist for that status
- Empty columns must still be visible (do not hide empty columns)

When NOT to use BoardView:
- When items do not map to discrete status columns (use QueuePage table instead)
- When there are more than 6 columns (consider a filtered list/table view instead)
- When column transitions are not meaningful to the user (use a sortable QueuePage)



Use for: forms/wizards/runbooks where user initiates an operation.

Layout structure:
- page-wrap or page-max-w
- page-header
- command panel (form-grid / section-grid)
- action footer (primary, secondary)

Spacing rhythm:
- consistent field group spacing from canonical form grid helpers

Header behavior:
- action-oriented title and outcome-focused subtitle

Filter placement:
- not applicable by default
- when present, filter controls must be subordinate to command intent

Table/list behavior:
- optional preview/result table below command panel using canonical table primitives

Primary action placement:
- right side of action footer or header when immediate run action is needed

Density rules:
- relaxed form density

Empty/loading/error states:
- inline validation/errors use canonical form error structure
- command execution states rendered near action footer/result block

Mobile behavior:
- single-column controls
- sticky action footer optional only if already supported

## 4) NetworkPage

Use for: relationship views (clients/matters/counterparties/linked entities) and graph-like mappings.

Layout structure:
- page-wrap
- page-header
- filter bar
- primary relationship surface (table/list/cards)
- optional side context panel

Spacing rhythm:
- same section cadence as QueuePage

Header behavior:
- emphasize scope and relationship context

Filter placement:
- top filter toolbar with entity and status filters

Table/list behavior:
- canonical table/list rows with linked-record affordances

Primary action placement:
- top-right for create/link operations

Density rules:
- compact for high-cardinality entity sets

Empty/loading/error states:
- empty state includes clear linking action
- error state includes retry and scope clarification

Mobile behavior:
- prioritize relationship identity columns
- defer secondary metadata visually but do not remove

## 5) ExceptionPage

Use for: alerts, incidents, errors, warnings, compliance exceptions, and dead-letter queues.

Layout structure:
- page-wrap
- page-header
- exception summary band (optional)
- canonical queue/list of exceptions

Spacing rhythm:
- keep high visual clarity with strict section rhythm

Header behavior:
- clearly states urgency and affected scope

Filter placement:
- severity/status filters first, search second

Table/list behavior:
- status-first row composition
- action column emphasizes triage/resolution

Primary action placement:
- right aligned for triage/escalate/create exception

Density rules:
- compact rows, clear status badges

Empty/loading/error states:
- empty = positive confirmation state with no-critical-items messaging
- loading/error behavior follows QueuePage conventions

Mobile behavior:
- status and title remain first-line visible
- action moves below metadata when needed

## Reusable Wrapper Contract

Canonical wrapper classes by role:
- page shell: page-wrap
- page header: page-header / page-title / page-subtitle
- actions: btn-primary-grad / btn-ghost / btn-soft-primary
- filters: form-input / form-select + flex filter toolbar
- surfaces: panel / stat-card / table-card
- tables: tbl-head / tbl-th / tbl-row / tbl-td
- status: badge-sm + badge-green|badge-blue|badge-yellow|badge-red|badge-gray|badge-purple
- empty: surface-bubble + c-muted + c-primary + c-link

Migration rule:
- A page must map to one archetype before migration.
- If a page spans multiple archetypes, split migration scope and keep existing behavior intact.

<!-- markdownlint-enable MD032 -->
