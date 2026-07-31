# Microsoft Entra SSO bounded operator runbook

**Scope:** default-off single-tenant OIDC validation for pre-provisioned
synthetic users in one named non-production environment. Credentials,
production activation, forced SSO, password retirement, SCIM authority, group
or role mapping, and real PayrollMinds identities are excluded.

## Preconditions

- Exact implementation SHA has the applicable owner/review evidence and all
  required CI is green.
- The non-production Entra app is single-tenant and its callback is limited to
  the named environment.
- The client secret is held outside source in the approved environment secret
  store.
- Synthetic users have unique stored emails and active memberships in an
  active OIDC workspace named in `MICROSOFT_ENTRA_ORG_ALLOWLIST`.
- Password recovery has been smoke-tested before the window.

## Activation

Configure the values in `docs/SSO_AZURE_SETUP.md`, keeping
`OIDC_CREATE_USER=false`, then restart. Do not alter a membership, role, MFA
policy, or password policy as part of the activation.

Before exposing the login route, run:

```bash
.venv/bin/python manage.py verify_microsoft_entra_activation \
  --environment=<named-non-production-environment> \
  --workspace=<synthetic-workspace-slug> \
  --redirect-uri=https://<non-production-host>/oidc/callback/
```

Preserve the boolean-only output and exact application SHA as operator
evidence. Any non-zero result aborts the window. The preflight is read-only,
performs no network request, and intentionally discloses no configured value
or identity.

## Observe

Prove:

- exact-tenant, exact-issuer, pre-provisioned login succeeds;
- unknown, inactive, duplicate-email, wrong-domain, wrong-tenant, and
  common-issuer identities fail generically;
- the resulting user has exactly their existing workspace and role;
- the append-only success event records `microsoft_entra` without token/claim
  content; and
- password login/recovery, logout, idle timeout, MFA, and repository
  object-policy boundaries still work.

Abort immediately on an unexpected user creation, membership/role change,
wrong workspace, token/claim audit content, issuer/tenant mismatch acceptance,
or unavailable password recovery.

## Rollback

Set `MICROSOFT_ENTRA_SSO_ENABLED=false` and `SSO_ENABLED=false`, restart, revoke
the non-production client secret, and verify password recovery. No data
migration exists. Preserve users, memberships, sessions, and append-only audit
evidence; any cleanup or session revocation is a separately authorized action.

## Current blocker

No named Entra tenant, single-tenant app registration, vaulted client
credential, or registered non-production redirect URI has been supplied. This
runbook and the preflight make those prerequisites verifiable; they do not
authorize or perform activation. Entra remains committed off.
