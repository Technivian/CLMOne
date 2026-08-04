# EXC-0001: PayrollMinds temporary deferral of enterprise capabilities

**Status:** Proposed
**Owner:** To be designated by the Product Owner
**Approval authority:** Applicable Product, Engineering and Security authorities under the active Charter
**Proposed start:** On approved controlled-pilot activation; until then this exception is inactive
**Proposed hard expiry:** 2026-09-30
**Affected rule:** Delivery Roadmap stages 6–8 and the pilot’s requested capability boundaries; this exception does not waive mandatory security, privacy, audit, release or operational gates.

## Deviation

For the proposed 30-day PayrollMinds pilot only, defer AI, email forwarding,
external users/collaboration, e-signature, SAML/SCIM, broad integrations,
advanced negotiation and analytics. The pilot instead limits operation to the
approved contract-record journey in PDR-0011.

## Scope

One isolated PayrollMinds workspace, at most 10 named users and 50 initial
records, only after production approval. No other workspace, customer,
environment, service, record type or user obtains a benefit from this proposed
exception.

## Rationale

These capabilities are not necessary to validate the narrow pilot outcome and
do not have the required stable implementation, privacy, supplier, identity or
operational evidence for real-data activation.

## Risks

- Users may attempt workarounds outside CLM One when excluded capabilities are
  unavailable.
- Deferral may be misrepresented as acceptance of missing enterprise controls.
- A flag/configuration mistake could activate an excluded feature.

## Safeguards

- Excluded capability flags are committed/default-off and verified at
  preflight; AI and email forwarding remain disabled.
- Navigation and server routes for excluded capabilities remain unavailable to
  the pilot where supported; server-side controls prevail over UI hiding.
- Scope, data classification, support and stop conditions are communicated to
  named users before activation.
- Any request to enable an excluded capability stops the pilot change and
  follows the normal PDR/ADR/release process.

## Monitoring

The launch owner reviews feature configuration, user/record/type limits,
support requests and audit events at preflight and throughout the pilot.
Unexpected AI/provider calls, forwarding/integration traffic, external access,
signature activity or scope-limit breach triggers immediate stop.

## Exit plan

By the hard expiry, close/offboard the pilot or submit a separate proposed,
reviewed and approved expansion decision for each capability. Disable pilot
exposure, revoke access, complete approved export/retention actions and retain
operator/audit evidence. The exception may not be renewed implicitly.

## Resolution evidence

None supplied. This proposed exception is inactive until the authorizing
GitHub PR, immutable reviewed SHA, required CI and operator/release evidence
exist. It never permits bypass of object-level access, quarantine-first
ingestion, prohibited-data rules, retention/legal hold, audit integrity,
backup/restore, or production release controls.
