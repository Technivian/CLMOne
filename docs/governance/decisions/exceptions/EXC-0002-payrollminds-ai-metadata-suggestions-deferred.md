# EXC-0002: PayrollMinds AI metadata suggestions deferred

**Status:** Proposed — not active and grants no deviation
**Owner:** Repository owner (`@haroonwahed`)
**Approval authority:** Not supplied; no approval is asserted
**Start:** Not started. The controlled-pilot guard is already fail-closed.
**Hard expiry:** No later than any request to activate AI provider processing;
the proposal cannot authorize operation before then.
**Affected Charter rule:** Canonical Data, AI, and Intelligence requirements
for governed, non-authoritative AI suggestions and human verification.

## Deviation

The pilot defaults describe AI metadata suggestions with human verification,
but that capability is deliberately deferred. No compensating external-AI
function is enabled.

## Scope

One future PayrollMinds workspace only. The exception does not apply to other
customers, environments, providers, routes, documents, or real data.

## Rationale

PM-AI-01 remains unresolved: there is no supplied provider retention/training/
deletion evidence, no accepted object-level AI context policy, and no complete
canonical durable metadata-suggestion record.

## Risks

Manual entry may take longer and users may receive fewer convenience hints.
Enabling an ungoverned provider to reduce that effort would create data-egress,
authorization, non-authority, and audit risks.

## Safeguards

- External AI routes are denied server-side in controlled-pilot mode.
- OCR jobs do not submit text to a provider.
- Manual entry and deterministic local hints remain available.
- Provider errors present a content-free manual fallback, not a bypass.
- Logs must not include document text, prompts, quotes, or provider output.

## Monitoring

Before any activation request, review the configuration inventory for
`CONTROLLED_PILOT_ENABLED=true` and `GEMINI_AI_ENABLED=false`, and retain the
negative-path test result. No customer-data or provider-operation monitoring is
expected because no provider processing is permitted.

## Exit plan

Expire this proposed exception without enabling AI, or replace it only after
PDR-0012 and ADR-0019 are accepted and their provider, authorization,
canonical-record, human-review, deletion, audit, rollback, and test evidence
is supplied. A new time-bounded exception is required for any approved
deviation; this proposal does not roll forward automatically.

## Resolution evidence

No approval or release evidence is supplied. This record remains Proposed.
