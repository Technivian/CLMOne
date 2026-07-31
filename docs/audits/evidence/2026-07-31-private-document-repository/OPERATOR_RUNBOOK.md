# Private document repository operator runbook

**Scope:** Existing authenticated document list, metadata search, detail,
version comparison, create/edit relationship choices, soft-delete lookup,
download, and manual OCR-review queue routes. This slice adds no document
model, storage backend, upload API, OCR/AI processing, external sharing,
identity integration, permission, credential, migration, or production
activation.

## Route-to-policy inventory

| Route / surface | Policy point | Protected output |
|---|---|---|
| `/contracts/documents/` | Document policy before query/search/pagination | Rows and empty/search results |
| `/contracts/documents/<id>/` | Document policy before object and version lookup | Metadata and version links |
| `/contracts/documents/<id>/compare/<other>/` | Policy applied independently to both versions | Comparison content |
| `/contracts/documents/new/` | Contract/client/matter choices filtered before form rendering and validation | Relationship names and identifiers |
| `/contracts/documents/<id>/edit/` | Document lookup and relationship choices filtered | Metadata and relationship options |
| `/contracts/documents/<id>/delete/` | Document policy before deletion service | Object existence |
| `/contracts/documents/<id>/download/` | Document policy before file state, audit, or signed URL | File existence, metadata, and URL |
| `/contracts/documents/ocr-queue/` and review route | Eligible document IDs applied before rows/lookups | Review state and extracted text |
| `/contracts/search/` | Contract/client/matter/document policy before filtering, ranking, and rendering | Global-search rows and zero-result behavior |

Active Ethical Walls are inherited through the document's canonical
`Contract`, `Client`, and `Matter` relationships. Relationally inconsistent
cross-workspace references are excluded. Denied and malformed policy outcomes
return empty results or generic not-found responses.

Internal create/edit views remove `share_with_counterparty` and version
services receive an explicit `False` whenever either the bounded repository
policy is active or the independent external-collaboration gate is off,
including when a caller forges the removed POST field. The legacy sharing
control is available only when `EXTERNAL_COLLABORATION_ENABLED=true`; that
setting is committed off and is not approved for activation. Existing internal
upload paths also reuse one pre-storage 50 MB and conservative extension
allowlist validator; browser MIME values remain untrusted metadata. Previously
shared records are not exposed, migrated, or deleted by this slice.

## Committed state

This extends the existing default-off repository boundary and uses the same
four non-production settings:

- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED=true`
- `PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED=false`
- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS=<current non-production environment>`
- `PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST=<workspace slug>`

An empty allowlist activates nothing. Production fails closed. The feature
must remain committed off and must not be activated merely because this code
is merged.

## Acceptance and smoke evidence

- Restricted contract-, client-, and matter-linked documents are absent from
  list/search results.
- Denied detail, edit, delete, download, and either-side comparison return a
  generic 404 without document metadata.
- Restricted contract/client/matter choices are absent from create/edit forms;
  forged relationship IDs fail normal form validation with zero document
  mutation.
- Forged `share_with_counterparty` input still creates a private document.
- Unsupported or oversized internal uploads fail before document/storage
  mutation; existing accepted-file API coverage remains green.
- Eligible document upload, versioning, download audit, durable-storage guard,
  and existing tenant-isolation tests remain green.
- Malformed policy, inactive membership, configuration error, and abort paths
  fail closed without object or exception details in logs.
- No model or migration change exists.

Use synthetic records only. For a named non-production workspace, verify one
ordinary and one Ethical-Wall-restricted contract with a document on each.
Confirm the restricted member cannot find, open, compare, edit, delete, or
download the restricted document and cannot select its relationships during
upload. Confirm an eligible administrator can upload a synthetic file and the
stored document remains private.

## Abort and rollback

If any restricted metadata, count, form option, file state, or signed URL is
observable, set `PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED=true` and restart.
The allowlisted workspace then receives empty document collections and generic
not-found responses rather than the tenant-only legacy path.

No schema or business-data rollback is required. Preserve audit evidence and
the immutable document versions. Do not delete documents, alter Ethical Walls,
or enable external sharing as a rollback action. Recovery requires revalidation
and a separately recorded operator decision before clearing the abort switch.

This is pilot/demo hardening, not a production malware-quarantine claim.
Production or sensitive-data use remains blocked until an approved malware
scanner, quarantine/release workflow, retention policy, and operator evidence
exist.
