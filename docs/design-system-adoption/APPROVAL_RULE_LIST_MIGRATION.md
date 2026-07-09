# Approval Rule List Migration

## Files changed

- `theme/templates/contracts/approval_rule_list.html`
- `theme/templates/contracts/approval_rule_list_content.html`
- `theme/templates/contracts/approval_rule_list_actions.html`
- `theme/templates/contracts/approval_rule_list_table.html`
- `docs/design-system-adoption/APPROVAL_RULE_LIST_MIGRATION.md`

This migration does not add new CSS. The compiled stylesheet may still be rewritten when `theme/static_src` is built.

## Adapter partials and classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `design_system/status_badge.html`
- `design_system/empty_state.html`
- `dc-ds-button`
- `dc-ds-button--primary`

## Behavior preserved

- The page still extends `base.html`.
- The page title remains `Approval Rules – DocClad`.
- The page heading remains `Approval Rules`.
- The subtitle remains `Manage approval rules`.
- The create link still targets `contracts:approval_rule_create`.
- Each edit link still targets `contracts:approval_rule_update` with `item.pk`.
- The active-state conditional still renders `Yes` for active rules and `No` for inactive rules.
- The empty state still says `No approval rules found`.
- No backend views, URLs, models, forms, permissions, auth behavior, queries, or data fetching were changed.
- No destructive action behavior was changed; this template did not contain delete/destructive actions.

## Data/context variables preserved

- `rules`
- `item.name`
- `item.get_trigger_type_display`
- `item.trigger_value`
- `item.get_approval_step_display`
- `item.sla_hours`
- `item.is_active`
- `item.pk`

## Risks avoided

- No shell, sidebar, or topbar templates were changed.
- No route names were changed.
- No forms, POST behavior, or destructive actions were introduced.
- No React, Radix, shadcn, or new JavaScript was introduced.
- The approval-rule table remains a native table inside a design-system surface.

## Manual test checklist

- Open `/contracts/approval-rules/`.
- Confirm the page renders inside the existing DocClad shell.
- Confirm the `Add New` button opens the approval-rule create route.
- Confirm each `Edit` button opens the correct approval-rule update route.
- Confirm rule rows display name, trigger, trigger value, step, SLA, and active state.
- Confirm inactive rules display `No`.
- Confirm the empty state appears when the organization has no approval rules.
- Confirm tenant scoping still excludes other organizations' approval rules.

## Before/after notes

- Before: local `page-wrap`, `page-header`, `btn-primary-grad`, `panel`, `tbl-*`, and `badge-sm` markup.
- After: design-system scaffold, hero, surface, buttons, active badge, and empty state.
- The row data remains Django-template-native and table-based.

## Known limitations

- The adapter still lacks a dedicated table/list partial for dense administrative tables.
- This page confirms the need for a reusable `dc-ds-table` or list-table partial before migrating more dense admin pages.
