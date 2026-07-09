# Organization Activity Migration

## Existing structure

The original page used:

- Page header with a `Back to Team` link.
- GET filter form with action/model/date filters, autosubmit attributes, submit button, and export link.
- Native table with timestamp, user, action, type, object, and event columns.
- Empty table row: `No organization activity entries yet.`
- Pagination links that preserve the existing query string.

## Dense admin list fit

`dense_admin_list` is appropriate because organization activity rows are compact audit entries with:

- row title: actor/user
- timestamp
- metadata: object representation
- badge: action
- body: type and event

The page does not require editable columns or column-level comparison, so a dense audit row is a better fit than adding a new table system.

## Behavior preserved

- GET filter method and all input names are preserved: `action`, `model`, `start_date`, `end_date`.
- `data-autosubmit` attributes are preserved.
- Filter selected/value conditionals are preserved.
- Export link still targets `contracts:organization_activity_export` and preserves `query_string`.
- Pagination still preserves `query_string` and `page`.
- No POST behavior exists on this page.
- Backend owner/admin permission checks remain unchanged.

## Context/data preserved

- `organization.name`
- `logs`
- `log.timestamp`
- `log.user.get_full_name`
- `log.user.username`
- `log.action`
- `log.get_action_display`
- `log.model_name`
- `log.object_repr`
- `log.changes.event`
- `is_paginated`
- `page_obj`
- `query_string`

## Adapter partials/classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `design_system/dense_admin_list.html`
- `design_system/dense_admin_row.html`
- `dc-ds-filterbar`
- `dc-ds-button`
- `dc-ds-actions`

## Tests

Relevant existing tests:

- `test_owner_can_view_organization_activity`
- `test_admin_can_view_organization_activity`
- `test_non_admin_cannot_view_organization_activity`
- `test_owner_can_export_organization_activity_csv`
- `test_activity_filters_apply`

## Known limitations

- This migration removes table column alignment in favor of dense audit rows.
- A future true `dc-ds-table` partial is still useful for pages where column comparison is required.
