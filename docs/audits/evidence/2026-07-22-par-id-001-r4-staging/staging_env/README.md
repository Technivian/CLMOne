# R4 staging-equivalent environment — `par-id-001-r4-staging-equivalent`

Named non-production staging environment for PAR-ID-001 R4 diagnostic activation.

**Do not commit `db.sqlite3`.**

Recreate (flags **off** until R4 activation):

```bash
export DJANGO_SETTINGS_MODULE=config.settings_development
export DATABASE_URL="sqlite:///$(pwd)/docs/audits/evidence/2026-07-22-par-id-001-r4-staging/staging_env/db.sqlite3"
export PROCESS_ROLE_SHADOW_WRITE_ENABLED=false
export PROCESS_ROLE_PARITY_REPORTING_ENABLED=false
export PROCESS_ROLE_RESOLVER_PARITY_ENABLED=false
export PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=false
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_data
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py seed_mvp_demo
.venv/bin/python manage.py seed_controlled_pilot
.venv/bin/python manage.py seed_payrollminds_demo
.venv/bin/python manage.py process_role_r1_certain_remediation --apply --json
```

R4 activation (authorized only after votes recorded):

```bash
export PROCESS_ROLE_SHADOW_WRITE_ENABLED=true
export PROCESS_ROLE_PARITY_REPORTING_ENABLED=true
export PROCESS_ROLE_RESOLVER_PARITY_ENABLED=true
# PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED remains false
```

Immediate rollback: set the three diagnostic flags back to `false`.
