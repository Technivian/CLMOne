# PayrollMinds production environment-variable inventory

**Status:** Proposed. This inventory names configuration only; it contains no
values, resource identifiers, endpoints, domains, or credentials.

Production values are injected by the selected platform's secret manager into
the web, worker, and scheduler services. Non-secret configuration may be
versioned only when it cannot identify a customer resource or enable access.

| Group | Variables | Handling and control |
|---|---|---|
| Runtime | `DJANGO_ENV`, `DJANGO_DEBUG`, `BUILD_SHA`, `APP_BASE_URL`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DEFAULT_FROM_EMAIL`, `OPERATOR_ALERT_EMAIL` | production must boot fail-closed; exact domain only; `DJANGO_DEBUG=false` |
| Session/TLS | `DJANGO_SECRET_KEY`, `SESSION_COOKIE_NAME`, `SESSION_IDLE_TIMEOUT_MINUTES`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`, `SECURE_REFERRER_POLICY` | secret manager for signing key; TLS termination and HSTS verified before public access |
| Database | `DATABASE_URL`, `DB_SSL_REQUIRE`, `DB_CONN_MAX_AGE` | secret manager; dedicated PostgreSQL; TLS required; no SQLite bypass |
| Released storage | `MEDIA_STORAGE_BACKEND`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_ACL`, `AWS_SIGNED_URL_EXPIRE` | private encrypted store; least-privilege identity; signed URLs only |
| Quarantine | `DOCUMENT_QUARANTINE_STORAGE_BACKEND`, `DOCUMENT_QUARANTINE_BUCKET_NAME`, `DOCUMENT_QUARANTINE_REGION_NAME`, `DOCUMENT_QUARANTINE_ENDPOINT_URL`, `DOCUMENT_QUARANTINE_ACCESS_KEY_ID`, `DOCUMENT_QUARANTINE_SECRET_ACCESS_KEY` | separate private store/identity; no public route; required only when approved ingestion enforcement is activated |
| Cache/jobs | `REDIS_URL`, `REMINDER_SCHEDULER_EXPECTED_INTERVAL_MINUTES`, `REMINDER_SCHEDULER_STALE_MULTIPLIER` | dedicated environment endpoint; worker and schedulers use same production instance only |
| Transactional email | `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | provider secret injection; outbound only; sandbox/verified sender before activation |
| Error reporting | provider DSN/token and environment/release identifiers, if a provider is selected | separate secrets; redact PII, documents, tokens, and request bodies; no provider selected by this PR |
| Optional integrations | `GEMINI_AI_ENABLED`, `GEMINI_API_KEY`, `SSO_ENABLED`, OIDC/SAML values, e-signature and CRM values | remain disabled/empty unless separately approved and evidenced |
| Explicitly prohibited | `ALLOW_SQLITE_IN_PRODUCTION`, `ALLOW_EPHEMERAL_MEDIA_IN_PRODUCTION`, email-forwarding enablement values | absent. Any emergency bypass needs a proposed/approved exception with owner, expiry, safeguards, and exit plan |

## Rotation procedure

1. Open an operator change record naming the secret class, owner, environment,
   reason, planned window, dependent services, and rollback action—never the
   secret value.
2. Create the replacement in the provider's secret manager and update the
   affected service references. Keep the prior credential valid only for the
   shortest provider-supported overlap.
3. Restart or roll the dependent web/worker/scheduler services, invalidate
   sessions when rotating `DJANGO_SECRET_KEY`, and verify `/_health/?format=json`.
4. Exercise the smallest safe path: authenticated login, one authorized signed
   download, one transactional-email sandbox delivery, and one worker heartbeat
   where relevant.
5. Revoke the former credential, record the redacted result and timestamps,
   and confirm no value appeared in logs, CI, tickets, or this repository.

The legacy repository-wide secret inventory contains historical entries and is
not production evidence for this pilot. A new operator-maintained inventory
must be created in the selected secret manager before activation.
