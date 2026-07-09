# Approval Rule Form Migration

## Files changed

- `theme/templates/contracts/approval_rule_form.html`
- `theme/templates/contracts/approval_rule_form_content.html`
- `theme/templates/contracts/approval_rule_form_body.html`
- `docs/design-system-adoption/APPROVAL_RULE_FORM_MIGRATION.md`

This migration does not add new CSS. The compiled stylesheet may still be rewritten when `theme/static_src` is built.

## Adapter partials and classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `dc-ds-actions`
- `dc-ds-button`
- `dc-ds-button--primary`
- `dc-ds-button--ghost`

## Form behavior preserved

- The page still extends `base.html`.
- The page title remains `{{ object|yesno:"Edit,New" }} Approval Rule – DocClad`.
- The create/update heading still derives from `object|yesno:"Edit,New"`.
- The form method remains `post`.
- The form action remains omitted, so submission still posts to the current route.
- The form `enctype="multipart/form-data"` is preserved.
- `{% csrf_token %}` is preserved.
- The submit button remains `type="submit"` and still says `Save`.
- The cancel link still targets `contracts:approval_rule_list`.
- No backend views, URLs, models, forms, permissions, auth behavior, queries, or data fetching were changed.
- No JavaScript was added.

## Fields preserved

The template still renders every Django form field through the existing generic loop:

- `{% for field in form %}`
- `{{ field }}`

The underlying `ApprovalRuleForm` fields remain unchanged:

- `name`
- `description`
- `trigger_type`
- `trigger_value`
- `approval_step`
- `approver_role`
- `specific_approver`
- `sla_hours`
- `escalation_after_hours`
- `is_active`
- `order`

Hidden fields, bound values, widget classes, field names, and field types remain controlled by the Django form exactly as before.

## Validation/error behavior preserved

- Field labels still use `field.id_for_label` and `field.label`.
- Help text still renders with `field.help_text`.
- Field errors still render with `field.errors|join:", "`.
- The previous template did not render non-field errors, so no new non-field error block was introduced.

## Risks avoided

- No route names were changed.
- No form field widgets were changed.
- No POST behavior was changed.
- No permission checks were changed.
- No shell, sidebar, or topbar templates were changed.
- No React, Radix, shadcn, or new JavaScript was introduced.
- The field loop was left structurally intact because changing field-by-field markup would increase form risk.

## Manual test checklist

- Open the new approval-rule form.
- Confirm every field appears with its existing widget type and bound value behavior.
- Submit an invalid form and confirm field-level validation errors render.
- Submit a valid create form and confirm it creates an approval rule.
- Open an existing approval rule edit form and confirm values are bound.
- Submit an update and confirm it saves to the same record.
- Confirm Cancel returns to the approval-rule list.
- Confirm tenant-scoped approver choices remain scoped by the existing backend form logic.

## Before/after notes

- Before: local `page-wrap`, `page-header`, `panel`, `panel-inner`, `btn-primary-grad`, and `btn-ghost` presentation.
- After: design-system scaffold, hero, surface card, and adapter buttons.
- The field rendering remains Django-template-native and form-owned.

## Known limitations

- The adapter does not yet include a reusable form-field partial.
- This page confirms the need for a `dc-ds-form-field` partial before migrating more complex forms.
