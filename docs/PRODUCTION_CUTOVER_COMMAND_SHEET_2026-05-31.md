# Production Cutover Command Sheet

Date: 2026-05-31
Use this in the live change window. Run from repo root on the production host.

## 0) Fill These First

- RELEASE_COMMIT_SHA=fe77689e61163763a7836b9359c57281cb1b04db
- PROD_HOST=cms-aegis-preview.onrender.com (verify this is the cutover host)
- PROD_DB_URL=<set from production secret manager>
- BACKUP_DIR=/backups/cms-aegis

## 1) Production Env

export DJANGO_ENV=production
export DJANGO_SECRET_KEY='<long-random-secret>'
export DATABASE_URL="$PROD_DB_URL"
export ALLOWED_HOSTS="$PROD_HOST,localhost,.onrender.com"
export CSRF_TRUSTED_ORIGINS="https://$PROD_HOST,https://*.onrender.com"
export DEFAULT_FROM_EMAIL='ops@example.com'
export ALLOW_SQLITE_IN_PRODUCTION='false'
export DB_SSL_REQUIRE='true'
export SECURE_SSL_REDIRECT='true'
export SECURE_HSTS_PRELOAD='true'

## 2) Confirm Target

git rev-parse HEAD
python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"

Expected:
- commit matches approved release commit
- database engine is django.db.backends.postgresql

## 3) Backup

mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/pre-cutover-$(date +%Y%m%dT%H%M%S).dump"
pg_dump -Fc "$PGDATABASE" > "$BACKUP_FILE"
ls -lh "$BACKUP_FILE"

Expected:
- backup file exists
- backup file size is non-zero

## 4) Drain Traffic

Use your platform maintenance or load-balancer drain step.
Do not continue until new user traffic is blocked.

## 5) Deploy Approved Commit

git fetch origin codex/cms-aegis-activation
git checkout "$RELEASE_COMMIT_SHA"
git rev-parse HEAD

## 6) Production Checks

python manage.py migrate --noinput
python manage.py audit_null_organizations
python manage.py verify_postgres_cutover
python manage.py generate_release_gate_report --fail-on-no-go

## 7) Live Smoke

Execute: docs/MANUAL_SMOKE_CHECKLIST.md
Minimum checks:
- anonymous /dashboard/ redirects to /login/
- org isolation holds
- cross-org contract access is denied
- admin/team flows work
- search does not leak across orgs

## 8) Reopen Traffic

Use your platform traffic-restore step.

## 9) Final Verify

python manage.py audit_null_organizations
python manage.py generate_release_gate_report --fail-on-no-go

## 10) Recurring Contract Maintenance

Run these on the scheduler cadence after cutover, or manually when validating a tenant:

python manage.py run_retention_jobs
python manage.py run_contract_lifecycle_jobs

Targeted validation example:

python manage.py run_retention_jobs --organization-slug <slug>
python manage.py run_contract_lifecycle_jobs --organization-slug <slug>

## 11) Stop And Roll Back If Any Fails

Rollback triggers:
- migration failure
- release gate NO-GO
- smoke failure
- cross-tenant leakage
- instability after reopening traffic

Rollback runbook:
- docs/ROLLBACK_RUNBOOK.md
