# PayrollMinds release evidence index

**Candidate:** `codex/payrollminds-uat-evidence`, based on `c093adad`.
**Scope:** local synthetic evidence only. CI/review/deployment evidence is not
yet attached and this is not an immutable production release SHA.

| Evidence | Status | Location / result |
|---|---|---|
| Synthetic catalog | Complete | `UAT_SYNTHETIC_CONTRACT_CATALOG.md`; six local fictional records/documents |
| UAT script and acceptance | Complete | `UAT_SCRIPT.md`, `UAT_ACCEPTANCE_SHEET.md` |
| Role and security evidence | Complete (local) | role matrix and security summary |
| Automated synthetic selection | PASS | ingestion/import/preview/AI gate/provenance/private repository/search/export/obligations/audit/jobs/restore/seed selection; exit 0 |
| Restore/job/seed focused selection | PASS | 26 tests in 1.756s; expected test-harness warning recorded as PM-UAT-08 |
| Django system check | PASS | `System check identified no issues (0 silenced).` |
| Migration drift check | PASS | `makemigrations --check --dry-run`: `No changes detected` |
| Tenant audit | PASS | `audit_null_organizations`: `No NULL organization rows found.` |
| Accessibility | Partial | no candidate-specific assistive-technology run |
| Backup/restore | Blocked | no target drill |
| Migration deployment | Blocked | no target migration |
| Deployment/operations | Blocked | no isolated pre-production/operator evidence |
| Offboarding/customer export | Blocked | procedure only; no authorized rehearsal |

Replace or supplement local evidence with exact-SHA green CI, reviews, operator
logs and target-environment artifacts before a release decision.

## Executed local commands

```text
python manage.py seed_payrollminds_demo --reset
python manage.py test tests.test_document_ingestion_security \
  tests.test_repository_csv_import \
  tests.test_legal_front_door.DocumentExtractPreviewApiTests \
  tests.test_payrollminds_ai_governance_gate \
  tests.test_par_core_003_provenance \
  tests.test_private_document_repository \
  tests.test_par_sec_002_repository_enforcement \
  tests.test_par_sec_002_search_enforcement \
  tests.test_organization_security_export \
  tests.test_obligation_tracker tests.test_audit_integrity \
  tests.test_async_job_system tests.test_restore_drill \
  tests.test_seed_payrollminds_demo --verbosity 0
python manage.py test tests.test_restore_drill tests.test_async_job_system \
  tests.test_seed_payrollminds_demo -v 1
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py audit_null_organizations
```

All commands above returned exit status 0. The focused restore/job/seed command
reported 26 tests in 1.756s. Its expected `SimpleTestCase` audit-append warning
is tracked as PM-UAT-08 rather than omitted.
