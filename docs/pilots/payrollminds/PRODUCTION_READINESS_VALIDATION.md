# PayrollMinds production-readiness validation

**Status:** Local documentation/repository validation only — not production,
pre-production, operator, customer, backup, restoration, TLS, or deployment
evidence.

## Executed on this draft candidate

```text
python manage.py test tests.test_production_config_gate \
  tests.test_document_storage_download \
  tests.test_observability_guardrails \
  tests.test_scheduled_job_automation \
  tests.test_restore_drill \
  tests.test_identity_telemetry_and_exports --verbosity 1

Ran 64 tests in 4.275s
OK
System check identified no issues (0 silenced).
```

```text
python manage.py check
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
No changes detected

bash -n scripts/db_backup.sh
bash -n scripts/db_restore_drill.sh
exit status: 0
```

The exercised guards cover production configuration rejection/secure cookies,
private object-storage requirements and document-download auditing,
health/scheduler observability, job retry/dead-letter behavior, restore-drill
record handling, and export-related application behavior. Expected negative
path logs occurred during the suite (for example a simulated degraded health
response); they are test assertions, not a deployed incident.

## Still required before Go

- exact-SHA CI after this draft PR is opened;
- isolated pre-production provisioning and region/IAM/TLS proof;
- transactional-email and alert-route delivery evidence;
- PostgreSQL and object-store backup/restore drill with actual RPO/RTO;
- error-reporting sink/redaction verification;
- named service owners, customer support route, privacy/offboarding terms, and
  controlled export/offboarding rehearsal.

No production credentials were used or committed, no production migration was
run, and no public production domain or traffic was enabled.
