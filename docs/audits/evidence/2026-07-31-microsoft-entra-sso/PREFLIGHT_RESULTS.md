# Microsoft Entra synthetic activation preflight results

**Result:** PASS

**Implementation head:** `fcf0487da784be378b6ebb17a8fafaec7541433a`

**Merged implementation:** `2b493ff6f486dac801464bb63eb07834ad733899`

**Named environment:** `entra-synthetic-preflight-2026-07-31`

**Workspace:** disposable `synthetic-entra-preflight`

**Identity data:** synthetic only

## Result

The read-only `verify_microsoft_entra_activation` command passed every
boolean check for a disposable pre-provisioned OIDC workspace and an exact
synthetic HTTPS callback. It proved:

- exact single-tenant UUID and discovery endpoint shape;
- SSO and Entra process flags enabled only for the probe;
- JIT account creation and access-token storage disabled;
- nonce, RS256, TLS verification, and minimized scopes enabled;
- explicit workspace and email-domain allowlists;
- active OIDC workspace with an active, pre-provisioned, unique identity;
- exact canonical callback URI; and
- client ID and secret present without emitting either value.

The command's captured output contained only named boolean checks and the
overall readiness boolean. A second invocation compared organization,
membership, user, and audit counts before and after and returned
`zero_mutation=true`.

## Restoration and limits

The process-scoped probe ended and an explicit rollback-state check returned
both `MICROSOFT_ENTRA_SSO_ENABLED=false` and `SSO_ENABLED=false`. The committed
defaults remain off.

This was not a Microsoft login, network call, tenant registration, application
registration, credential-vault operation, redirect registration, deployed
activation, or production test. The synthetic tenant/client/secret values were
placeholders and the disposable SQLite database was moved to Trash.

Real non-production activation remains blocked until the owner supplies a
named Entra tenant and environment, a single-tenant app registration, a vaulted
credential, the exact registered callback, approved synthetic identities, and
identity activation authority. Production and real PayrollMinds identities
remain unauthorized.
