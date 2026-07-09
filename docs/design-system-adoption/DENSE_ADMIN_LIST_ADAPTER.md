# Dense Admin List Adapter

## Purpose

The dense admin list adapter is for audit, admin, and read-heavy pages that need compact rows with operational metadata and optional actions.

It is intentionally Django-template-native and does not own business behavior. Row actions remain page-owned so security-sensitive forms can preserve their exact method, action, CSRF token, hidden inputs, and confirmation attributes.

## Files

- `theme/templates/design_system/dense_admin_list.html`
- `theme/templates/design_system/dense_admin_row.html`
- `theme/static_src/src/design-system/components.css`

## When to use

Use `dense_admin_list.html` when:

- Rows are operational/audit records.
- Each row has a title plus metadata, timestamps, badges, or compact actions.
- Rows may contain sensitive POST actions that must remain structurally unchanged.
- The page needs more density than cards but less rigidity than a data table.

Use a normal table when:

- Users need column comparison.
- Numeric or tabular values must align by column.
- Sorting/filtering/pagination already exists around table semantics.
- The data has many repeated columns.

Use a card list when:

- Each item has rich narrative content.
- Rows need multiple sections or large descriptions.
- The page benefits from visual separation over density.

## Generic usage

```django
{% include "design_system/dense_admin_list.html" with items=records row_template="path/to/row.html" empty_title="No records found." %}
```

Row template:

```django
{% include "design_system/dense_admin_row.html" with title=item.name metadata=item.description badge_label=item.status actions_template="path/to/actions.html" %}
```

## Security-sensitive row actions

Keep sensitive action forms in page-owned templates:

```django
<form method="post" data-confirm="Revoke this session now?">
  {% csrf_token %}
  <input type="hidden" name="action" value="revoke_session">
  <input type="hidden" name="session_key" value="{{ item.session_key }}">
  <button type="submit" class="dc-ds-button dc-ds-button--ghost">Revoke</button>
</form>
```

Then include that form through `actions_template`. The adapter will place it visually but will not change its behavior.

## Supported row content

`dense_admin_row.html` supports:

- `title`
- `metadata`
- `timestamp`
- `badge_label`
- `badge_tone`
- `body_template`
- `actions_template`
- `class_name`

## Limitations

- This is not a full data-table system.
- It does not provide sorting, filtering, pagination, sticky headers, or column alignment.
- It intentionally does not construct forms or inputs.

## Migration guidance

For audit/admin pages:

1. Preserve the existing query/view/context.
2. Wrap the page in `page_scaffold.html` and `surface_card.html`.
3. Use `dense_admin_list.html` for repeated rows.
4. Keep destructive forms in page-local action includes.
5. Run the page's existing render/action tests.
