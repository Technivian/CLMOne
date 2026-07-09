# Organization Identity Settings Migration

## Files changed

- `theme/templates/contracts/organization_identity_settings.html`
- `theme/templates/contracts/organization_identity_settings_content.html`
- `theme/templates/contracts/organization_identity_settings_form.html`
- `theme/templates/contracts/organization_identity_saml_endpoints.html`
- `theme/templates/contracts/organization_identity_scim.html`
- `theme/templates/contracts/organization_identity_api_access.html`
- `theme/templates/contracts/organization_identity_salesforce.html`
- `theme/templates/contracts/organization_identity_webhooks.html`
- `docs/design-system-adoption/ORGANIZATION_IDENTITY_SETTINGS_MIGRATION.md`

## Forms/action blocks found

- Main identity settings form: `method="post"`, saves SAML and SCIM settings.
- SCIM token rotation form: `method="post"`, hidden `action=rotate_scim_token`, `data-confirm` confirmation.
- API token rotation form: `method="post"`, hidden `action=rotate_api_token`, `data-confirm` confirmation.

## Blocks using `form_field.html`

None.

The main form uses manual labels and a custom SCIM checkbox help block. Using `form_field.html` would change visible label copy and checkbox structure, so the field blocks were preserved structurally.

## Blocks left structurally unchanged

- Main form fields and custom SCIM checkbox: preserved to avoid changing labels, widget rendering, and checkbox helper copy.
- SCIM token rotation form: preserved because it is a sensitive action with hidden `action` and `data-confirm`.
- API token rotation form: preserved because it is a sensitive action with hidden `action` and `data-confirm`.
- Salesforce and webhook tables: preserved as native tables because the adapter still lacks a dense table partial.

## Adapter partials/classes used

- `design_system/page_scaffold.html`
- `design_system/page_hero.html`
- `design_system/surface_card.html`
- `dc-ds-actions`
- `dc-ds-button`
- `dc-ds-button--ghost`
- `dc-ds-button--primary`

## Behavior preserved

- The page still extends `base.html`.
- The page title remains `Identity Provider – DocClad`.
- The main form still posts to the current route because no `action` attribute was added.
- Every `{% csrf_token %}` is preserved.
- Every field widget is still rendered from the Django form object.
- Token preview conditionals remain unchanged.
- Salesforce and webhook empty states remain unchanged.
- No backend views, URLs, models, forms, permissions, auth behavior, queries, or data fetching were changed.
- No JavaScript was added.

## Token/security behavior preserved

- `data-confirm="Rotate the SCIM token? This will invalidate the existing token."` is preserved.
- Hidden input `name="action" value="rotate_scim_token"` is preserved.
- `Rotate SCIM token` submit label is preserved.
- `data-confirm="Rotate the API token? This will invalidate the existing token value."` is preserved.
- Hidden input `name="action" value="rotate_api_token"` is preserved.
- `Rotate API token` submit label is preserved.
- One-time SCIM and API token preview rendering is preserved.

## Fields/buttons/actions preserved

- `form.identity_provider`
- `form.saml_entity_id`
- `form.saml_sso_url`
- `form.saml_slo_url`
- `form.saml_metadata_url`
- `form.saml_x509_certificate`
- `form.scim_enabled`
- `Save identity settings`
- `View identity telemetry`
- `Manage approval rules`
- `View approval requests`

## Risks avoided

- Did not manually reconstruct any inputs.
- Did not change token rotation form structure.
- Did not add non-field error rendering because the original template did not render it.
- Did not change table structure for Salesforce sync or webhook deliveries.
- Did not alter shell, sidebar, or topbar markup.

## Manual test checklist

- Open `/settings/identity/`.
- Save identity settings and confirm SAML and SCIM fields persist.
- Rotate the SCIM token and confirm the token preview appears once.
- Rotate the API token and confirm the token preview appears once.
- Confirm the SCIM and approval links still point to the same URLs.
- Confirm Salesforce sync rows and empty state render.
- Confirm webhook delivery rows and empty state render.
- Confirm a non-admin user remains forbidden by backend permissions.

## Before/after notes

- Before: local `page-max-w`, `settings-card-lg`, and page-specific section layout.
- After: design-system scaffold, hero, and surface cards while preserving form/table internals.

## Known limitations

- The page still uses existing form/table utility classes inside adapter surfaces.
- A future pass should add a dense table partial and a checkbox-specific form-field partial before changing those inner structures.
