# PayrollMinds operator backup/restore drill runbook

**Audience: the human Infrastructure operator (Haroon Wahed), running this
from a shell with real browser/OAuth access to Render, Neon, and
Cloudflare, and Google Cloud Shell (or any shell) with outbound internet.**
This document assumes the coding-agent sandbox that authored it has
**none** of that access — confirmed empirically (AGENT PROMPT 34):
`clmone.com`, `console.neon.tech`, `api.neon.tech`, `api.cloudflare.com`,
`api.render.com`, and `dash.cloudflare.com` all return an explicit `403`
policy denial from that environment's own network proxy. Nothing in this
runbook can be executed by an agent; every command below is meant for you
to run yourself.

**Release posture, unchanged by this runbook or by running this drill:**
`TECHNICAL ENVIRONMENT: LIVE` / `PAYROLLMINDS CUSTOMER ONBOARDING: NO-GO`.
Completing this drill closes specific named gaps (see
`PRODUCTION_TARGET_COMMISSIONING.md`'s Recommendation section); it does
not by itself authorize customer onboarding.

**CLI syntax in this document was verified, not guessed.** `neonctl@2.46.0`
and `wrangler@4.120.0` were installed from the public npm registry (no
credentials required for `--help`) and their command trees inspected
directly before this runbook was written. If you're running a different
installed version, run `--help` yourself before trusting any command here
verbatim — flags do change between releases.

---

## Section A — Authentication

Do this once per shell session. Never paste an API key or connection
string into a chat with an AI agent, including this one — everything
below uses browser/OAuth login instead.

### Neon

```bash
npm install -g neonctl@latest
neonctl auth
neonctl projects list -o json
```

`neonctl auth` opens a browser login; `neonctl projects list` should show
the existing CLM One project. Select it and note its `id` — you'll need
`--project-id` for every later command.

### Cloudflare

```bash
npx wrangler@latest login
npx wrangler@latest r2 bucket list
```

`wrangler login` opens a browser login. `r2 bucket list` should show the
canonical document bucket and the quarantine bucket.

**Where a scoped R2 API token is required** (Section 12's object-copy step
— `wrangler r2 object get/put` can use your OAuth login for buckets in
your own account, but a *separate* recovery-target bucket you create for
this drill may need its own narrowly-scoped Account API token per
`TARGET_ENVIRONMENT_INVENTORY.md` §1c's existing convention): create it
in the Cloudflare dashboard as an **Account API token** (not a User
token — see the reasoning already recorded for the quarantine bucket's
token), scoped to **that one bucket only**, and export it only as a Cloud
Shell environment variable for this session:

```bash
export AWS_ACCESS_KEY_ID="<paste once, this shell session only>"
export AWS_SECRET_ACCESS_KEY="<paste once, this shell session only>"
```

Never echo these, never write them to a file in this repository, never
paste them into chat with any agent.

---

## Section 7 — Discover and record infrastructure

### Neon

```bash
neonctl projects list -o json
neonctl projects get --project-id "$NEON_PROJECT_ID" -o json
neonctl branches list --project-id "$NEON_PROJECT_ID" -o json
```

Record (non-secret): project ID, project name, region, plan, the
production branch's name/id, the database name, PostgreSQL version. The
configured point-in-time-recovery history window is a plan property, not
a CLI flag as of this writing — check it on the project's Neon dashboard
page (Settings → Backup/restore) and record the number of days/hours
shown there. **Do not assume it matches whatever was previously
documented — record what the dashboard actually shows today.**

### Cloudflare R2

```bash
wrangler r2 bucket list
wrangler r2 bucket info <canonical-bucket-name>
wrangler r2 bucket info <quarantine-bucket-name>
wrangler r2 bucket lifecycle list <canonical-bucket-name>
wrangler r2 bucket lifecycle list <quarantine-bucket-name>
wrangler r2 bucket lock list <canonical-bucket-name>
```

Record: account ID, both bucket names, jurisdiction/location if shown,
public-access state (`wrangler r2 bucket dev-url get <bucket>` — should
report disabled/no public URL for both), lock configuration, lifecycle
rules. **`wrangler`'s R2 command tree has no `versioning` or
`replication` subcommand at all** (verified directly against the
installed CLI) — do not write into evidence that either exists unless
you find independent confirmation elsewhere; the absence of a CLI surface
for it is itself evidence worth recording as-is.

### Render

In the Render dashboard, on the web service's page: record the service
ID (visible in the URL), region, the currently-deployed commit SHA
(shown on the Deploys tab), and current health status. No credential
values go into evidence — just these identifiers.

---

## Section 8 — Create the live synthetic fixture

Run this **from Render's own Shell** (dashboard → your service → Shell
tab) so it uses the real, already-configured production settings safely
— this task's tooling never needs its own copy of production
credentials, because it runs inside the process that already has them.

```bash
python manage.py create_payrollminds_recovery_fixture \
  --confirm-synthetic-recovery-drill
```

This prints a `namespace=payrollminds-recovery-drill-<timestamp>` line —
copy it. It creates one small, explicitly synthetic Organization with a
Contract, a real generated `.docx` Document (written through whichever
storage backend production is actually configured to use — R2, given
`MEDIA_STORAGE_BACKEND=s3` is confirmed set), a Deadline, and the
resulting AuditLog trail. **No employee, salary, or payroll data is
created** — it's a synthetic B2B commercial-contract fixture, the same
object shape the real MSA builder always produces.

Then, still in Render's Shell:

```bash
python manage.py export_payrollminds_recovery_manifest \
  --namespace "$RECOVERY_NAMESPACE" \
  --output /tmp/recovery-before.json
```

The manifest is plain, secret-free JSON (the exporter refuses to write
anything that looks like a credential — verified in
`tests/test_payrollminds_recovery_drill.py`). Move it to Cloud
Shell however you'd move any small text file off Render's Shell — e.g.
`cat /tmp/recovery-before.json` and paste the output into a file in Cloud
Shell, or use Render's own file-download mechanism if the Shell UI offers
one. Either is fine: **the file itself contains no secret**, so there's
no exposure risk in how you move it, only in accidentally running the
*fixture* command against the wrong database.

---

## Section 9 — Establish the Neon recovery point and isolated branch

Record the wall-clock time immediately after the fixture command above
returns — that's your source data timestamp.

```bash
export RECOVERY_TIMESTAMP="2026-08-08T21:16:00Z"   # use the real time you recorded

neonctl branches create \
  --project-id "$NEON_PROJECT_ID" \
  --name "payrollminds-recovery-drill-$(date +%Y%m%d-%H%M)" \
  --parent "$RECOVERY_TIMESTAMP" \
  -o json
```

This is the verified real syntax: `--project-id`, `--name`, and
`--parent` (which accepts a timestamp directly for point-in-time branch
creation — confirmed via `neonctl branches create --help`). **This
creates a new, separate branch — it does not touch the production
branch.** Record the branch ready time and the returned branch ID from
the JSON output.

Retrieve its connection string without ever printing it into any evidence
file:

```bash
neonctl connection-string "payrollminds-recovery-drill-$(date +%Y%m%d-%H%M)" \
  --project-id "$NEON_PROJECT_ID"
```

Set it as an environment variable in this shell only:

```bash
export RECOVERY_DATABASE_URL="<paste the printed connection string>"
```

---

## Section 10 — Database integrity and authorization verification

Still in Cloud Shell, pointed at the recovery branch — **never at
production**:

```bash
export DATABASE_URL="$RECOVERY_DATABASE_URL"
export DJANGO_SETTINGS_MODULE=config.settings_development
export ALLOW_REMOTE_DATABASE=true   # this repo refuses to run against any non-local DB otherwise — see contracts/apps.py
```

Use `config.settings_development`, not `config.settings_production`, for
this verification run — verified directly against this repository's own
code: `settings_production` raises `ImproperlyConfigured` at import time
(before your command even runs) unless `ALLOWED_HOSTS`,
`CSRF_TRUSTED_ORIGINS`, `DEFAULT_FROM_EMAIL`, `APP_BASE_URL`,
`OPERATOR_ALERT_EMAIL`, and a strong `SECRET_KEY` are all already set in
this shell — none of which a bare Cloud Shell session has.
`settings_development` has none of those guards and reads whichever real
`DATABASE_URL` you give it, which is all this step needs.

```bash
python manage.py verify_payrollminds_recovery_manifest \
  --manifest recovery-before.json \
  --after-output recovery-database-after.json \
  --comparison-output recovery-database-comparison.json \
  --verify-authorization
```

This writes both output files and exits non-zero if there is any
unexplained difference or missing object — including, when
`--verify-authorization` is passed, if the owner can't access the
synthetic contract, if the unrelated member *can*, if the cross-workspace
user *can*, or if the restored AuditLog rows are no longer append-only.
It reuses this repository's real `filter_contract_queryset` policy
service (the same function production views use) rather than any
recovery-drill-specific ACL check — see
`contracts/services/recovery_drill.py::_verify_authorization`.

Record the start time (before this command) and completion time (after)
— that's your database validation duration for Section 14.

**Do not make this recovery branch's compute endpoint public.** It only
needs to be reachable from this Cloud Shell session.

---

## Section 11 — R2 backup design discovery (do this before Section 12)

First determine whether an independent object backup already exists.
**Do not assume `wrangler r2 bucket lock` output means backup coverage
exists — lock rules prevent deletion/overwrite, they are not a copy of
the data anywhere else.** A real GREEN answer requires one of:

- a dedicated, separate R2 backup bucket you can point to,
- an external storage provider holding a copy,
- a scheduled/automated object-copy job you can point to,
- any other genuinely independent, separately-recoverable copy.

```bash
wrangler r2 bucket list   # look for anything already named/tagged as a backup destination
```

**If none of the above exists, stop here and report:**

```
OBJECT RECOVERY MECHANISM NOT YET CONFIGURED
```

Do not silently create one as a side effect of "discovery." If you want
to remediate, the separate, explicit next step is:

```bash
wrangler r2 bucket create payrollminds-recovery-backup
```

Then create a **separate, narrowly-scoped Account API token** for this
new bucket only (same pattern as the quarantine bucket's token — Account
API token, not User token, `Specify bucket(s)` → this bucket only). Do
not enable `dev-url` (public access) on it. This is infrastructure
remediation, not part of the drill itself — track it as a follow-up, not
something this PR performs.

---

## Section 12 — R2 one-object recovery drill (only once Section 11 found or created a real backup destination)

Using the synthetic document object from the fixture (its key is in
`recovery-before.json` at `document.version.storage.key`):

```bash
export SOURCE_KEY="documents/general/<...>.docx"   # from recovery-before.json

# 1. Original hash, read directly from the canonical bucket
wrangler r2 object get "$CANONICAL_BUCKET/$SOURCE_KEY" --file /tmp/source.docx
sha256sum /tmp/source.docx   # note this value: SOURCE_SHA256

# 2. Copy into the independent backup bucket
wrangler r2 object put "payrollminds-recovery-backup/$SOURCE_KEY" --file /tmp/source.docx

# 3. Verify the backup copy's hash
wrangler r2 object get "payrollminds-recovery-backup/$SOURCE_KEY" --file /tmp/backup-copy.docx
sha256sum /tmp/backup-copy.docx   # must equal SOURCE_SHA256

# 4. Simulate loss recovery: fetch from the backup into an isolated recovery location
wrangler r2 object get "payrollminds-recovery-backup/$SOURCE_KEY" --file /tmp/restored.docx

# 5. Restored hash
sha256sum /tmp/restored.docx   # must equal SOURCE_SHA256
```

**Required: `SOURCE_SHA256` (step 1) == backup hash (step 3) == restored
hash (step 5).** Compare all three against `recovery-before.json`'s
`document.version.storage.sha256` too — all four values must match.

Deliberately using plain `wrangler r2 object get/put` and `sha256sum`
here rather than this repository's own `hash_payrollminds_recovery_object`
command: that Django command reads through **already-configured** Django
storage aliases (`default`, `quarantine`), which is right for verifying
the *live* canonical/quarantine buckets from Render's own Shell, but the
independent recovery-backup bucket has no Django configuration pointing
at it — adding one would be a production settings change, which this
drill must not make. Provider-neutral `wrangler`/`sha256sum` avoids that
entirely.

If quarantine recovery is in scope for your operating model, repeat the
same five steps for a quarantine object using the quarantine bucket
instead.

**Never delete the production source object** at any point in this
procedure.

Record start/end time of steps 2–5 for Section 14's object-recovery
duration.

If no viable recovery mechanism exists (Section 11's `OBJECT RECOVERY
MECHANISM NOT YET CONFIGURED`), skip this section entirely and report
that status instead — do not fabricate a recovery result.

---

## Section 13 — Routine R2 backup control (separately deployed)

Because native S3-style versioning/replication is not a first-class
`wrangler` R2 feature (confirmed by the absence of any such subcommand),
separate **prevention** from **recovery** explicitly:

- **Prevention** (already partly in place): `wrangler r2 bucket lock`
  rules stop accidental deletion/overwrite of live objects. This is not
  backup coverage by itself.
- **Recovery** (the remaining gap): a narrow scheduled Cloudflare Worker is
  technically ready in `infrastructure/r2-daily-document-backup`. It copies
  each observed new/changed primary object version to the independent
  `clmone-documents-backup` bucket once daily, retains earlier copies, and
  never mirrors a delete. Its two bucket bindings, UTC Cron Trigger, run
  evidence, rollback steps, and first-run proof requirements are in
  `R2_DAILY_DOCUMENT_BACKUP_DEPLOYMENT_RUNBOOK.md`.

It is not deployed by this repository evidence. Do not treat its local tests
as a provider-side backup result: `DOCUMENT RECOVERY` remains
`BLOCKED — ROUTINE BACKUP DEPLOYMENT/PROOF PENDING` until separately
authorized deployment and a retained successful first-run record.

---

## Section 14 — RPO/RTO, calculated from your own recorded timestamps

Do not invent numbers — fill these in from what you actually recorded
above:

| Metric | Formula | Your value |
|---|---|---|
| Database observed RPO | `RECOVERY_TIMESTAMP` (Section 9) minus the last committed write before it | fill in |
| Database observed restore time | branch-ready time (Section 9) minus restore-initiation time | fill in |
| Database validation completion time | Section 10 command completion time minus Section 10 command start time | fill in |
| Object observed RPO | based on Section 11's actual configured mechanism (e.g. "however stale the last scheduled copy job run was" — record whatever is true, including "unknown, no scheduled job exists yet") | fill in |
| Object recovery duration | Section 12 step 5 completion time minus step 2 start time | fill in |
| Configured Neon history window | from Section 7's dashboard check | fill in — record separately, do not equate this with observed RPO above |

If no approved RPO/RTO target objective exists anywhere in this
repository's documentation (it doesn't, as of this writing), record that
explicitly as an open operational-governance item — do not invent a
target to compare against.

---

## Section 15 — Cleanup

```bash
# Temporary Neon recovery branch
neonctl branches delete "payrollminds-recovery-drill-<your-branch-name>" --project-id "$NEON_PROJECT_ID"

# Temporary R2 recovery-namespace objects (if you created a scratch prefix beyond the backup bucket itself)
wrangler r2 object delete "payrollminds-recovery-backup/$SOURCE_KEY"   # only if you don't want to keep this as a real backup copy

# Temporary Cloud Shell files
rm -f /tmp/source.docx /tmp/backup-copy.docx /tmp/restored.docx

# Temporary scoped credentials created for this drill
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY RECOVERY_DATABASE_URL
```

**Do not delete the live synthetic fixture** (the Organization/Contract/
Document created in Section 8) until you've explicitly decided to and the
evidence bundle (Section 16) is complete — it's the one non-production
object this drill created, and it's clearly namespaced
(`payrollminds-recovery-drill-*`) so it can never be confused with real
data. If you do delete it later, do so directly against the production
database via the governed application (not a raw SQL delete), and note
in the evidence that cleanup occurred — never delete `AuditLog` rows,
which the application itself refuses to allow anyway.

Record exactly what you cleaned up and what (if anything) you chose to
retain.

---

## Section 16 — Evidence bundle

Once `recovery-before.json`, `recovery-database-after.json`,
`recovery-database-comparison.json`, and (if Section 12 ran)
`recovery-object-comparison.json` exist in one directory:

```bash
python manage.py build_payrollminds_recovery_evidence_bundle \
  --evidence-dir . \
  --output recovery-evidence-bundle.json
```

This re-checks every value in every artifact for secret-shaped content
before writing the combined bundle, independently of the checks each
producing command already applied — it will refuse to write the bundle
at all if anything looks like a live credential.

**Do not commit `recovery-before.json` et al., or any Neon/R2 dump file,
to this repository.** Once you've reviewed the evidence bundle and are
satisfied it's clean, update
`docs/pilots/payrollminds/BACKUP_RESTORE_DRILL.md` with the real
`BACKUP/RESTORE GATE GREEN` (or the appropriate `NO-GO —
...UNPROVEN` status per this drill's actual outcome) — that document may
only claim success after you have actually run this runbook and it is
accurate to report.

---

## Section 17 — PayrollMinds database-only Neon recovery gate

This section is the canonical operator procedure for the **database recovery**
gate. It is intentionally narrower than Sections 8–16: do **not** create the
synthetic fixture, do **not** perform an R2 action, and do **not** change
application, contract-type, monitoring, or production configuration in this
procedure. The only provider mutation is creation of a temporary, isolated
Neon recovery branch. Production remains the read-only source throughout.

Before beginning a future drill, confirm the current canonical status in
`PAYROLLMINDS_PRODUCTION_OPERATIONS_READINESS.md`. A recovery gate that is
BLOCKED cannot become GREEN until actual evidence satisfies this section. The
Infrastructure/Backup Owner is Haroon Wahed during bootstrap; ownership must
be reviewed by 2026-09-30 or earlier when independent capacity is available.

### 17.1 Preconditions and source-state manifest

1. Record the UTC drill-start timestamp.
2. In the Neon console, record non-secret evidence of the project, production
   branch name/ID, Frankfurt/EU region, and the actual currently available
   PITR/history window. Do not rely on the historical six-hour entry; it is a
   temporary risk decision, not a provider-console observation.
3. From a trusted operator shell already configured for the production database,
   run the following unchanged read-only manifest and retain its plain TSV
   output outside this repository:

   ```bash
   psql "$DATABASE_URL" -X -v ON_ERROR_STOP=1 -P pager=off \
     -f docs/pilots/payrollminds/NEON_DATABASE_RECOVERY_MANIFEST.sql \
     > payrollminds-production-manifest.tsv
   ```

   The SQL contains counts for public tables, `django_migrations`, Contract,
   Document, DocumentVersion, WorkflowInstance, and AuditLog, plus an ordered
   non-sensitive Contract structural fingerprint. It contains no titles,
   contents, counterparties, names, email addresses, or payroll data.
4. Record the manifest capture timestamp and select a recovery point at or
   before that known source state, within the PITR window. Record the exact UTC
   timestamp and its age relative to the source manifest. This is the empirical
   demonstrated RPO for the drill; do not describe it as a contractual target.

### 17.2 Create and time the isolated recovery branch

1. Record the UTC branch-create submission timestamp.
2. Create the isolated branch, substituting only operator-recorded values:

   ```bash
   neonctl branches create \
     --project-id "$NEON_PROJECT_ID" \
     --name "payrollminds-recovery-drill-YYYYMMDD" \
     --parent "$RECOVERY_POINT_UTC" \
     -o json
   ```

   Preserve the returned non-secret branch ID/name as evidence. Do not alter
   the production branch and do not make the recovery endpoint public.
3. Poll the branch only until its database is queryable. Record the UTC
   branch-ready timestamp. **Measured recovery time** is branch-ready timestamp
   minus branch-create submission timestamp. Record drill elapsed time from
   overall drill start separately.
4. Obtain the recovery branch connection string only in the operator shell and
   set it only as a session environment variable. Never commit, print, paste,
   or place it in evidence:

   ```bash
   export RECOVERY_DATABASE_URL="<operator-pasted secret>"
   ```

### 17.3 Verify recovered state and reconcile

1. Run the identical manifest on the isolated recovery branch:

   ```bash
   psql "$RECOVERY_DATABASE_URL" -X -v ON_ERROR_STOP=1 -P pager=off \
     -f docs/pilots/payrollminds/NEON_DATABASE_RECOVERY_MANIFEST.sql \
     > payrollminds-recovery-manifest.tsv
   diff -u payrollminds-production-manifest.tsv payrollminds-recovery-manifest.tsv
   ```

2. A zero diff proves the selected point reproduced the recorded source state,
   including schema/migration count and required application-state counts. If
   the selected point is earlier than the source capture, explain each expected
   difference using the recorded recovery-point age. Any unexplained difference,
   missing table, failed query, or inaccessible recovered branch is a **FAIL**;
   DATABASE RECOVERY remains BLOCKED.
3. Record the schema/migration result explicitly: the manifest must complete and
   `django_migrations_count` plus `public_schema_table_count` must reconcile to
   the selected source point. This is the database schema/migration check; do
   not run `migrate`, `makemigrations`, fixture creation, or any write command
   against either branch for this drill.
4. Record production-write count as **zero**. The only permitted provider-side
   mutation is the temporary recovery branch.

### 17.4 Completed isolated Neon drill evidence — 2026-08-17

The following is the factual summary supplied by the authorized operator. It
does not add unrecorded Neon-console metadata, recovery-branch identifiers,
recovery-point timestamps, or branch-provisioning timing.

| Evidence field | Recorded result |
| --- | --- |
| Operator | Haroon Wahed |
| Source manifest capture | 2026-08-17 15:04:19.345088+00 |
| Recovery verification query | 2026-08-17 15:08:30.910053+00 |
| Restore target | Isolated Neon recovery branch |
| Public table count | 128 source / 128 recovered |
| Django migration-history count | 149 source / 149 recovered |
| Contract count | 4 source / 4 recovered |
| Identifier-only Contract fingerprint | `ff9e0fc04dc813d818adc966f1dbdcdd` source / recovered |
| Document / DocumentVersion / WorkflowInstance counts | 0 / 0 / 0 source and recovered |
| Audit-event count | 29 source / 29 recovered |
| Recovered database queryability | Verified by successful recovered-manifest query |
| Manifest reconciliation | EXACT MATCH |
| Production writes during drill | NONE |
| Production restore | Not performed |
| Conservative end-to-end drill duration | <= 4m12s (251.564965 seconds from source-manifest capture to successful recovered query) |
| Recovery-branch disposal | Not claimed; permitted only after evidence retention |

Schema/table count, Django migration history, Contract count, the
identifier-only Contract fingerprint, and the audit-event count reconciled.
No observed loss existed relative to the selected verified state. Because the
source counts for Documents, DocumentVersions, and WorkflowInstances were
zero, this drill did not prove recovery of populated examples of those row
types. That fact does not invalidate the database-recovery result; recovery of
document objects remains a separate R2/document-recovery gate.

The duration is deliberately conservative and is **not** asserted to be Neon
branch provisioning time: the operator did not separately record branch-create
submission and branch-ready timestamps. The result is empirical and creates no
contractual RTO/RPO SLA. The recovery/history window remains the previously
accepted temporary six-hour constraint; this drill proves the selected point,
not every point in that window.

### 17.5 Pass criteria and recurring control

For each future drill, retain the following non-secret evidence outside the
repository, then add only the factual summary to the canonical readiness
record after review:

| Evidence field | Required result for each future drill |
| --- | --- |
| Operator | Haroon Wahed |
| Drill start / recovery point / source-manifest capture | Recorded as actual non-secret evidence |
| Project, production branch, Frankfurt/EU and PITR console evidence | Recorded as actual non-secret evidence |
| Recovery branch name/ID and branch-ready timestamp | Recorded as actual non-secret evidence |
| Measured recovery time and effective recovery-point age | Recorded as actual evidence; distinguish branch provisioning from end-to-end time |
| Source/recovered manifest files and reconciliation | Retained; exact match or explained differences only |
| Schema/migration verification | Manifest completes and counts reconcile |
| Production-write count | Zero |
| Result | GREEN only when all required evidence is satisfied |

DATABASE RECOVERY is **GREEN** for the completed 2026-08-17 drill. Future
drills may be recorded GREEN only after the evidence proves an isolated branch
was created and became queryable, a recorded recovery point was used, the
schema/migrations and required counts/fingerprint reconcile, recovery time was
measured, production writes were zero, and the recurring control below is
documented. This procedure establishes no contractual RTO/RPO commitment: the
measured result is empirical and the maximum available PITR remains constrained
by the accepted temporary retention window.

After evidence is safely retained, the operator may delete the temporary
recovery branch through Neon. Verify the branch name/ID before deletion; never
delete or alter the production branch.

### 17.6 Recurring control

Repeat this isolated database recovery drill quarterly and after every material
database or storage architecture change. Retain each drill's non-secret
evidence with the release/operations record. This is an operator cadence, not
an automated production scheduler. Infrastructure/Backup Owner remains Haroon
Wahed during bootstrap, subject to review by 2026-09-30.
