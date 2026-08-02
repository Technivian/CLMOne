# PayrollMinds deployment and rollback runbook

**Status:** Proposed operator procedure. It is not authorization to deploy or
open public production access.

## Release preconditions

- Approved immutable release SHA and applicable GitHub release evidence.
- Exact-SHA green CI; no unresolved launch-readiness blocker.
- Pre-production uses separate resources and passes the approved synthetic
  pilot journey, access/revocation, export, audit, worker, and email tests.
- Fresh verified database and released/quarantine object-store backups exist.
- A restoration drill has passed in pre-production and its evidence is linked.
- The custom domain/TLS, monitoring, error reporting, and on-call/support
  routes are configured but production traffic remains closed.
- AI, forwarded email ingestion, external portals, and unsupported
  integrations are confirmed disabled.

## Deployment procedure

1. Record release SHA, approver, operator, environment, change window, backup
   identifiers, migration list, expected worker/scheduler versions, and
   rollback owner in the release record.
2. Confirm production configuration without printing values:

   ```bash
   python manage.py check --deploy --fail-level WARNING
   python manage.py migrate --check
   python manage.py audit_null_organizations
   python manage.py verify_audit_chain
   ```

3. Drain production traffic and pause worker claims. Do not delete queue,
   document, quarantine, or audit rows.
4. Take and verify a new PostgreSQL custom-format backup and object-storage
   recovery point. Record the opaque backup identifiers and timestamps.
5. Deploy the approved artifact/SHA to the web, worker, and scheduler services.
   Never use the demo seed command in a pilot production start command.
6. Run `python manage.py migrate --noinput`, followed by the commands in step
   2. A migration failure or audit-chain/tenant failure is a stop condition.
7. Start the worker and schedulers. Confirm a fresh `ScheduledJobRun`, queue
   claim, and `/_health/?format=json` database/scheduler result. Review logs
   and error-reporting sink for startup exceptions.
8. Run authorized synthetic smoke checks for login/session, private upload
   quarantine path when separately approved, owner access, denied cross-workspace
   access, search/count non-leakage, dates/reminders, download, and export/audit.
9. Only the named release authority may decide whether to enable the public DNS
   or traffic route. This task performs no such action.

## Migration rules

Every release uses a forward migration plan. Before applying a migration,
identify whether it is reversible; for destructive or data-transforming
migrations, use a tested restore/compensating plan rather than assuming a
reverse migration is safe. Record the schema state and post-migration tenant,
provenance, and audit checks.

## Rollback triggers

Immediately stop the release on migration failure, health degradation,
cross-workspace or unauthorized access, audit-chain failure, worker duplicate
execution, unexpected email delivery, storage exposure, error spike, or failed
smoke test.

## Rollback procedure

1. Close public traffic, stop worker/scheduler claims, and preserve logs,
   audit events, queue/dead-letter rows, and quarantine evidence.
2. Classify the failure: configuration-only, code-only, schema/data, or
   security incident. Notify the incident owner and support route.
3. For configuration/code-only failures, roll the affected services back to
   the last known-good immutable SHA/configuration and run the health, tenant,
   audit, and authorized smoke checks.
4. For schema/data failures, do not automatically run a reverse migration.
   Restore the verified pre-release PostgreSQL backup into an isolated restore
   target, verify it, then perform the approved cutback/restore procedure.
   Restore object storage consistently with the database snapshot and verify
   document hashes through authorized downloads.
5. Re-enable workers only after reconciliation of `BackgroundJob`,
   `ScheduledJobRun`, audit, document-version, and ingestion-attempt state.
6. Record release/rollback timestamps, SHA, backup identifiers, commands,
   outcomes, customer impact, and follow-up. Do not record secrets or content.

No deployment or rollback is complete until `/_health/?format=json`, tenant
integrity, audit-chain verification, and the designated smoke checks pass.
