# Document quarantine operations

**Status:** Proposed, default-off implementation. Do not use with real client or
PayrollMinds data until ADR-0016 is accepted and the applicable activation gate
is complete.

## Boundary

`DocumentIngestionService` stores untrusted bytes under the separate private
`quarantine` storage alias and records a tenant-scoped
`DocumentIngestionAttempt`. No canonical `Document`, immutable
`DocumentVersion`, OCR review, preview, AI output, search record, workflow
action, download, or share exists before a clean verdict and explicit release.

The existing `Document` and `create_document_version()` service remain the
canonical released-object owners. The attempt is technical security evidence,
not a second document model.

## Committed defaults

```text
DOCUMENT_QUARANTINE_ENFORCEMENT_ENABLED=false
DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED=false
DOCUMENT_QUARANTINE_RELEASE_ENABLED=false
DOCUMENT_QUARANTINE_PURGE_ENABLED=false
DOCUMENT_QUARANTINE_ENVIRONMENTS=
DOCUMENT_QUARANTINE_ORG_ALLOWLIST=
DOCUMENT_MALWARE_SCANNER_CLASS=
DOCUMENT_QUARANTINE_RETENTION_DAYS=0
DOCUMENT_QUARANTINE_STORAGE_BACKEND=filesystem
```

Production must use a private encrypted quarantine store outside the normal
media namespace, with a distinct least-privilege worker credential. Local
filesystem quarantine is outside `MEDIA_ROOT` and has no download URL.

## Activation prerequisites

Before even a non-production observation:

1. ADR-0016 is explicitly accepted in the authorizing PR review.
2. Required CI is green for the unchanged exact SHA.
3. A named non-production environment and workspace are allowlisted.
4. A named scanner is configured. The included adapter is
   `contracts.services.document_malware_scanners.ClamAVScanner`.
5. Private quarantine storage and least-privilege worker access are tested.
6. A positive quarantine retention period is approved.
7. Abort, rollback and operator-evidence owners are named.
8. Only synthetic files are used unless real-data authorization is separately
   granted.

Run the secret-free readiness check:

```bash
.venv/bin/python manage.py verify_document_ingestion_preflight \
  --organization-slug <workspace>
```

The output is boolean-only. It does not print scanner endpoints, storage keys,
credentials, filenames, content or provider responses.

## Lifecycle

1. `POST /contracts/api/documents/ingestion/` validates the member and target
   tenant, checks size, extension, byte signature and bounded DOCX structure,
   writes to quarantine, and scans.
2. Status is available only to an authorized same-workspace member at
   `/contracts/api/documents/ingestion/<correlation-id>/`.
3. Only `CLEAN` is releasable, and release also requires
   `DOCUMENT_QUARANTINE_RELEASE_ENABLED=true`.
4. `POST .../<correlation-id>/release/` creates the canonical private document
   through `create_document_version()`, then deletes the quarantine copy.
   Cleanup failure is recorded as `CLEANUP_PENDING`; it never deletes the
   released canonical record.
5. Malicious, unscannable, timeout, outage and malformed scanner results remain
   unavailable and create no canonical object.

When enforcement is active, the primary upload API and internal browser
create/version forms route new bytes into this lifecycle. Metadata extraction
preview returns a controlled unavailable response and never reads the bytes.
Legacy behavior remains unchanged while the committed gate is off.

## Retention and legal hold

Retention is dry-run by default:

```bash
.venv/bin/python manage.py run_document_quarantine_retention \
  --organization-slug <workspace>
```

The report contains content-free counts. Destructive expiry additionally
requires `DOCUMENT_QUARANTINE_PURGE_ENABLED=true`, a positive retention period,
active enforcement for the named workspace, and explicit `--execute`.

Active matter/client legal holds take precedence. Released canonical documents
are never deleted by the quarantine retention command.

## Abort and rollback

Set `DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED=true` to deny quarantine, scan,
preview and release without restoring direct-to-canonical ingestion. Then keep
release and purge off, preserve all attempt/audit rows, reconcile quarantine
storage, and resolve `CLEANUP_PENDING` or missing-object evidence manually.

Never delete an attempt row or audit evidence as rollback. Destructive storage
cleanup follows the approved retention and legal-hold process only.

## Audit evidence

Append-only events cover received, quarantined, scan started, verdict recorded,
release started, released, release failed, cleanup completed, expired and
retention blocked. Evidence includes workspace, correlation ID, digest, size,
detected media type, provider class, signature/version identifier, status and
outcome. It excludes filenames, titles, content, extracted text, raw scanner
output, detected signature names, tokens and credentials.
