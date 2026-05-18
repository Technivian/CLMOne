# CMS Aegis Project Status

Last updated: 2026-04-25

Current checkout: `main` at `0262a2a` (`Automate release evidence bundle`)

## Executive Snapshot

CMS Aegis is a multi-tenant Django CLM / legal operations platform with contract lifecycle management, workflow routing, clause governance, privacy/compliance tooling, e-signature handling, search, reporting, and a broad set of admin/integration surfaces.

The app is **demo-ready** and **internally MVP-ready** for a CLM pilot. The current checkout can be taken to a `GO` release-gate state by running the synthetic Sprint 3 evidence seed + release evidence bundle command. The remaining production gap is live integration proof and rollback / restore evidence, not basic code correctness.

## UI Design Unification Status (Phase 2)

Latest pass: 2026-05-18 (Classification-only mapping pass)

Classification artifact:

- `DESIGN_ARCHETYPE_MAP.md`

Classification coverage:

- Templates scanned: 123
- UI routes classified: 190
- Recommended archetype totals:
  - QueuePage: 28
  - WorkspacePage: 20
  - CommandPage: 32
  - NetworkPage: 16
  - ExceptionPage: 19
  - Unknown / Needs decision: 8

Classification-only outcomes:

- Complete template-level planning matrix now exists with: current archetype, recommended archetype, confidence, drift notes, migration priority/risk, and dependencies.
- Major named UI routes now have recommended archetype mapping for migration planning.
- Top migration candidates and recommended Batch 3 scope are explicitly documented.

Classification pass risk level:

- None (no runtime template changes were made)

Previous migration batch: 2026-05-18 (Batch 1)

Migrated files:

- `theme/templates/contracts/contract_list.html`
- `theme/templates/contracts/risk_log_list.html`
- `theme/templates/contracts/budget_list.html`
- `theme/templates/contracts/trademark_request_list.html`

Batch outcomes:

- Canonical page headers applied (`page-wrap`, `page-header`, `page-title`, `page-subtitle`).
- Canonical form-field primitives maintained (`form-input`, `form-select`).
- Canonical table surface + row patterns applied (`panel`, `tbl-*`, removal of inline row hover handlers).
- Canonical status badge primitives applied (`badge-sm` + semantic badge variants).

Remaining inconsistent areas:

- Multiple list/detail templates still use ad-hoc status pills and non-canonical table wrappers.
- Some pages still use custom header structures and mixed spacing rhythm.
- `contracts/forms.py` still contains hardcoded utility class constants pending canonical form primitive migration.

Visual-risk level (latest batch):

- Low-to-medium
- Rationale: no business logic changes, no new visual styles, and no architecture changes; only primitive consolidation.

Pattern-first update (2026-05-18):

- Canonical page archetypes defined in `DESIGN_ARCHETYPE_PATTERNS.md`.
- Reusable wrappers/examples added in `theme/templates/patterns/archetype_wrappers_examples.html`.

Batch 2 migrated files (QueuePage archetype):

- `theme/templates/contracts/client_list.html`
- `theme/templates/contracts/matter_list.html`
- `theme/templates/contracts/document_list.html`

Batch 2 outcomes:

- Queue pages now follow canonical header, filter, table, badge, and spacing behavior.
- Business logic, data behavior, and routes preserved.

Batch 2 visual-risk level:

- Low-to-medium
- Rationale: strict archetype/pattern migration without introducing new visual systems or one-off designs.

Batch 3 pre-migration planning (2026-05-18):

- Strict execution checklist created before any template edits begin.
- Full per-template analysis completed for all 8 Batch 3 candidates.
- Artifact: `BATCH3_WORKSPACE_MIGRATION_PLAN.md`
- Status: Planning only — no templates modified.

Batch 3 Slice 1 migration (2026-05-18):

Migrated files:

- `theme/templates/contracts/notification_list.html` (ExceptionPage)
- `theme/templates/contracts/deadline_list.html` (ExceptionPage)
- `theme/templates/contracts/privacy_dashboard.html` (WorkspacePage)
- `theme/templates/contracts/operations_dashboard.html` (ExceptionPage)

Batch 3 Slice 1 outcomes:

