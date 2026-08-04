# ADR-0017: PayrollMinds isolated pilot release topology and evidence boundary

**Status:** Proposed
**Date:** 2026-08-02
**Owner:** To be designated by the Engineering owner
**Affected Charter sections:** 16 Repository evidence and release control
**Related PDRs:** PDR-0011, PDR-0008
**Related exceptions:** proposed EXC-0001
**Related ADRs:** ADR-0016

## Context

The repository’s current demo Blueprint automatically deploys `main`, seeds
demo data in the web-process start command and lacks dedicated worker/cron
resources. That shape is explicitly labelled evaluation-only. It cannot supply
the isolated environment, durable operations, explicit migration control,
backup/restore evidence or immutable reviewed-SHA deployment required for a
real-data controlled pilot.

The pilot must also keep untrusted document bytes quarantined under ADR-0016,
keep AI/email forwarding/integrations off, and avoid changing the canonical
domain model merely to create a deployment environment.

## Decision

Propose a dedicated, isolated pre-production and production topology for this
pilot. The topology must deploy an explicit immutable reviewed SHA, not an
unreviewed moving branch; separate web, worker/scheduler and migration
operations; use managed PostgreSQL, private durable object storage, private
quarantine storage, shared queue/cache, SMTP, monitoring/error reporting and
verified offsite backups; and remove demo seeding from production startup.

Production configuration is committed-default-off for excluded capabilities:
AI, email forwarding, external collaboration, signatures and unproven
integrations. Activation is limited to the named pilot workspace and cannot
alter authorization or create a customer record without the applicable
separate authority.

This is a topology and evidence proposal. It does not select a cloud provider,
store secrets, configure production infrastructure, introduce a model or
permission, or authorize a deployment/activation.

## Alternatives considered

### Continue using the evaluation Blueprint

Rejected for real data. Its automatic deployment, demo seed and missing
worker/cron resources do not meet the proposed pilot operations boundary.

### Run pilot jobs synchronously in the web process

Rejected. It reduces reliability, failure isolation and evidence for reminder,
quarantine and retention processing.

### Permit environment flags to decide activation

Rejected. Flags control exposure only and never grant the release authority
required by the active Charter.

## Consequences

### Positive

- Separates pilot operation from synthetic demonstration behavior.
- Supplies an auditable place to rehearse migration, backup, restoration,
  alerting, quarantine/release and rollback controls.
- Preserves default-off excluded capabilities and a narrow workspace boundary.

### Negative

- Requires infrastructure ownership, recurring operational cost and named
  support/incident responsibilities.
- Introduces deployment coordination before any customer data is accepted.

### Risks

- Misconfigured storage, queue, scanner or alerting could invalidate a gate.
- A deploy that differs from the reviewed SHA invalidates evidence.
- Incomplete operational ownership can turn a contained incident into data
  loss or prolonged denial of service.

### Migration

No migration is authorized by this ADR. A future deployment plan must back up,
restore-test and verify every approved migration on the intended candidate.

### Rollback

The future runbook must stop affected workers/ingestion, disable only approved
pilot exposure flags, restore the last known-good application release and use
the approved database compensating action. It must not re-enable a legacy
direct-to-canonical upload path or delete quarantined/released data outside
retention/legal-hold controls.

## Security and privacy impact

Secrets must remain in managed secret storage, never source control. Storage,
quarantine, database, queue and backups must be private, least-privilege and
tenant-aware. Production logs/metrics/errors must be content-minimized. This
ADR does not waive the separate data-classification, privacy, object-access or
ingestion requirements.

## Data and audit impact

Deployment, migration, backup, restoration, rollback, worker/scheduler and
quarantine activation evidence must identify environment, immutable SHA,
operator, time and outcome without recording sensitive content or secrets.

## Test evidence required

- production-profile configuration checks;
- isolated pre-production deploy and synthetic UAT;
- worker/scheduler, email failure/retry and alerting drills;
- private storage and quarantine access tests;
- backup and successful restoration drill;
- migration and rollback/compensating-action rehearsal;
- exact-SHA green CI and authorized deployment/operator record.

## Approval

Proposed only. No provider, environment, secret, deployment, customer-data
activation or release approval is supplied by this ADR.
