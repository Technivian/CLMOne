# PayrollMinds operations, monitoring, and support runbook

**Status:** Partially live. A real deployment exists (Render, Frankfurt —
see `TARGET_ENVIRONMENT_INVENTORY.md` §1c) and an Infrastructure operator
is named below, but no monitoring provider, alert route, or support
contact has actually been configured — `SENTRY_DSN` is confirmed unset on
the live deployment, and the failure-mode/alert tables below remain
documented design, not live, tested alerting.

## Service ownership

| Service/control | Accountable owner | Operator evidence required |
|---|---|---|
| Release and application runtime | Deployment Approver: **Haroon Wahed** — bootstrap assignment through 2026-09-30 | SHA, deployment, health, rollback record |
| PostgreSQL, Redis, storage, DNS/TLS, backup | Infrastructure operator: **Haroon Wahed** — confirmed 2026-08-08 as provisioning authority ("authorized to create production resources and run backup/restore drills") | region, IAM, encryption, backup/restore evidence |
| Access, audit, scanning, secrets, incident security decision | Incident Owner: **Haroon Wahed** — bootstrap assignment through 2026-09-30 | review, scan, rotation, incident evidence |
| Privacy, retention, deletion, export/offboarding | Privacy Owner: **Haroon Wahed** — bootstrap assignment through 2026-09-30 | approved retention/offboarding and customer terms |
| Customer communications and support | Support Owner: **Haroon Wahed** — bootstrap assignment through 2026-09-30 | approved support route, hours, escalation contacts |

The 2026-08-17 Owner decision names Haroon Wahed for the bootstrap roles
shown above; it does not represent them as independent authorities. Contact
addresses, support hours, RPO/RTO, customer promises, a customer-facing
support channel, and retention/offboarding terms remain absent until supplied
and approved. The assignments must be reviewed by 2026-09-30 or replaced
earlier by a qualified separate owner.

## Monitoring and alert inventory

| Signal | Source | Trigger | Initial response |
|---|---|---|---|
| Web availability | `/_health/` and `/_health/?format=json` | non-200/degraded | confirm database/scheduler state; close traffic if security/data risk |
| 5xx rate | structured request metrics | P1 at >=2%/5m; P2 at >=0.8%/15m | inspect release, logs, error sink; rollback if release-related |
| Core latency | route latency metrics | P1 p95 >1500ms/10m; P2 >800ms/15m | inspect DB/cache/worker saturation |
| Database health | health JSON and provider metrics | down/slow | protect writes, notify operator, assess restore point |
| Scheduler heartbeat | `ScheduledJobRun` and health JSON | stale for >2 expected intervals | inspect cron/worker and dead letters |
| Worker/dead letters | `BackgroundJob` and `review_dead_letter_jobs` | failed/dead-letter growth | stop unsafe retry loops; resolve/requeue only after cause known |
| Storage/ingestion | structured logs/audit and provider logs | access denial, scan failure, orphan/reconciliation mismatch | keep upload/release unavailable; investigate IAM/scanner |
| Auth/session | login metrics and audit | sustained login failures or anomalous revocations | verify identity provider, session key, rate limits |
| Export/download | immutable audit events | denied/failed spike or unusual volume | check authorization and incident triage |
| Transactional email | provider and application events | delivery/bounce/complaint failure | pause non-essential sends; protect support/recovery messages |

Logs must be structured and carry request/correlation, service, release SHA,
environment, status, latency, and safe actor/workspace references. They must
not carry passwords, tokens, raw DSNs, document content, raw filenames,
scanner payloads, or unredacted customer data. Error reporting must apply the
same redaction and restricted access before it is enabled.

## Failure-mode table

| Failure mode | Safe behavior | Detection | Recovery / stop condition |
|---|---|---|---|
| Web service unavailable | no partial request completion assumed | health check, 5xx alert, provider signal | close traffic; roll back to known-good SHA after investigation |
| PostgreSQL unavailable or slow | health becomes degraded; protect writes if integrity is at risk | health JSON, DB latency/error alerts | pause traffic/workers; use verified recovery plan, not an ad hoc database change |
| Redis/cache unavailable | metrics may degrade; no authorization bypass | service logs, cache/provider alert | investigate endpoint; verify auth/rate-limit behavior before continuing |
| Worker or scheduler stalled | jobs remain pending/retry/dead-letter; no duplicate claim | heartbeat, queue depth, `ScheduledJobRun` | restart only after cause review; reconcile stale `RUNNING` jobs |
| Storage/IAM failure | upload/release/download fails safely; objects stay private | provider event, application/audit event | stop affected ingestion/release path; repair least-privilege policy and re-test |
| Malware scanner/ingestion failure | quarantine remains unavailable; no canonical release | ingestion audit, worker alert | keep enforcement closed; do not bypass scanner/quarantine |
| Transactional email failure | no silent recipient substitution or retry storm | provider events, job failures | pause non-essential sends; validate sender and retry/dead-letter policy |
| Secret compromise or rotation failure | revoke/replace credential; sessions invalidated when signing key rotates | secret-manager/security alert, authentication errors | activate incident path; rotate and verify without logging values |
| Unauthorized access/export indication | preserve evidence and deny/close affected path | immutable audit, access-denial spike, customer report | security incident; close traffic if exposure is plausible; do not delete evidence |
| Bad release or migration | traffic remains closed until checks pass | deploy health, migration, tenant/audit smoke checks | code/config rollback or verified restore; never assume reverse migration is safe |

## Background jobs and email

- Continuous worker: `process_background_jobs --limit 200`, with one claim
  owner per job and existing retry/dead-letter behavior.
- Scheduler: `queue_background_jobs` at the approved cadence; lifecycle and
  retention jobs only at their approved cadence and scope.
- Observe `ScheduledJobRun`, worker logs, heartbeat, queue depth, retries, and
  dead letters. Do not use CI as evidence that production jobs ran.
- Transactional email is outbound-only. Verify sender/domain and recipient
  handling in pre-production before production. Forwarded email ingestion is
  disabled; no inbound mailbox, webhook, or destination is configured here.

## Incident and support route

1. Acknowledge alert, open an incident record, record the release SHA and
   correlation/request IDs, and classify availability, data, access, storage,
   job, email, or security impact.
2. For suspected tenant exposure, unauthorized export/download, malware,
   credential loss, or data corruption: close traffic or disable the affected
   path, stop workers if needed, preserve evidence, and escalate to Security
   and the release authority immediately.
3. Use the deployment/rollback runbook; do not delete audit, job, or quarantine
   evidence to recover service.
4. The customer support route must be a named, authenticated channel with an
   approved incident/escalation contact and response target before launch.
   Until supplied, customer support is a launch blocker, not an assumed email
   address.