- `chip`, `chip-active`, `chip-inactive` filter control primitives added to `base.html` (token-backed, light/dark variant).
- Canonical `page-wrap`, `page-header`, `page-title`, `page-subtitle` applied to all 4 templates.
- Canonical `panel`, `panel-head`, `panel-title` applied to table/card surfaces.
- Canonical `dash-grid dash-grid-4|3|2`, `kpi-card`, `stat-card-lg` applied to dashboard grid layouts.
- Canonical `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td` applied to all tables.
- Canonical `badge-sm` + semantic badge variants applied to all status/priority indicators.
- Canonical `btn-primary-grad`, `btn-ghost` applied to all action buttons.
- `aria-label` added to form action buttons and icon-only indicators; `aria-hidden` on decorative SVGs; `role="region"` on drill command block.
- `overflow-x-auto` table wrapper added for mobile safety.
- Zero business logic changes. Zero inline event handlers introduced. Zero routing changes.
- Django check: 0 issues. Template parse: 4/4 OK. Test suite: 3/3 passed.

Batch 3 Slice 2 Step 1 migration (2026-05-18):

Migrated files:

- `theme/templates/dashboard.html` (WorkspacePage — action-chip retirement + normalization)
- `theme/templates/base.html` (removed `.action-chip` CSS block — class fully retired)

Batch 3 Slice 2 Step 1 outcomes:

- `action-chip` is now fully retired from the design system. Zero references remain in any template.
- 3 × `action-chip` CTAs replaced with `btn-ghost` in dashboard.html page-actions.
- `audit-action` non-canonical badge replaced with `badge-sm` + semantic variant.
- `aria-hidden="true"` applied to all decorative SVGs in dashboard.html.
- Redundant sr-only span (duplicate of visible text) removed.
- Django check: 0 issues. Template parse: OK. Test suite: 3/3 passed.

Batch 3 Slice 2 Step 2 migration (2026-05-18):

Migrated files:

- `theme/templates/contracts/workflow_dashboard.html` (WorkspacePage — full primitive replacement)

Batch 3 Slice 2 Step 2 outcomes:

- Full WorkspacePage normalization: `page-wrap`, `page-header`, `page-title`, `page-subtitle`, `page-actions`.
- `bg-teal-600` hardcoded primary CTA replaced with `btn-primary-grad`.
- Raw secondary buttons/links replaced with `btn-ghost`.
- Inline `onclick="toggleFilters()"` removed; replaced with `addEventListener` in script block; `aria-expanded`/`aria-controls` added.
- Filter panel: raw bg/border → `panel` + `panel-inner`; labels → `form-label`.
- Table: `panel overflow-hidden`, `tbl-head`, `tbl-th`, `tbl-row`, `tbl-td`.
- Status dots: raw rounded divs → `status-dot [green/blue/yellow/gray]`.
- Stage badges: raw utility string → `badge-sm badge-[yellow/blue/purple/green/gray]`.
- Contract links → `c-link`; sub-text → `item-meta`; muted text → `c-muted`.
- Progress bar: raw Tailwind → `progress-bar-bg` / `progress-bar-fill`; `data-width` JS preserved.
- Pagination links → `btn-ghost`.
- Decorative SVG → `aria-hidden="true"`.
- Django check: 0 issues. Template parse: OK. Test suite: 3/3 passed. 0 inline violations.

Batch 3 Slice 2 Step 3 migration (2026-05-18):

Files changed:
- `theme/templates/contracts/repository.html` — WorkspacePage normalization; inline handler removal
- `theme/static/js/cms-aegis-repository.js` — two new addEventListener bindings in setupEventListeners()

Primitives applied: page-wrap, page-header, page-title, page-subtitle, page-actions, dash-grid dash-grid-4, kpi-card, kpi-card stat-card-amber, kpi-label, kpi-value, panel, panel-inner, tbl-th (normalized), aria-hidden on decorative SVGs, aria-label on select-all, aria-live="polite" on selected-count.

Inline handlers removed: saveCurrentView onclick → data-action="save-view" (bound via JS); clearSelection onclick → data-action="clear-selection" (bound via JS).

Batch 3 Slice 2 Step 3 outcomes:
- Template parse: OK
- manage.py check: 0 issues
- manage.py test contracts: 3/3 passed
- Inline handler/style scan: 0 violations
- Retired/ad-hoc class scan: 0 remaining

Batch 3 Slice 2 remaining templates:

- `theme/templates/contracts/legal_task_board.html` (WorkspacePage/BoardView — Kanban AJAX, highest risk, requires board-* CSS first) — **can begin now**

Batch 3 targets (8 templates, 1,158 total lines):
- WorkspacePage: dashboard.html, workflow_dashboard.html, repository.html, privacy_dashboard.html, legal_task_board.html
- ExceptionPage: operations_dashboard.html, deadline_list.html, notification_list.html

