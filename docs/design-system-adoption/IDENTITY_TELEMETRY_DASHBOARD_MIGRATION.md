# Identity Telemetry Dashboard Migration

## Files changed

- `theme/templates/contracts/identity_telemetry_dashboard.html`
- `theme/templates/contracts/identity_telemetry_dashboard_content.html`
- `theme/templates/contracts/identity_telemetry_dashboard_actions.html`
- `theme/templates/contracts/identity_telemetry_recovery_meta.html`
- `theme/templates/contracts/identity_telemetry_recovery_body.html`
- `theme/templates/contracts/identity_telemetry_recent_logs.html`
- `docs/design-system-adoption/IDENTITY_TELEMETRY_DASHBOARD_MIGRATION.md`

The compiled stylesheet may change when `theme/static_src` is built, but this migration does not add new CSS.

## Adapter partials and classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `design_system/status_badge.html`
- `design_system/audit_timeline_item.html`
- `dc-ds-metric-grid`
- `dc-ds-metric`
- `dc-ds-metric__label`
- `dc-ds-metric__value`
- `dc-ds-timeline`
- `dc-ds-actions`
- `dc-ds-button`

## Behavior preserved

- The page still extends `base.html`.
- The page title remains `Identity Telemetry – DocClad`.
- The subtitle still reads `SAML, SCIM, MFA, and recovery-code activity for {{ organization.name }}`.
- The `settings_hub` back link is preserved.
- All telemetry metrics still render from `telemetry_events`.
- Recovery-code inventory still renders from `recovery_code_counts`.
- Recent identity events still render from `recent_logs`.
- The original empty states remain:
  - `No active members found.`
  - `No recent identity events.`
- No backend views, URLs, forms, permissions, auth behavior, queries, or data fetching were changed.

## Data/context variables preserved

- `organization.name`
- `telemetry_events`
- `metric.key`
- `metric.label`
- `metric.value`
- `recovery_code_counts`
- `profile.user.get_full_name`
- `profile.user.username`
- `profile.mfa_recovery_code_count`
- `profile.mfa_enabled`
- `recent_logs`
- `log.changes.event`
- `log.action`
- `log.timestamp`
- `log.model_name`

## Risks avoided

- No shell, sidebar, or topbar templates were changed.
- No route names were changed.
- No forms or POST behavior were introduced.
- No React, Radix, shadcn, or new JavaScript was introduced.
- The recovery-code inventory remains a native table because tabular member data is clearer and lower risk than forcing it into cards.

## Manual test checklist

- Open `/organizations/identity-telemetry/` as an organization owner/admin.
- Confirm the page renders inside the existing DocClad shell.
- Confirm the Back to settings link returns to `/settings/`.
- Confirm KPI values match the underlying telemetry counts.
- Confirm recovery-code rows render active member profiles.
- Confirm MFA enabled displays `Yes` or `No`.
- Confirm recent logs render event/action, timestamp, and model name.
- Confirm empty states render when collections are empty.

## Before/after notes

- Before: local `page-wrap`, `page-header`, `dash-grid`, `kpi-card`, and `panel` markup.
- After: design-system scaffold, hero, metric cards, surfaces, badges, and timeline rows.
- The dashboard data and conditionals remain Django-template-native.

## Known limitations

- The adapter does not yet include a table-specific partial, so the recovery-code inventory uses a native table inside a design-system surface.
