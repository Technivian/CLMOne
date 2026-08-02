# ADR-0018: PayrollMinds pilot production topology

**Status:** Proposed
**Date:** 2026-08-02
**Owner:** Repository owner (`@haroonwahed`)
**Affected Charter sections:** Active Charter §16
**Related PDRs:** PDR-0010
**Related exceptions:** None

## Context

The existing `render.yaml` is explicitly a free, demo-only Blueprint. It is
not durable production infrastructure: it starts a demo seed at boot and does
not define workers, cron, backups, restoration evidence, a customer domain,
or an operator-owned secret store. The PayrollMinds readiness report records
PM-OPS-01, PM-OPS-02, PM-SEC-04, and PM-SEC-05 as unresolved blockers.

The application is a Django modular monolith with PostgreSQL, private
S3-compatible document storage, database-backed background jobs, and
production setting guards. Replacing that stack is not necessary to prepare a
bounded pilot and is not authorized by this record.

## Decision

Propose an isolated, paid PayrollMinds pilot topology on the existing Render
deployment family, using its Frankfurt region where the selected service
supports it. The topology has separate development, pre-production, and
production accounts/projects or equivalent hard isolation; distinct databases,
Redis instances, object-storage buckets, secret sets, domains, and service
identities; and no production demo seeding.

The production candidate consists of a web service, a continuous background
worker, scheduled dispatch/daily jobs, managed PostgreSQL with TLS required,
private released-object and quarantine-object stores, an EU-capable
transactional-email provider, and operator-configured logging/error-reporting
sinks. Email ingestion remains disabled; enabling it requires a separately
approved design and operational evidence.

This ADR is a target design and operator checklist only. It does not provision
resources, create DNS records, add a public domain, inject secrets, deploy a
release, enable email ingestion, or authorize real data.

## Alternatives considered

### Continue using the free demo Blueprint

Rejected. It is documented as demo/evaluation-only and cannot provide the
durability, worker, cron, backup, or isolation evidence required for the pilot.

### Replace the modular monolith or change hosting provider

Rejected for this pilot. No demonstrated blocker requires a stack replacement.
Any later provider or architecture change requires a separate ADR with a
migration, data-residency assessment, rollback plan, and rehearsal evidence.

### Enable forwarded email as an ingestion workaround

Rejected. The approved pilot excludes it; the sender/destination, quarantine,
idempotency, malware, retry/dead-letter, and audit controls are not proven.

## Consequences

### Positive

- Preserves canonical objects and existing production-setting safeguards.
- Makes EU-region selection, isolation, deployment, recovery, and ownership
  explicit before any activation.
- Keeps the production domain closed until the release gate is satisfied.

### Negative

- Requires paid operator-owned infrastructure and a named operator record.
- Requires a pre-production restoration drill before production access.

### Risks

- A provider's selected region alone does not prove every subprocessor or
  backup location is EU-only; the operator must obtain and retain that proof.
- Object-store IAM, SMTP, monitoring, and DNS/TLS configuration cannot be
  validated from source code.

### Migration

No schema, object, data, or application migration is introduced by this ADR.
Any release migration follows the migration/restore gate in the pilot runbook.

### Rollback

Do not reverse production migrations by default. Drain traffic, stop workers,
roll back code/config to the last known-good SHA, and restore the verified
pre-release database/object snapshot only under the documented incident
decision. Preserve audit and ingestion evidence.

## Security and privacy impact

Production credentials stay in the selected provider's secret manager, not
Git, `.env`, logs, issue text, or support tickets. Released and quarantine
storage must be private, encrypted, region-scoped, separately permissioned,
and accessed only through the application/worker identities. Production
activation remains blocked pending IAM, TLS, backup, privacy, and restoration
evidence.

## Data and audit impact

The deployment record must retain immutable release SHA, environment, operator,
backup/restore identifiers, migration output, health result, and rollback
decision. It must not contain credentials, document bodies, or customer data.

## Test evidence required

- exact-SHA green CI and production configuration gate;
- isolated pre-production migration plus tenant/audit verification;
- database and object-store restoration drill within agreed RPO/RTO;
- TLS/domain, worker heartbeat, email delivery, logging/error sink, and alert
  delivery evidence;
- no-public-access, encryption, and least-privilege IAM evidence; and
- customer support, export, offboarding, and deletion tabletop evidence.

## Approval

This record is Proposed. Approval and any production activation require the
applicable GitHub review/release record and named-environment operator evidence.
