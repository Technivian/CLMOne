# PDR-0011: PayrollMinds controlled pilot scope and governance

**Status:** Proposed
**Date:** 2026-08-02
**Owner:** To be designated by the Product Owner
**Affected Charter sections:** 16 Repository evidence and release control
**Related ADRs:** ADR-0016, proposed ADR-0017
**Related exceptions:** proposed EXC-0001
**Related policy:** PDR-0008 remains Proposed and separately governs any future object-level read implementation.

## Problem

PayrollMinds requires a sharply bounded path from synthetic demonstration to a
possible controlled production pilot. The readiness assessment identifies
critical gaps in object-level access, quarantine-first ingestion, release
identity, operational evidence, test health and privacy evidence. Without a
governed scope, the pilot could become an unapproved enterprise release or
silently introduce real payroll/employee data, AI, integrations or permissions.

## Decision

Propose a 30-day, single-workspace controlled pilot with the boundary defined
in `docs/pilots/payrollminds/`. The target outcome is governed contract
ingestion, provenance, human metadata verification, private authorized access,
dates/reminders and audit evidence; it is not broad product activation.

The proposed operating limits are: one isolated workspace; up to 10 named
users; up to 50 initial records; three agreement types (MSA, Order
Confirmation and Mutual NDA); manual/bulk browser ingestion only; contract
documents and minimum contract metadata only; and a named launch owner plus
one support channel before activation.

AI, email forwarding, external users, e-signature, SAML/SCIM, integrations,
advanced negotiation and analytics are excluded. Raw payroll, salary,
employee/worker bulk, bank, tax, benefits, credential and special-category
data are prohibited. Retention, deletion, export, offboarding, data location
and subprocessor commitments remain preconditions to real-data activation,
not assumptions that this record can approve.

No pilot is activated unless the proposed Go/No-Go Checklist is satisfied on
an immutable reviewed SHA and the active Charter’s required review and release
evidence exists. The pilot remains stopped on any charter stop condition.

## Users and roles affected

Uses existing `OWNER`, `ADMIN` and `MEMBER` workspace roles only. It introduces
no role, permission, workflow responsibility or authority. Membership is
necessary but not sufficient for protected reads; any implementation must
satisfy the separately approved object-read policy.

## Lifecycle impact

Imported documents may create durable contract records without an originating
workflow instance only with mandatory, immutable provenance. Existing contract,
document, verification, deadline, reminder and audit lifecycles remain
authoritative. No new lifecycle stage or status is introduced.

## Permissions and access behavior

Pilot access must be private by default and enforced server-side for records,
documents, search, counts, reminders, exports and any future AI context. This
PDR does not authorize a runtime authorization change. It requires PDR-0008’s
policy/implementation path and the required independent release authority
before activation.

## Terminology

Use **workspace**, **contract record**, **document version**, **provenance**,
**workspace role**, **workflow responsibility**, **human verification** and
**controlled export** as defined in canonical documentation. “Pilot” means the
bounded operational proposition in this record, not an approval state.

## Alternatives considered

### Continue the synthetic design-partner demonstration

Retains low risk but does not test controlled real-data operation. It remains
available as a separate non-production proposition.

### Activate broad enterprise functionality

Rejected. It conflicts with the readiness report and bypasses unresolved
authorization, ingestion, privacy and operations gates.

### Activate a membership-only multi-user workspace

Rejected. Workspace isolation is not object-level private access and does not
meet the active security/privacy requirements.

## Consequences and trade-offs

The proposal deliberately sacrifices breadth for a traceable, reversible
contract-record journey. It requires operational preparation before customer
data, delays AI/integrations and prevents a feature flag from being treated as
authority. It does not make any commercial, support, retention or customer
commitment.

## Migration and compatibility

This planning record creates no migration, runtime flag, model, data backfill,
permission change or deployment. Future approved implementation must be
additive/reversible and include a migration/compensating-action plan.

## Acceptance criteria

- The charter, scope, classification, role/access, success, risk and checklist
  documents are internally consistent with active governance.
- No prohibited data or excluded capability is described as approved.
- Each real-data gate names evidence and an accountable human role without
  inventing a person, commitment or approval.
- PDR-0008 and ADR-0016 are referenced rather than duplicated or overridden.
- Approval occurs only through the applicable GitHub review and immutable SHA
  evidence, with a separate operator/release record where required.

## Metrics and evidence

See `SUCCESS_CRITERIA.md`, `RISK_REGISTER.md` and `GO_NO_GO_CHECKLIST.md`.
Evidence must identify the candidate SHA, environment, command/test or
operator action, outcome and date; it must not reproduce editable approvals.

## Approval

Proposed only. No approval, activation, named user, privacy term, support
commitment or customer acceptance is recorded in this PDR.
