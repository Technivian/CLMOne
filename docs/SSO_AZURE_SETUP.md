# Microsoft Entra SSO setup (OIDC)

CLM One supports a bounded, single-tenant Microsoft Entra OIDC configuration
through `mozilla-django-oidc`. The integration is committed off and must not be
enabled with production credentials without the identity release gate.

## Security model

- One explicit Entra tenant UUID is accepted; `common`, `organizations`,
  `consumers`, multi-tenant, and issuer-mismatched tokens are rejected.
- JWT signature, audience, expiry, and nonce validation remain owned by the
  OIDC library; CLM One additionally checks the token tenant and issuer.
- Just-in-time user creation is disabled.
- A user must already exist with one unique matching email and have an active
  membership in an active, explicitly allowlisted OIDC workspace.
- The workspace role remains the existing `OrganizationMembership` role. Entra
  claims never grant or change a CLM One role.
- An explicit email-domain allowlist is required as defense in depth.
- Access and ID tokens, secrets, raw claims, and subject identifiers are not
  stored in the audit event. Successful login records only the
  `microsoft_entra` authentication method.
- Password login remains available as a recovery path unless a separately
  authorized policy changes it.

## 1. Register the application

In Microsoft Entra admin center:

1. Open **Identity → Applications → App registrations → New registration**.
2. Name the application `CLM One`.
3. Select **Accounts in this organizational directory only**.
4. Add a Web redirect URI:
   `https://<non-production-host>/oidc/callback/`.
5. Do not add a production redirect URI during a pilot configuration.

Record the Directory (tenant) ID and Application (client) ID. Create a
short-lived non-production client secret through the approved secret store;
never put it in source, a migration, a fixture, a screenshot, or this runbook.

## 2. Pre-provision users

Before testing SSO, create or invite each synthetic pilot user through the
existing governed workspace administration path. Confirm:

- the stored email uniquely matches the Entra `email`, `upn`, or
  `preferred_username` claim;
- the user and workspace are active;
- the membership is active and has the intended existing role; and
- the workspace identity provider is `OpenID Connect`.

SSO does not create an account, workspace, membership, role, or permission.

## 3. Configure a named non-production environment

```bash
SSO_ENABLED=true
MICROSOFT_ENTRA_SSO_ENABLED=true
MICROSOFT_ENTRA_TENANT_ID=<tenant-uuid>
MICROSOFT_ENTRA_ORG_ALLOWLIST=<synthetic-workspace-slug>
OIDC_CREATE_USER=false
SSO_ALLOWED_EMAIL_DOMAINS=<approved-domain>
OIDC_RP_CLIENT_ID=<client-id-from-secret-store>
OIDC_RP_CLIENT_SECRET=<client-secret-from-secret-store>
OIDC_OP_DISCOVERY_ENDPOINT=https://login.microsoftonline.com/<tenant-uuid>/v2.0/.well-known/openid-configuration
OIDC_RP_SCOPES=openid email profile
OIDC_VERIFY_SSL=true
```

`MICROSOFT_ENTRA_SSO_ENABLED=false` remains the committed state. Startup fails
for a non-UUID tenant, a non-tenant-specific discovery endpoint, an empty
domain/workspace allowlist, or `OIDC_CREATE_USER=true`.

## 4. Validate

Use synthetic identities only:

1. Verify password login and recovery still work.
2. Open `/login/` and select **Continue with Microsoft**.
3. Confirm the exact pre-provisioned user reaches only their existing
   workspace and role.
4. Confirm an unknown user, inactive user, inactive membership, wrong domain,
   wrong tenant, `common` issuer, and duplicate email are denied generically.
5. Confirm sign-in produces an append-only `auth.login_succeeded` event with
   `authentication_method=microsoft_entra` and no token or claim content.
6. Confirm logout and idle-session/MFA policy still apply.

## Abort and rollback

For any tenant/issuer mismatch, unexpected provisioning, role change, wrong
workspace, audit leak, or recovery-path failure:

1. set `MICROSOFT_ENTRA_SSO_ENABLED=false`;
2. set `SSO_ENABLED=false`;
3. restart the application;
4. revoke the non-production client secret in Entra; and
5. preserve the content-free release and audit evidence.

Rollback changes configuration only. Do not delete users, memberships, audit
events, or sessions as an unreviewed repair. Production activation, forced SSO,
password retirement, SCIM authority, role mapping, and live PayrollMinds
identity data require separate authorization.
