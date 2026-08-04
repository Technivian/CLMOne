# ADR-0019: PayrollMinds AI provider disabled boundary

**Status:** Proposed
**Date:** 2026-08-02
**Owner:** Repository owner (`@haroonwahed`)
**Affected Charter sections:** Active Charter §16
**Related PDRs:** PDR-0012
**Related exceptions:** EXC-0002

## Context

The readiness report requires AI to remain disabled for launch. Existing OCR
background processing could invoke clause extraction without a requesting
human, and route middleware previously relied on the global provider flag.
Neither arrangement proves approved use case, authorized context, data
classification/redaction, provider retention, or canonical suggestion fields.

## Decision

Propose a fail-closed boundary for controlled-pilot mode: deny all external-AI
routes server-side regardless of the global provider flag, and do not submit
OCR text to a provider from background processing. Retain the existing
environment and workspace controls as defense in depth. Local deterministic
metadata hints and manual entry remain provider-free.

## Alternatives considered

### Enable clause extraction behind the workspace toggle

Rejected. It is advanced clause review, not the bounded metadata-suggestion
use case, and cannot provide the required durable field-level governance.

### Rely only on `GEMINI_AI_ENABLED=false`

Rejected. Configuration drift could re-enable egress, and direct view calls do
not necessarily traverse middleware.

## Consequences

### Positive

- Prevents unattended provider submission and accidental controlled-pilot AI
  enablement.
- Keeps manual metadata completion functional after a disabled/unavailable
  provider.

### Negative

- PayrollMinds does not receive external AI suggestions during the pilot.

### Risks

- A future non-pilot route may need a separate approved context-builder and
  durable canonical suggestion implementation.

### Migration

No schema or data migration. Existing data is neither transformed nor deleted.

### Rollback

Keep controlled-pilot mode enabled and provider configuration disabled. If a
future, separately approved enablement fails, re-enable this boundary by
setting `CONTROLLED_PILOT_ENABLED=true`, disable provider configuration, and
use manual metadata entry. Preserve documents, review records, and audit
evidence.

## Security and privacy impact

No PayrollMinds data is sent to an AI provider under the proposed boundary.
The guard operates after normal tenant/object authorization so denials do not
become an object-existence oracle. Logs must contain no document excerpt,
prompt, or provider response.

## Data and audit impact

No provider suggestion is created. Future activation must use canonical
records and immutable audit events rather than a parallel contract/document/
property/audit model.

## Test evidence required

- configured-provider controlled-pilot denial without provider invocation;
- workspace kill-switch denial without provider invocation;
- manual metadata fallback while provider configuration is present; and
- no unattended OCR provider invocation.

## Approval

This record is Proposed. Approval and any later provider activation require
the applicable GitHub review/release evidence and supplied data-processing
controls.
