# PDR-0012: PayrollMinds AI metadata-suggestion gate

**Status:** Proposed
**Date:** 2026-08-02
**Owner:** Repository owner (`@haroonwahed`)
**Affected Charter sections:** Active Charter §16
**Related ADRs:** ADR-0019
**Related exceptions:** EXC-0002

## Problem

The launch-readiness report identifies PM-AI-01: current Gemini configuration
is environment-wide and the repository has no complete durable canonical
metadata-suggestion record or supplied provider data-governance evidence.
The controlled pilot must not send PayrollMinds contract data to a provider
merely because a key is configured.

## Decision

Propose that controlled PayrollMinds pilot mode permit **no external AI use
case**. Manual metadata entry and deterministic local extraction hints remain
available. This is not approval for a provider, data transfer, user opt-in, or
production activation.

A later request may propose only field-level contract metadata suggestions;
it may not include autonomous legal decisions, clause/risk review, drafting,
negotiation, or any other advanced analysis. Each proposed suggestion must be
non-authoritative and individually accepted or rejected by a user authorized
to edit that Contract Record.

## Users and roles affected

Pilot users use the existing manual metadata path. Existing workspace
administrator policy controls remain able to disable AI outside controlled
pilot mode. No new role, permission, or approval authority is created.

## Lifecycle impact

Upload/OCR continues to a recoverable human-review/manual-entry state. It does
not create a provider suggestion or change the Contract Record. A future
suggestion must reference its immutable source document version and preserve
workspace/provenance.

## Permissions and access behavior

External context may be built only after the same server-side object-level
read decision as the corresponding human route. Unavailable authorization,
classification, source version, or redaction controls deny the provider call
without revealing restricted content or existence.

## Terminology

“Deterministic local hint” is not an AI-provider suggestion. “Authoritative
metadata” means a human-verified Contract Record value; no suggestion has that
status by itself.

## Alternatives considered

- Enable the existing clause-extraction route with an organization toggle:
  rejected for the pilot because it is advanced clause review and lacks the
  required durable metadata-suggestion and provider controls.
- Treat OCR output as AI metadata: rejected because local extraction does not
  establish AI provider provenance and must remain reviewable.
- Block manual entry after a provider failure: rejected because it makes AI a
  critical-path dependency.

## Consequences and trade-offs

The pilot sacrifices provider suggestions in exchange for preventing customer
data egress without an approved policy and evidence. Manual verification stays
available and is the supported recovery path.

## Migration and compatibility

No model, data, schema, role, permission, status, or lifecycle migration is
introduced. Existing provider-backed features outside controlled-pilot mode are
not approved by this PDR and are not a PayrollMinds launch capability.

## Acceptance criteria

Before a future enablement request:

1. an accepted canonical suggestion design records source document/version and
   location, provider/model/model version, policy version, confidence,
   suggestion, reviewer, per-field disposition, final value, provenance and
   immutable audit correlation;
2. provider DPA/retention/training/deletion/residency evidence is supplied;
3. server-side object authorization and classification/redaction are proven
   before retrieval and provider submission;
4. an authorized human accepts or rejects each field and every override is
   audited; and
5. negative access, provider failure, non-authority, logging minimization,
   deletion, and rollback tests pass on the reviewed immutable SHA.

## Metrics and evidence

Retain only content-free operational counts for denied provider calls and
manual fallback outcomes. Do not retain prompts, document excerpts, raw
provider responses, sensitive metadata, or identifiers in application logs.

## Approval

This is Proposed. Its status may change only through the applicable GitHub PR
review and CI evidence on the immutable reviewed SHA. Acceptance would not by
itself authorize provider configuration, data processing, or production
activation.
