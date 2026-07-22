# PAR-ID-002 — ADMIN process-role reconciliation (residual)

**Status:** Future roadmap (residual from PAR-ID-001)  
**Priority:** P1  
**Opened:** 2026-07-22  
**Parent:** PAR-ID-001 **Closed**

## Problem

`UserProfile.Role.ADMIN` maps to `legacy_process_admin` with confidence **AMBIGUOUS** and was explicitly excluded from the first canonical resolver cutover. Workspace `OrganizationMembership.Role.ADMIN` remains a separate workspace role and must never be conflated. A dedicated product + security reconciliation is required before any ADMIN canonical authority.

## In scope (future authorization required)

- Disambiguate process vs workspace ADMIN semantics per org
- Decide target RoleDefinition code(s) and CERTAIN mapping (or permanent exclusion)
- Staging parity for ADMIN cases after mapping decision
- Separate threat review + activation votes if authority is proposed

## Out of scope

- Silent remap of workspace ADMIN → process ADMIN
- Privilege / permission expansion via labels
- Automatic repair of historical ADMIN assignments without authorization

## Dependencies

- PAR-ID-001 Closed (**met**)
- Product owner decision per org / policy
- Security advisory on escalation risk

## Acceptance (when authorized later)

- Explicit mapping or permanent exclusion recorded
- No AMBIGUOUS silent MATCH relabeling
- Tests + staging evidence + separate activation package if authority changes

## Evidence pointers

- [`PROCESS_ROLE_MAPPING_MATRIX.md`](PROCESS_ROLE_MAPPING_MATRIX.md) — ADMIN collision rule + first-cutover exclusion
- [`CANONICAL_RESOLVER_ACTIVATION_RESULTS.md`](CANONICAL_RESOLVER_ACTIVATION_RESULTS.md) — excluded-role counts during pilot
- [`RESOLVER_CUTOVER_THREAT_REVIEW.md`](RESOLVER_CUTOVER_THREAT_REVIEW.md) — T4 workspace/process ADMIN
