# PayrollMinds AI extraction and data-governance gate

**Status:** Proposed operational record. It does not approve AI processing,
provider selection, customer data processing, production activation, or a
customer commitment.

## Current pilot decision

External AI is **not callable** in controlled-pilot mode. The server-side
contract AI resolver and the controlled-pilot middleware deny AI routes even
if an environment accidentally contains a provider key and
`GEMINI_AI_ENABLED=true`. OCR processing extracts local text only; it does not
submit contract text to an external provider in a background job.

This is the smallest safe response to PM-AI-01 in the launch-readiness report:
there is no approved canonical durable metadata-suggestion implementation, no
accepted object-level AI-context policy, and no supplied provider retention,
training, deletion, residency, or DPA evidence. It is not a finding that a
particular provider has unsafe practices; no provider is approved or configured
for this pilot.

The available path is manual metadata entry and verification. The existing
local `agreement_metadata_extract` preview may offer deterministic document or
filename hints, but it is not an AI-provider use case, creates no authoritative
fact, and does not call a provider. A missing or unreadable extraction leaves a
clear manual-review state; it never blocks a user from entering metadata.

## Enforced boundary

| Control | Pilot behavior | Evidence / recovery |
|---|---|---|
| Callable use cases | None for external AI. Clause extraction, clause suggestion, drafting, review, and assistant routes are out of scope. | Controlled-pilot route and resolver denials; continue with manual metadata. |
| Authorized context | No contract, document, search result, or metadata is sent to a provider. | OCR background processing has no provider call. |
| Suggestions | No provider suggestion is persisted or presented. | A future enabled suggestion needs the PDR/ADR acceptance criteria below. |
| Authority | A user-entered value remains authoritative only through the existing human review/contract action path. | No AI output can update contract metadata in this pilot. |
| Workspace disablement | `OrgPolicy.ai_features_enabled` remains the existing workspace administrator kill switch outside controlled-pilot mode. Controlled-pilot mode is stricter: it is always off. | A disabled policy returns a recoverable, provider-free response. |
| Failure and retry | Provider processing returns a content-free message directing the user to manual entry. | No document, prompt, or provider detail is returned or logged. |
| Logging | Do not log document text, quoted clauses, prompts, or provider response content. | The clause extraction diagnostic no longer logs an excerpt. |

## Data processing, retention, training, and deletion

No external provider is configured for the controlled pilot, so no pilot
contract data, metadata, prompts, source locations, or identifiers should be
sent, retained, used for training, or deleted by an AI provider.

Before any future activation, the responsible owner must retain evidence for:

1. provider identity, model and model-version behavior;
2. contractual data-processing terms, subprocessor and region information;
3. retention duration, training/feedback opt-out, and prompt/output deletion;
4. deletion request handling and evidence, including backed-up data; and
5. an approved data-classification and redaction map for every submitted field
   and document region.

An unknown or unavailable control fails closed. A provider error is not a
reason to bypass authorization, omit review, or send a broader document.

## Future enablement gate — not approved

Only a narrowly defined metadata-suggestion use case may be proposed for a
later pilot iteration. Advanced clause review, legal/risk conclusions,
autonomous decisions, drafting, negotiation, and broad document analysis are
excluded.

For each future suggestion, the canonical durable record must include the
workspace and provenance, source `Document`/immutable `DocumentVersion`, a
source location where available, use case and policy version, provider, model
and model version, timestamp, supplied confidence, suggested value, human
reviewer and disposition, final authoritative value, and immutable audit
correlation. A suggestion remains non-authoritative until an authorized human
accepts or rejects the individual field. Overrides must likewise be auditable.

The design must apply object-level authorization before constructing any AI
context and must fail closed for a missing classification, source location,
policy decision, or provider control. It must add access-control, non-authority,
failure-path, audit, and deletion tests before an activation request.

## Pilot rollback

Keep `CONTROLLED_PILOT_ENABLED=true` and `GEMINI_AI_ENABLED=false` in the
pilot environment. If a provider key or an AI feature is enabled accidentally,
the server-side controlled-pilot guard still denies the request; remove the
key/disable the environment flag and restart under the normal configuration
change procedure. Do not delete contract records, OCR review records, document
versions, or audit evidence as part of this rollback.
