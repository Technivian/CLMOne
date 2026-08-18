# ADR-0020: PayrollMinds R2 daily document backup control

**Status:** Proposed — implementation evidence only; provider deployment and
first-run proof remain separately authorized.

**Date:** 2026-08-18
**Owner:** Repository owner (`@haroonwahed`)
**Affected Charter sections:** Active Charter §§12, 16
**Related PDRs:** PDR-0010, PDR-0013
**Related exceptions:** None

## Context

The isolated R2 recovery drill proves deletion isolation and byte-for-byte
restore integrity for a synthetic object. It does not ensure that newly added
or changed released documents are copied routinely to the separate recovery
bucket. The document-recovery gate is therefore blocked on an at-least-daily
backup control.

## Decision

Use one scheduled Cloudflare Worker, with no HTTP handler or public route:

- `PRIMARY_DOCUMENTS` binds `clmone-documents`.
- `BACKUP_DOCUMENTS` binds `clmone-documents-backup`.
- Cloudflare Cron invokes it once daily at `15 2 * * *` UTC.
- Every source version is copied to the reversible immutable key
  `_backup_versions/v1/<base64url(primary-key)>/<base64url(source-version)>`.
- The Worker never propagates deletes and never runs a delete operation.
- Immutable per-run records are written below `_backup_runs/`; the mutable
  `_backup_control/last-success.json` marker is changed only after a fully
  successful run.

R2 bindings, rather than repository-held access keys, provide access. The
control does not modify the Django runtime, document rows, contract types, R2
objects, or provider settings until a separately authorized operator deploys
it.

## Consequences

An earlier object version survives a later overwrite or primary deletion. Run
metadata gives the Infrastructure/Backup Owner a content-free operational
record, but is not a substitute for the quarterly SHA-256 restore drill.

Deployment must prove the two exact bindings, UTC Cron Trigger, a successful
controlled first run, a new synthetic-object backup, an immutable success
manifest, last-success update, unchanged primary, and retained earlier backup
object. Until then, the canonical status remains:

`DOCUMENT RECOVERY = BLOCKED — ROUTINE BACKUP DEPLOYMENT/PROOF PENDING`.

## Alternatives considered

- R2 lock/lifecycle rules alone: retention controls do not create an
  independent recovery copy.
- A mutable one-key mirror: later replacement or deletion would lose earlier
  recoverable versions.
- Django/Render scheduled work: it would couple backup credentials and backup
  execution to the application runtime instead of using scoped R2 bindings.

## Security and privacy impact

The Worker receives bucket-scoped bindings only. It has no public `fetch`
handler, route, repository-held R2 credential, or production application
credential. It copies streams directly between R2 bindings rather than
materializing document bodies in Worker memory. Run failure entries identify
objects by a truncated SHA-256 identifier and use safe errors rather than
document keys or contents.

## Data and audit impact

The Worker does not write application tables or application `AuditLog` rows.
It writes only recovery-bucket object copies, immutable per-run manifests, and
the last-success control marker after complete success. Provider deployment
and first-run evidence are separate operational records.

## Test evidence required

- local scheduled-event handling with Wrangler;
- new/changed-version copy, immutable-key, and source-accounting tests;
- stream-only body transfer and no-delete static guard;
- pagination, partial-failure manifest, and last-success failure tests;
- dependency/secret/whitespace and repository-required PR checks.

## Approval

This record is Proposed. Its review may approve repository implementation
evidence only. Cloudflare deployment, first-run proof, and any status change
to `DOCUMENT RECOVERY` require separate applicable authorization.