Batch 3 scope estimates:
- Estimated migration difficulty: Medium overall; High for legal_task_board.html
- Highest-risk page: theme/templates/contracts/legal_task_board.html
- Safest page: theme/templates/contracts/notification_list.html
- Recommended migration order: notification_list → deadline_list → privacy_dashboard → operations_dashboard → dashboard → workflow_dashboard → repository → legal_task_board
- Templates requiring JS changes (scoped): legal_task_board.html (inline onclick → addEventListener)
- Pre-migration decisions required: legal_task_board.html (Kanban subvariant governance, board-* CSS must be added to base.html first)

Expected UX impact if Batch 3 succeeds:
- Visual coherence across top 5 highest-traffic workspace surfaces.
- 25% of all WorkspacePage templates (5 of 20) on canonical primitive system.
- Inline event handler violations eliminated from 2 pages.
- Accessibility baseline improved (ARIA roles, aria-label, aria-hidden on icons).
- Token-backed primitives replacing hardcoded utility stacks on 4 fully-raw templates.

## What The App Is For

### Main user roles

- Org owner / admin
- Legal ops / contract manager
- Reviewer / approver
- Privacy / compliance operator
- External signer
- Integration operator / system admin

### Main business flows

- Register / log in / switch organization
- Create and manage contracts
- Draft from clause templates and playbooks
- Route work through workflows and approvals
- Send and reconcile signature requests
- Track privacy/compliance records and deadlines
- Search, save views, and export reports
- Sync from Salesforce / NetSuite and receive webhooks
- Monitor operations and release evidence

### Core modules

- Identity, tenancy, and session security
- Contracts, documents, clients, matters, counterparties
- Clause library, playbooks, variants, and versioning
- Workflow templates, workflow execution, approvals, and reminders
- Signature requests and e-sign reconciliation
- Privacy/GDPR records, DSAR, retention, subprocessors, transfers
- Search, repository, saved searches, and semantic ranking
- Reporting, dashboards, exports, and operational evidence
- Salesforce, NetSuite, SCIM, SAML, and webhook integrations
- AI assistant and AI action planning

## System Map

### Routes and pages

The route surface is large. The two route registries are:

- [`config/urls.py`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/config/urls.py)
- [`contracts/urls.py`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/contracts/urls.py)

Key route families:

- Public / auth:
  - `/`
  - `/login/`
  - `/register/`
  - `/logout/`
  - `/dashboard/`
  - `/profile/`
  - `/settings/*`
  - `/operations/`
- Identity:
  - `/saml/*`
  - `/oidc/*`
  - `/scim/v2/*`
- Contracts core:
  - `/contracts/`
  - `/contracts/new/`
  - `/contracts/<id>/`
  - `/contracts/<id>/edit/`
  - `/contracts/search/`
  - `/contracts/repository/`
  - `/contracts/notifications/`
- Repository and drafting:
  - `/contracts/clients/*`
  - `/contracts/matters/*`
  - `/contracts/documents/*`
  - `/contracts/clause-categories/*`
  - `/contracts/clause-library/*`
  - `/contracts/counterparties/*`
- Workflow / approvals / signatures:
  - `/contracts/workflows/*`
  - `/contracts/templates/*`
  - `/contracts/approval-rules/*`
  - `/contracts/approvals/*`
  - `/contracts/signatures/*`
- Privacy / compliance:
  - `/contracts/privacy/*`
  - `/contracts/due-diligence/*`
  - `/contracts/legal-tasks/*`
  - `/contracts/trademarks/*`
  - `/contracts/risks/*`
  - `/contracts/compliance/*`
  - `/contracts/budgets/*`
  - `/contracts/deadlines/*`
- APIs:
  - SCIM users / groups
  - contracts API v1 and legacy contracts API
  - Salesforce status / OAuth / field map / sync / sync runs
  - NetSuite sync
  - webhook deliveries
  - e-sign webhook
  - executive analytics / dashboard presets

### Major frontend templates

Templates are primarily server-rendered and live under:

