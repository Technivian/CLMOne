# PayrollMinds R2 daily document backup deployment runbook

**Status:** Operator procedure only. This document does not deploy the Worker
or close the document-recovery gate.

## Exact Worker configuration

- Worker name: `clmone-r2-daily-document-backup`
- Source directory: `infrastructure/r2-daily-document-backup`
- Primary binding: `PRIMARY_DOCUMENTS` → `clmone-documents` (`jurisdiction = "eu"`)
- Backup binding: `BACKUP_DOCUMENTS` → `clmone-documents-backup` (`jurisdiction = "eu"`)
- Cron Trigger: `15 2 * * *` (**Cloudflare Cron is UTC**)
- Public HTTP route: none. Keep `workers_dev = false`; the production path is
  `scheduled()` only.

No access key, secret key, bucket credential, or account token belongs in a
repository file. Authenticate to Cloudflare using the operator's normal
interactive Worker deployment mechanism and confirm the existing account and
bucket names before proceeding.

## Deploy after separate authorization

From the repository checkout at the separately authorized immutable SHA:

```bash
cd infrastructure/r2-daily-document-backup
npm ci
npx wrangler deploy
```

In the Cloudflare dashboard, confirm the deployed Worker has exactly the two
EU-jurisdiction R2 bindings above, the one Cron Trigger, and no public route.
Do not add a route, enable a development URL, or change application environment
variables.

## Verify the first controlled provider-side run

Use Cloudflare's controlled scheduled-event invocation or wait for the Cron
Trigger. Record only non-secret evidence:

1. Worker name, deployed version identifier, and UTC start/finish time.
2. The synthetic canary/new primary object key or approved safe identifier.
3. Its immutable backup key below
   `_backup_versions/v1/<base64url(primary-key)>/<base64url(source-version)>`.
4. A new immutable `_backup_runs/<timestamp>-<run-id>.json` manifest whose
   `result` is `SUCCESS`.
5. `_backup_control/last-success.json` pointing to that manifest.
6. Primary object metadata before/after showing it was unchanged.
7. A prior recovery object still present after the run.

The run metadata records original key, source version, source ETag, source
size, source upload timestamp, and backup timestamp. Its post-write metadata
and size check is operational reconciliation only; the quarterly SHA-256
restore drill remains the stronger byte-integrity control.

The Worker preserves source HTTP metadata on the recovery copy. It does not
blindly duplicate arbitrary source custom metadata, because that metadata can
be unbounded or contain values unsuitable for a routine recovery-control
artifact; the required source identity and accountability metadata is written
under the dedicated `backup_*` keys instead.

## Failure and rollback

If any deployment or scheduled run check fails, disable the Worker Cron Trigger
or roll back to the previously deployed Worker version. Do not delete backup
objects, run a mirror/delete synchronization, change the two bucket bindings,
or alter the primary bucket. A failed or partial run must retain its immutable
run manifest and must not advance `_backup_control/last-success.json`.

Keep the document-recovery gate blocked until a separately authorized
provider-side deployment and successful first-run proof are retained.
