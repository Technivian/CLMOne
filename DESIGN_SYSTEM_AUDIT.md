# DESIGN SYSTEM AUDIT - CMS Aegis

Date: 2026-04-18
Scope: Django templates, shared shells, Tailwind/CSS token layers, representative workflow pages
Assessment mode: UX, visual system, enterprise trust, implementation consistency

## 1) Executive Summary

CMS Aegis has strong functional breadth and meaningful domain coverage, but the UI system is currently in a mixed state. It does not yet present as one coherent enterprise product across all surfaces.

Short answer to the core questions:

- Does the app feel professionally designed? Partially. Some surfaces do, many still feel template-driven and inconsistent.
- Does it feel like one coherent product? Not yet. It feels like 2-3 visual systems coexisting.
- What immediately lowers trust? Inconsistent controls, mixed interaction patterns, and visible style drift between pages.
- What should be standardized first? Buttons, inputs, table patterns, feedback states, and shell ownership.
- Which 20% of fixes yields 80% improvement? Remove style drift in base shell + form controls + table system + status/empty/loading/error patterns.

## 2) Maturity Assessment

Overall maturity: 2.8 / 5 (Emerging, not yet governed)

Scorecard:

- Visual consistency: 2.5 / 5
- Enterprise polish: 2.8 / 5
- UX coherence: 2.6 / 5
- Implementation consistency: 2.3 / 5
- Accessibility consistency: 2.7 / 5
- Design governance readiness: 2.1 / 5

## 3) Evidence Snapshot (Implementation Facts)

Architecture and shell usage:

- Main shell usage is heavy: 112 templates extend base shell.
- Fullscreen shell is separate: 5 templates.
- Redesign shell adoption is currently zero: 0 templates.
- Evidence files: theme/templates/base.html, theme/templates/base_fullscreen.html, theme/templates/base_redesign.html

Styling system fragmentation:

- Inline style blocks exist in 4 key templates:

  - theme/templates/base.html
  - theme/templates/base_fullscreen.html
  - theme/templates/landing.html
  - theme/templates/components_demo.html

- Shared CSS also exists in theme/static_src/src/theme.css, theme/static_src/src/base.css, theme/static_src/src/components.css
- Result: token and component authority is split across shell and static pipeline.

Interaction pattern drift:

- 53 inline DOM event handlers remain in templates (onclick/onmouseover/onmouseout/onchange), indicating behavior coupled directly to markup.
- Repeated local toast implementations exist in clause_library, obligations_list, templates_list.

Control and component drift:

- Buttons: btn-primary, btn-primary-grad, btn-primary-sm, btn-primary-auth, btn-ghost, btn-ghost-secondary, btn-soft-primary, glow-btn-primary, btn-glow-blue, etc.
- Inputs: form-input, input-base, input-field, plus many raw utility strings in templates and Python forms.
- Tables: mixed use of tbl-* semantic classes and raw divide-y/bg-gray patterns.
- Status/feedback: multiple badge systems, pills, local toasts, message banners with inconsistent semantics.

Form style coupling in backend forms:

- contracts/forms.py uses hardcoded TAILWIND_INPUT/SELECT/TEXTAREA classes with blue ring and gray border assumptions.
- This creates backend-level dependency on current presentation choices.

## 4) What Works Well

- Primary shell has robust navigational IA and broad route coverage.
- Tokenized theming exists and supports light/dark variants in shared shell.
- Dashboard and selected list pages show stronger card/table discipline than earlier pages.
- Strong domain-specific UX breadth (contracts, risk, privacy, workflows, audit, trademark, DD).

## 5) Trust-Killing Issues (Highest Priority)

1. Multiple active design languages in production

- Example: enterprise dashboard style vs legacy gray utility pages vs glowing auth/landing style.
- Impact: product appears assembled, not designed as one platform.

1. Component semantics are not canonical

- Same intent implemented with different class systems and interaction states.
- Impact: inconsistent scanning, cognitive load, lower confidence.

1. Table and form systems are split

- Semantic table classes and raw utility-table markup coexist.
- Form controls are defined in Python constants and also ad-hoc in templates.
- Impact: inconsistent spacing, focus states, and control hierarchy.

1. Feedback/state behavior not standardized

- Alerts, badges, empty states, toasts, and flash messages use different visual and behavioral rules.
- Impact: weak predictability and reduced operational clarity.

1. Behavior embedded inline in templates

- Inline events and duplicated toast code increase fragility.
- Impact: hard to enforce consistency and accessibility across pages.

## 6) Design Debt Inventory

Shell and style debt:

- Dual shell stacks with duplicated style concerns:

  - theme/templates/base.html
  - theme/templates/base_fullscreen.html

- Unused redesign shell:

  - theme/templates/base_redesign.html

Component duplication debt:

- Buttons: 8+ variants with overlapping intent.
- Inputs: 4+ pattern families plus hardcoded form constants in Python.
- Tables: 2 major pattern families, mixed row hover approaches.
- Status/feedback: badges, pills, banners, toasts, messages implemented in multiple incompatible variants.

State pattern debt:

- Empty/loading/error/success states are not normalized by page type.
- Notifications and page messages vary in tone, density, and visual priority.

Behavioral debt:

- Inline handlers and per-page JS utilities duplicated across templates.

## 7) Pages to Prioritize for Redesign

Tier 1 (highest user-perceived impact):

- theme/templates/base.html
- theme/templates/base_fullscreen.html
- theme/templates/dashboard.html
- theme/templates/contracts/contract_list.html
- theme/templates/contracts/workflow_dashboard.html
- theme/templates/contracts/privacy_dashboard.html
- theme/templates/contracts/repository.html

Tier 2 (high consistency gain):

- theme/templates/contracts/client_list.html
- theme/templates/contracts/matter_list.html
- theme/templates/contracts/document_list.html
- theme/templates/contracts/reports_dashboard.html
- theme/templates/contracts/organization_security_settings.html
- theme/templates/contracts/legal_task_board.html

Tier 3 (supporting consistency):

- theme/templates/registration/login.html
- theme/templates/registration/register.html
- theme/templates/registration/logout.html
- theme/templates/contracts/saml_select.html
- theme/templates/landing.html

## 8) Canonical Pattern Recommendations

Adopt one canonical implementation per primitive:

- Shell: one source of truth for top bar, sidebar, page container, content rhythm.
- Button set: primary, secondary, ghost, danger, link (with defined sizes and state rules).
- Input set: text/select/textarea/checkbox/radio/switch with shared labels/help/error rules.
- Table set: compact and relaxed density variants with same typography and affordances.
- State set: loading, empty, success, warning, error, no-access.
- Feedback set: flash banner and toast both standardized with semantics and duration rules.

## 9) 80/20 Fixes (20% Work, 80% Perceived Quality Gain)

1. Consolidate shell and token authority into one system.
1. Standardize all form controls and migrate contracts/forms.py classes to shared semantic classes.
1. Standardize table scaffold (header, row hover, density, actions column).
1. Standardize status and feedback components (badges, alerts, toasts, messages).
1. Remove inline event handlers and move to delegated JS modules.

Expected result: immediate improvement in trust, coherence, and perceived build quality without rewriting every page.

## 10) Final Verdict

Current state: functional and promising, but visually and behaviorally inconsistent for enterprise-grade expectations.

Launch-quality design verdict:

- Operationally usable: yes.
- Enterprise-polished and design-coherent: not yet.

Recommendation: execute the unification roadmap before broad external scale-up, especially for high-stakes legal/compliance buyer workflows.
