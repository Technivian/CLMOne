# PDR-0009: Governed contract import execution and compensation boundary

**Status:** Proposed — planning decision only; not implementation authority.  
**Date:** 2026-07-28  
**Owner:** Contracts Repository roadmap R1  
**Affected Charter sections:** Repository evidence and release control; access and audit  
**Related PDRs:** PDR-0002, PDR-0003, PDR-0008  
**Related roadmap:** `docs/roadmap/REPOSITORY_FIVE_OF_FIVE_ROADMAP.md` (R1)

## Problem

An empty, private workspace needs a governed way to create canonical Contract
Records from a synthetic CSV inventory. The current preview intentionally
validates without writing. A direct write would otherwise have no durable
batch identity, idempotency key, bounded compensation path, or auditable
connection between the reviewed preview and created records.

## Proposed decision

A separately authorized R1 implementation may introduce one additive,
tenant-owned **contract import batch** owned by Contract Records. It is an
execution envelope, not a second Contract, Entity, Document, or workflow
object. It records a content-minimized input digest, opaque correlation ID,
actor, preview summary, commit outcome, and links only to the Contract Records
created by that batch.

The allowed path is:

1. An owner or administrator obtains a non-mutating preview.
2. The same authorized actor explicitly confirms the unchanged preview digest.
3. The service creates new same-workspace Contract Records only, through the
   existing lifecycle and provenance services.
4. A repeat of the same committed digest is idempotent; it returns the prior
   batch outcome and never creates duplicates.
5. Compensation is explicit and only applies to unchanged records created by
   that batch. It uses the canonical lifecycle path to archive those records;
   it never deletes, overwrites, or rewrites independent later changes.

No document, document version, Entity, Counterparty record, key-date reminder,
external integration, AI/OCR output, sharing, role, permission, or automatic
processing is created by this slice. `owner_email` may resolve only to exactly
one active member of the same workspace.

## Users and roles affected

Only the existing workspace owner/administrator predicate may preview, commit,
inspect, or compensate a batch. An ordinary member receives a generic
no-access result. This record proposes no role, permission, or privilege
change.

## Lifecycle impact

Every imported Contract Record is created through the existing canonical
status/stage resolution and immutable provenance path. A batch does not change
workflow execution, approval, signature, or contract lifecycle semantics.
Compensation is an auditable archival action, not deletion or historical
rewriting.

## Permissions and access behavior

All batch and Contract queries are tenant-scoped. Duplicate detection uses
only title/counterparty values in the active workspace. Errors, confirmations,
audit summaries, and response bodies must not disclose another workspace's
records or contents. The import surface remains private and default-off until
its applicable release gate is met.

## Terminology

- **Preview:** non-mutating validation result.
- **Import batch:** the proposed durable execution envelope and correlation
  boundary for one confirmed input digest.
- **Compensation:** governed archival of eligible batch-created records; never
  deletion, overwrite, or restoration of prior data.

## Alternatives considered

### Write directly from the preview endpoint

Rejected. It has no durable execution identity, confirmation binding,
idempotency, or bounded compensation evidence.

### Delete records to undo an import

Rejected. It destroys evidence and could remove records changed after import.

### Create a new contract or entity model for imports

Rejected. `Contract` remains the canonical record, and entity ownership is
outside R1.

## Consequences and trade-offs

The implementation is deliberately narrower than a general migration tool:
it is create-only, synthetic-data-only, and has no documents. It adds durable
batch metadata and tests, but avoids a parallel records model and preserves
audit history. Larger source mapping, external sources, resume/retry, entity
resolution, and real-data migration require later decisions.

## Migration and compatibility

Any implementation must use an additive, reversible migration. It must not
backfill or alter historical Contract Records, legacy imports, audit rows, or
existing APIs. The feature must ship disabled by default; rollback disables
new commit/compensation paths while retaining batch and audit evidence.

## Acceptance criteria

- Preview remains non-mutating, tenant-scoped, and content-minimized.
- Commit requires an explicit preview digest confirmation and is create-only.
- Lifecycle, provenance, contract type, owner, and key-date mapping use their
  existing canonical services and validation.
- Same-digest retries are idempotent; duplicate, malformed, cross-tenant, and
  stale-preview attempts cannot create or reveal records.
- Each material outcome emits append-only, content-minimized audit evidence
  under the batch correlation ID.
- Compensation archives only unchanged records created by the named batch;
  changed, foreign, missing, or ineligible records are preserved and reported
  without leaking data.
- Tests cover authorization, tenant isolation, dry-run non-mutation, mapping,
  lifecycle/provenance, duplicate handling, repeat submission, audit-chain
  behavior, compensation eligibility, default-off behavior, and rollback.

## Metrics and evidence

Operational evidence is content-free: batch outcome category, coarse row
counts, policy/audit outcome, correlation ID, and rollback result. It excludes
CSV rows, filenames, contract titles, counterparties, owner emails, and
document content. Any non-production observation requires the reviewed SHA,
green CI, reversible default-off controls, abort/rollback evidence, and a
named-environment operator record.

## Approval

This is a Proposed planning decision. It may become binding only through the
applicable GitHub PR review and CI evidence on the immutable reviewed SHA.
Acceptance defines the R1 import boundary; implementation and activation still
require the applicable release gate and must not infer authority from a feature
flag or this document.
