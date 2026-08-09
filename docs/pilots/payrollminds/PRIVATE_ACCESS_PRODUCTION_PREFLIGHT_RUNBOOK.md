# PDR-0008 production private-access accountability preflight

**Status:** Required before production activation. This implementation branch
does not have access to the live Neon database and records no production-data
result.

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

**Current implementation-branch status:** **PRODUCTION DATA PREFLIGHT
PENDING**. Production activation is blocked until this run and any resulting
approved remediation are complete.
