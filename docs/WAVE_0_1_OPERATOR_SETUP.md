# Wave 0–1 — Operator Setup

This covers the **manual steps** required to finish the Wave 0–1 remediation.
The code/config is in place; these are the credential/infra actions only you can do.

---

## C16 — Running the test suite (done, no action)

The suite now runs hermetically against in-memory SQLite (no Supabase/Redis/network):

```bash
DJANGO_SETTINGS_MODULE=config.settings_test .venv/bin/python manage.py test
```

742 tests run in ~30s. 14 failures remain and are **pre-existing** design-system
template tests (roadmap D1) — they fail identically on pristine `main` and are out
of Wave 0–1 scope.

---

## B1 — Object storage for documents (action required)

Code is wired (`config/settings_base.py`, `STORAGES`). To activate:

1. **Create a bucket** — AWS S3, or a Supabase Storage bucket (S3-compatible).
   Make it **private** (no public read).
2. **Set these env vars** in Render (already present as `sync: false` in `render.yaml`):
   - `MEDIA_STORAGE_BACKEND=s3`
   - `AWS_STORAGE_BUCKET_NAME`
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
   - `AWS_S3_REGION_NAME`
   - `AWS_S3_ENDPOINT_URL` — **Supabase only** (the project's S3 endpoint). Omit for AWS S3.
3. **Install the dependency** (already in `requirements/runtime.txt`):
   `django-storages[boto3]`.
4. **Migrate existing files** — copy anything currently in `media/` to the bucket
   (one-time `aws s3 sync media/ s3://<bucket>/`), since local disk is wiped on deploy.
5. Verify: upload a document in the app, redeploy, confirm it still downloads.

> The S3 backend is only referenced when `MEDIA_STORAGE_BACKEND=s3`, so local dev
> keeps using the filesystem with no extra dependencies.

---

## B7 — Automated verified backups (action required)

`scripts/db_backup.sh` now fails loudly, asserts a minimum size, verifies the
archive is restorable with `pg_restore --list`, removes partial dumps, and can
push offsite. The bogus 0-byte artifact has been deleted.

To enable scheduled offsite backups via `.github/workflows/db-backup-scheduler.yml`,
add these **repository secrets**:

- `DATABASE_URL` — production Postgres connection string
- `BACKUP_S3_URL` — e.g. `s3://my-bucket/db-backups/`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_ENDPOINT_URL` (Supabase only), `AWS_DEFAULT_REGION` (optional)

(Alternatively run `scripts/db_backup.sh` from a Render cron — pick one scheduler.)

### Required: rehearse one restore (do not skip)

A backup you have never restored is not a backup. Once:

```bash
# into a throwaway local DB
createdb cms_restore_test
pg_restore --no-acl --no-owner -d cms_restore_test backups/<latest>.dump
psql cms_restore_test -c '\dt' | head   # sanity-check tables exist
dropdb cms_restore_test
```

Record the date you did this; repeat quarterly.

> **Media is separate.** B7 backs up Postgres only. Once B1 is live, ensure the
> object-storage bucket also has versioning/backup enabled — document rows in the
> DB point at files in the bucket, and both must be recoverable together.

---

## 0.2 — Pilot scope flags (done; flip for production)

`render.yaml` sets the pilot scope: `GEMINI_AI_ENABLED=false`,
`BILLING_SELF_SERVE_ENABLED=false`, `TRUST_ACCOUNTING_ENABLED=false`.
Flip each to `true` only when its production control is in place (B6 for AI,
B10 for billing, B8 for trust accounting).
