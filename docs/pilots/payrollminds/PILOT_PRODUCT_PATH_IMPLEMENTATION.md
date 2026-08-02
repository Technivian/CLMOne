# PayrollMinds pilot product-path implementation

**Status:** Proposed operational record. This document does not approve
PayrollMinds production activation, data processing, users, or customer
commitments.

## Implemented bounded path

The default-off path uses only canonical CLM One records and services:

1. `DocumentIngestionAttempt` quarantines an upload and records its workspace,
   uploader, correlation ID, digest and scanner outcome. It is technical
   quarantine evidence under accepted ADR-0016, not a second document model.
2. Only a `CLEAN` verdict may enter the atomic release operation.
3. A human supplies the Contract Record metadata at release. The service creates
   the canonical `Contract` with locked `UPLOAD` provenance, then the canonical
   `Document` and immutable `DocumentVersion`, all in one transaction.
4. The `DocumentReviewRun` records that those initial values are
   `human_entered` and that suggestions are non-authoritative. External AI
   review/provider surfaces are blocked in controlled-pilot mode; failed local
   extraction never prevents manual entry.
5. The Contract owner is the releasing user. In the existing PAR-SEC-002
   allowlisted mode, ordinary members can discover only records they own or
   created; active workspace owners and admins retain their defined operational
   role. Ethical Walls still restrict every role.
6. Existing repository, document and obligations surfaces apply the same
   read-policy boundary. Contract-linked dates and reminders do not disclose
   private records to an ineligible member.

No external portal, workflow-designer, negotiation, signature, analytics,
integration, or new role/permission/task/property/audit model is included.

## Activation and user-facing states

This code is disabled by default. A clean verdict is not a production approval.
The upload/release APIs return controlled messages for missing titles, invalid
types or dates, unavailable ingestion, and a failed clean-release operation.
The released review run supplies the explicit next action: verify or enter
contract metadata. If scanning fails, the attempt remains recoverable through
the explicit retry/scan flow and no canonical record is created.

The status/release endpoint is private to the uploader or an active workspace
owner/admin. A non-disclosing `404` is returned to other members.

## Migration and rollback

**Migration impact:** none. This change introduces no database model, field,
enum, or data migration.

**Configuration rollback:** set both existing controls to fail closed and
restart the application:

```text
DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED=true
PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED=true
```

This preserves quarantine attempts, Contract Records, Document Versions,
review records and append-only audit evidence. It denies new ingestion/release
and returns empty/private repository results rather than reverting to an
unfiltered access path. Do not delete customer records or audit evidence as a
rollback step. Recovery requires the applicable approval, unchanged reviewed
SHA, successful tests, and an operator record before either abort switch is
cleared.

## Residual limitations and required evidence

## Release-evidence validation (2026-08-02)

The following source-SHA checks were repeated for
`fec9b205a42d976a35ccb093f68c6cf3e5371487` before updating the PR evidence
checklist:

- `python manage.py check` — passed.
- `python manage.py test tests.test_cross_tenant_isolation -v 1` — 75 tests
  passed.
- `python manage.py migrate --noinput` and `python manage.py
  audit_null_organizations` — passed; the audit reported no violations.
- `git diff --check` — passed.
- Fail-closed rollback drill: `tests.test_document_ingestion_security`,
  `tests.test_par_sec_002_repository_enforcement`, and
  `tests.test_private_document_repository` — 45 tests passed. The drill
  confirms that the quarantine and repository abort switches deny or hide data
  rather than falling back to an unfiltered path.

This is source-branch release-evidence remediation only. It does not enable a
pilot, alter production configuration, add a feature, or constitute combined
release-candidate validation.

- This is a code path only; it does not enable a production workspace or grant
  any user access.
- Named record sharing beyond owner/creator plus defined workspace
  owner/admin roles is not implemented because no approved canonical persisted
  record-grant model was available. It must not be simulated with client-side
  controls.
- Bulk upload, email forwarding, external users, production storage setup,
  reminder delivery operations, and production export activation remain outside
  this implementation and require their own evidence.
- The existing organization activity export is restricted to active workspace
  owners/admins and now emits `organization.activity_exported`; it is the
  controlled audit-evidence export for this narrow path. This path also emits
  immutable audit events for quarantine, release, Contract Record
  creation/provenance, Document Version creation, and reminder changes.
