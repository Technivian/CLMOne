# Operations Dashboard Migration

## Files changed

- `theme/templates/contracts/operations_dashboard.html`
- `theme/templates/contracts/operations_dashboard_content.html`
- `theme/templates/contracts/operations_dashboard_actions.html`
- `theme/templates/contracts/operations_dashboard_kpis.html`
- `theme/templates/contracts/operations_dashboard_job_counts_meta.html`
- `theme/templates/contracts/operations_dashboard_job_counts.html`
- `theme/templates/contracts/operations_dashboard_drill_meta.html`
- `theme/templates/contracts/operations_dashboard_drill.html`
- `theme/templates/contracts/operations_dashboard_recent_jobs_meta.html`
- `theme/templates/contracts/operations_dashboard_recent_jobs.html`
- `theme/templates/contracts/operations_dashboard_recent_job_row.html`
- `theme/templates/contracts/operations_dashboard_recent_job_body.html`
- `theme/templates/contracts/operations_dashboard_scheduled_runs_meta.html`
- `theme/templates/contracts/operations_dashboard_scheduled_runs.html`
- `theme/templates/contracts/operations_dashboard_scheduled_run_row.html`
- `theme/templates/contracts/operations_dashboard_scheduled_run_body.html`
- `docs/design-system-adoption/OPERATIONS_DASHBOARD_MIGRATION.md`

## Adapter partials/classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `design_system/dense_admin_list.html`
- `design_system/dense_admin_row.html`
- `dc-ds-metric-grid`
- `dc-ds-metric`
- `dc-ds-button`

## Behavior preserved

- The page still extends `base.html`.
- The `docclad_format` template library is still loaded.
- The title remains `Operations Dashboard – DocClad`.
- The Back to settings link still targets `settings_hub`.
- Scheduler, database, alerts, request metrics, job counts, drill state, recent jobs, recent job runs, and failed 24h count all render from existing context variables.
- The drill command text is unchanged.
- Empty states remain:
  - `No background jobs yet.`
  - `No scheduled job runs recorded yet.`

## Dense admin list validation

The new dense admin list adapter is used for:

- Recent jobs
- Scheduled job runs

No POST forms or destructive actions exist on this page.

## Risks avoided

- No backend views, URLs, models, forms, permissions, auth behavior, queries, exports, or business logic were changed.
- No JavaScript was added.
- No broad table system was introduced.

## Known limitations

- The job-count cards still use existing stat-card utility classes inside a design-system surface.
- The dense admin list is not a full data table and does not provide sorting/filtering/pagination.