- [`theme/templates/base.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/base.html)
- [`theme/templates/base_fullscreen.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/base_fullscreen.html)
- [`theme/templates/base_redesign.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/base_redesign.html)
- [`theme/templates/dashboard.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/dashboard.html)
- [`theme/templates/landing.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/landing.html)
- [`theme/templates/registration/login.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/registration/login.html)
- [`theme/templates/registration/register.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/registration/register.html)
- [`theme/templates/profile.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/profile.html)
- [`theme/templates/settings_hub.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/settings_hub.html)
- `theme/templates/contracts/*` for the business modules
- [`theme/templates/styleguide.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/styleguide.html)
- [`theme/templates/components_demo.html`](/Users/haroonwahed/Documents/Projects/CMS-Aegis/theme/templates/components_demo.html)

### Backend apps and modules

The codebase is centered on the `contracts` Django app:

- `contracts/models.py`
- `contracts/forms.py`
- `contracts/permissions.py`
- `contracts/middleware.py`
- `contracts/api/views.py`
- `contracts/views.py`
- `contracts/views_domains/*`
- `contracts/services/*`
- `contracts/management/commands/*`
- `contracts/domain/*`
- `config/settings_base.py`
- `config/urls.py`

### Database entities

The main persisted models are:

- Organization / membership / invitation / user profile
- SCIM groups and API tokens
- Salesforce connection / field map / sync run
- Webhook endpoint / delivery
- Executive dashboard preset / search preset
- Client / matter / contract / document / OCR review
- Time entry / invoice / trust account / trust transaction
- Deadline / audit log / notification
- Conflict check / trademark request / legal task / tag / risk log
- Compliance checklist / checklist item
- Workflow template / workflow template step / workflow / workflow step
- Due diligence process / task / risk
- Budget / budget expense
- Negotiation thread
- Counterparty
- Clause category / clause template / clause playbook / clause variant
- Ethical wall
- Signature request
- Data inventory / DSAR / subprocessor / transfer record / retention policy / legal hold
- Approval rule / approval request
- Background job

### APIs and integrations

The app currently includes:

- SCIM provisioning APIs
- SAML login / ACS / logout / metadata
- Salesforce OAuth, status, sync, and sync-run APIs
- NetSuite sync API / command
- E-sign webhook reconciliation API
- Webhook delivery APIs
- Executive analytics APIs
- API v1 contract endpoints
- Legacy contract APIs
- AI assistant contract endpoint
- Background job and evidence bundle commands

## What Works

- Tenant-scoped login / register / logout flows
- Dashboard and main navigation
- Contract create / edit / list / detail
- Clause library create / edit / compare / version history
- Workflow templates and workflow execution
- Signature requests and transition guardrails
- Privacy/compliance pages and records
- Search, semantic search, and saved search presets
- Reporting / executive dashboards / exports
- Client, matter, document, billing, trust, risk, compliance, due diligence, trademark, and ethical wall flows
- Focused Django test suites pass locally
- `manage.py check` passes
- `manage.py migrate --noinput` passes on the current checkout
- `manage.py audit_null_organizations` passes after migrations
- `manage.py generate_release_evidence_bundle` generates a full release evidence pack and reports `GO` when Sprint 3 evidence is seeded

## What Is Partial

- SAML and SCIM are implemented, but external IdP / lifecycle proof is still a deployment concern
- Salesforce, NetSuite, and e-sign integrations exist, but live end-to-end evidence is still the real gate
- Some UI shells and demo templates are still experimental
- Some features are strong enough for internal use but still need enterprise polish and production hardening

## What Is Broken Or Missing

- The repo currently has a moderate `postcss` vulnerability reported by `npm audit`
- `theme/templates/contracts/templates_list.html` still contains placeholder TODO actions for edit/use-template behavior
- `contracts/services/repository.py` still retains a mock service path and abstract interface
- Production proof is not complete without a backup / restore rehearsal and real live cutover evidence
- Live Salesforce / webhook evidence from the target environment is still needed for true rollout confidence

## Current Risks

- Large, high-complexity modules are still easy to regress
- Integrations depend on external systems and live credentials
- Release confidence depends on evidence, not just code passing locally
- The UI contains some experimental/demonstration shells that can confuse scope
- Frontend dependency audit has a moderate PostCSS issue

## Recommendation

Treat the app as:

- **Demo-ready:** yes
- **Internal MVP-ready:** yes, with scope discipline
- **Production-ready:** not yet for a live rollout, because production cutover proof and live integration evidence are still missing

## Next Recommended Actions

1. Capture live Salesforce sync evidence in the target org.
2. Capture webhook delivery evidence from a real endpoint.
3. Finish the backup / restore rehearsal on the real database target.
4. Remove or resolve the remaining frontend TODO actions.
5. Address the moderate PostCSS advisory.
6. Consolidate experimental UI shells and demo templates.
7. Keep release evidence bundle commands attached to the release workflow.
8. Add stronger live E2E coverage for the major user flows.
