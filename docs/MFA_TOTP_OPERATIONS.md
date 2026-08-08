# Authenticator-app MFA operations

**Status:** Implemented, committed default-off; no production activation is
authorized by this document.

## Control boundary

CLM One now supports RFC 6238 authenticator-app codes as a stronger local MFA
factor. The canonical owner remains `UserProfile`; no second identity or MFA
model is introduced. Factor secrets are encrypted at rest, never written to
audit evidence, and are shown only during authenticated enrollment. Successful
time-steps are consumed atomically so the same code cannot be replayed.

Existing email-code enrollment remains compatible while
`MFA_TOTP_ENROLLMENT_ENABLED=false`. An already-confirmed authenticator factor
continues to verify if enrollment is switched off, preventing a flag rollback
from locking out enrolled users. Entra/SAML MFA assurance remains a separate,
fail-closed federated path.

## Configuration

Committed defaults:

```text
MFA_TOTP_ENROLLMENT_ENABLED=false
MFA_TOTP_ENCRYPTION_KEY=
MFA_TOTP_ENCRYPTION_PREVIOUS_KEYS=
MFA_TOTP_ISSUER=CLM One
MFA_RATE_LIMIT_REQUESTS=8
MFA_RATE_LIMIT_WINDOW_SECONDS=300
```

Generate the primary key in an approved secret-management environment with
`cryptography.fernet.Fernet.generate_key()`. Store it in the deployment vault;
never place it in GitHub, a PR, logs, screenshots, support messages, or an
operator record. Production settings refuse TOTP enrollment without a valid
vaulted key.

Enabling `Organization.require_mfa` changes an identity policy and is not
authorized by the code flag. It requires the applicable exact-SHA CI/review and
operator/release evidence before use. Microsoft Entra activation still
requires the named PayrollMinds tenant, app registration, vaulted application
credential, redirect registration, assurance policy, and separate approval.

## Verification evidence

Before any named non-production activation, record for the unchanged reviewed
SHA:

- focused TOTP, legacy email-MFA, SAML assurance, session and rate-limit tests;
- migration and rollback review;
- secret-free configuration verification;
- QR/manual enrollment, recovery-code storage and one-time display;
- invalid, expired, replayed and malformed-secret failure paths;
- tenant-attributed append-only enrollment and challenge audit events; and
- accessibility and browser verification of enrollment and challenge pages.

Production additionally requires independent Product, Engineering and Security
review (or an explicit scope-specific owner decision allowed by the active
Charter), a release record, named environment, support/recovery procedure and
incident ownership.

## Abort and rollback

1. Set `MFA_TOTP_ENROLLMENT_ENABLED=false` to stop all new authenticator
   enrollment.
2. Keep `MFA_TOTP_ENCRYPTION_KEY` available. Removing a key does not disable
   MFA; it makes confirmed factors unverifiable and can lock users out.
3. Existing confirmed factors continue to verify. Users may use a saved
   single-use recovery code if their authenticator is unavailable.
4. Do not reverse migration `0117` while any confirmed TOTP factor exists.
   Database rollback is safe only after a reviewed factor inventory proves the
   fields are empty and affected sessions have a recovery path.
5. Preserve audit events. Never delete security evidence as rollback.

For key rotation, set a new primary `MFA_TOTP_ENCRYPTION_KEY` and retain the
superseded key in `MFA_TOTP_ENCRYPTION_PREVIOUS_KEYS`. A successful enrollment
confirmation or challenge re-encrypts the factor with the primary key. Keep
previous keys vaulted until an operator inventory proves no factor still
depends on them.

## Remaining production boundary

This implementation closes the local authenticator-factor gap. It does not
activate MFA for PayrollMinds, connect Entra, retire passwords, provision users,
change workspace membership, or establish production readiness for payroll
data. Passkeys/WebAuthn remain unimplemented.
