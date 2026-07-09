# Organization Security Settings Migration

## Files changed

- `theme/templates/contracts/organization_security_settings.html`
- `theme/templates/contracts/organization_security_settings_content.html`
- `theme/templates/contracts/organization_security_workspace_badge.html`
- `theme/templates/contracts/organization_security_mfa_badge.html`
- `theme/templates/contracts/organization_security_workspace_mode.html`
- `theme/templates/contracts/organization_security_mfa_policy.html`
- `theme/templates/contracts/organization_security_session_revocation.html`
- `docs/design-system-adoption/ORGANIZATION_SECURITY_SETTINGS_MIGRATION.md`

## Forms/action blocks found

- Workspace mode form: `method="post"`, hidden `action=save_workspace_mode`, manual `workspace_mode` select.
- MFA/session policy form: `method="post"`, manual `require_mfa` checkbox and `session_idle_timeout_minutes` number input.
- Session revocation form: `method="post"`, hidden `action=revoke_sessions`, `data-confirm` destructive confirmation.

## Blocks using `form_field.html`

None.

This template uses manual fields, hidden actions, selected/checked conditionals, and sensitive security actions. The internal form structures were preserved rather than converted to generic field partials.

## Blocks left structurally unchanged

- Workspace mode select: preserved because it is a manual input with selected-option conditionals.
- MFA checkbox and idle-timeout number input: preserved because they are manual security policy inputs.
- Revoke-all-sessions form: preserved because it is destructive and uses a hidden action plus confirmation attribute.

## Adapter partials/classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `design_system/status_badge.html`
- `dc-ds-actions`
- `dc-ds-button`
- `dc-ds-button--ghost`
- `dc-ds-button--primary`

## Behavior preserved

- The page still extends `base.html`.
- The page title remains `Organization Security – DocClad`.
- Every form still posts to the current route because no `action` attribute was added.
- Every `{% csrf_token %}` is preserved.
- Every field name, hidden input, selected/checked conditional, value, and button label is preserved.
- Session audit and security CSV links are preserved.
- No backend views, URLs, models, forms, permissions, auth behavior, queries, or data fetching were changed.
- No JavaScript was added.

## Security/session/destructive behavior preserved

- Hidden input `name="action" value="save_workspace_mode"` is preserved.
- Hidden input `name="action" value="revoke_sessions"` is preserved.
- `data-confirm="Revoke sessions for all active organization members?"` is preserved.
- `Revoke all sessions` remains a submit button inside the same POST form.
- MFA policy wording and session timeout wording are preserved.
- Active member count rendering is preserved.

## Fields/buttons/actions preserved

- `workspace_mode`
- `require_mfa`
- `session_idle_timeout_minutes`
- `Save workspace mode`
- `Save security policy`
- `Session audit`
- `Export security CSV`
- `Revoke all sessions`

## Permission checks preserved

The template had no permission conditionals. Backend owner/admin authorization in `organization_security_settings` remains unchanged.

## Risks avoided

- Did not manually reconstruct sensitive inputs beyond moving existing markup into page-local includes.
- Did not change destructive action form structure.
- Did not add non-field error rendering because the original template did not render it.
- Did not alter shell, sidebar, or topbar markup.

## Manual test checklist

- Open `/settings/security/` as an organization owner/admin.
- Confirm non-manager users remain forbidden.
- Change workspace mode and confirm it persists.
- Toggle MFA policy and confirm it persists.
- Set idle timeout and confirm it persists.
- Use Session audit link.
- Use Export security CSV link.
- Revoke all sessions and confirm affected sessions are forced to sign in again.

## Before/after notes

- Before: local `page-wrap`, `settings-card-lg`, and page-specific card headers.
- After: design-system scaffold, hero, surface cards, badges, and buttons while preserving form internals.

## Known limitations

- The page still uses existing form utility classes inside adapter surfaces.
- A future checkbox/select-specific form-field pattern would be needed before safely changing the inner security form markup.
