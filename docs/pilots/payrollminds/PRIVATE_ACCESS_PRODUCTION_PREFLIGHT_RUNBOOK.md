# PDR-0008 production private-access accountability preflight

**Status:** Preflight completed on 2026-08-10; deployment authorization remains
pending. This runbook records the approved read-only assessment boundary and
the completed operator evidence. It does not authorize deployment or a
contract-type activation.

## Safety boundary

Run the command through the Infrastructure operator's approved, read-only
production access path. It reads contract/accountability metadata only and
returns no titles, document content, counterparty data, or user names. It does
not write, migrate, repair, backfill, or activate anything.

```bash
DJANGO_SETTINGS_MODULE=config.settings_production \
DATABASE_URL="$READ_ONLY_NEON_DATABASE_URL" \
.venv/bin/python manage.py private_access_data_preflight
```

For a single-workspace review, append `--organization-slug <workspace-slug>`.
Save the JSON output in the restricted release-evidence location, not in this
repository. The output's `classification_record_ids` contains opaque Contract
primary keys only, for an approved remediation decision if needed.

## Required operator decision

- If every record is `safe_under_new_policy`, record **NO DATA MIGRATION
  REQUIRED** in the release evidence.
- If any record is classified `requires_owner_assignment`,
  `requires_created_by_repair`, or `requires_explicit_access_review`, stop.
  Prepare a separately approved deterministic remediation plan identifying the
  opaque record IDs, proposed accountable principal, evidence source, dry-run,
  audit treatment, and rollback. Do not infer ownership from audit logs.

## Completed operator evidence — 2026-08-10

- **Operator:** Haroon Wahed.
- **Evidence source:** operator-controlled Neon SQL assessment and remediation;
  no application request or application `AuditLog` event was generated.
- **Before:** 4 total Contracts; 2 with owner; 4 with `created_by`; 2 missing
  owner; 0 missing `created_by`.
- **Affected historical records:** Contract IDs `2` and `3` only, organization
  `1`, MSA, each `owner_id = NULL`, `created_by_id = 2`.
- **Accountability check:** user `2` is active and has an active MEMBER
  membership in organization `1`.
- **Rationale and deterministic action:** the existing `created_by_id` was the
  verified accountable principal, so the operator set
  `owner_id = existing created_by_id` for IDs `2` and `3` only.
- **Dry-run:** a transaction proved exactly two rows would change and was
  rolled back before the committed action.
- **Committed result:** exactly those two rows changed; Contracts `2` and `3`
  now each have `owner_id = 2`, `created_by_id = 2`.
- **Final preflight:** total 4; owner 4; creator 4; missing owner 0; missing
  creator 0; owner/creator difference 0; inactive/invalid owner 0;
  inactive/invalid creator 0; safe under new policy 4; owner assignment 0;
  creator repair 0; explicit access review 0.
- **Disposition:** **PRODUCTION DATA PREFLIGHT GREEN — NO FURTHER DATA
  REMEDIATION REQUIRED.**

Rollback predicate: if either cited Contract ID or user `2` accountability
evidence is later found wrong before deployment, stop the release. An
authorized operator restores `owner_id` to `NULL` for the affected ID(s) only,
inside a transaction; then repeats the preflight and uses the implementation
code revert as the release rollback path. This predicate has not been met.

**Current implementation-branch status:** **PRIVATE-BY-DEFAULT IMPLEMENTATION
GREEN — PRODUCTION DATA PREFLIGHT GREEN — MERGE/DEPLOYMENT AUTHORIZATION
PENDING**. Production deployment and contract-type activation remain blocked.
