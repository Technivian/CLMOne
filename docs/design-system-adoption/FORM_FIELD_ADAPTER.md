# Form Field Adapter

## Purpose

The Django design-system adapter now includes a small form-field pattern for migrated Django-template pages. It is intentionally conservative: it renders Django `BoundField` objects directly and only styles wrapper, label, help text, and error text.

It does not change widgets, field names, IDs, values, attributes, validation, POST behavior, or form ownership.

## Files

- `theme/templates/design_system/form_field.html`
- `theme/templates/design_system/form_errors.html`
- `theme/templates/design_system/form_actions.html`
- `theme/static_src/src/design-system/components.css`

## Generic usage

Use inside an existing Django form. The parent template remains responsible for `method`, `action`, `enctype`, `csrf_token`, submit behavior, and route behavior.

```django
<form method="post">
  {% csrf_token %}
  {% include "design_system/form_errors.html" with form=form %}
  {% for field in form %}
    {% include "design_system/form_field.html" with field=field %}
  {% endfor %}
  <div class="dc-ds-actions">
    <button type="submit" class="dc-ds-button dc-ds-button--primary">Save</button>
  </div>
</form>
```

Optional action helper:

```django
{% url 'contracts:approval_rule_list' as cancel_url %}
{% include "design_system/form_actions.html" with submit_label="Save" cancel_label="Cancel" cancel_href=cancel_url %}
```

## Behavior guarantees

`form_field.html` preserves Django form behavior because it renders the passed field directly:

```django
{{ field }}
```

That means Django still owns:

- field name
- field ID
- widget type
- widget attributes
- hidden input rendering
- bound values
- selected/checked state
- validation state
- submitted POST values

No custom template filters are required.

## Hidden fields

Hidden fields are rendered directly and are not wrapped:

```django
{% if field.is_hidden %}
  {{ field }}
{% endif %}
```

This avoids invalid labels, spacing, and layout artifacts for hidden inputs.

## Labels, help text, and errors

Visible fields render:

- `field.label`
- `field.id_for_label`
- `field.help_text`
- each item in `field.errors`

`form_errors.html` renders `form.non_field_errors` in a page-level alert block when the parent page opts in.

## Limitations

- The partial does not style widgets directly because doing that safely would require changing widget attrs in forms or custom rendering inputs.
- Existing forms with inconsistent widget classes will keep those inconsistencies until the form classes are intentionally normalized.
- The action helper is optional and intentionally simple; complex action bars should use page-local markup or a dedicated future partial.

## Recommended migration approach

For simple forms, migrate in this order:

1. Wrap the page in `page_scaffold.html`.
2. Add `page_hero.html`.
3. Put the existing form inside `surface_card.html`.
4. Add `form_errors.html` only if non-field errors should be displayed.
5. Replace each visible field block with `form_field.html`.
6. Keep the parent form method/action/enctype/csrf exactly as-is.

For complex settings pages with multiple forms or destructive actions, migrate one form at a time and keep risky blocks structurally unchanged until verified.
