# PayrollMinds synthetic UAT acceptance sheet

**Status key:** PASS = local code/test evidence only; BLOCKED = required
environment or approval evidence absent; N/A = deliberately excluded. None of
these rows authorizes production use.

| Test IDs | Scenario | Result | Evidence / limitation |
|---|---|---|---|
| 01–02 | authorized and blocked upload | PASS | document-ingestion and private-repository tests exercise clean release and denied object access. |
| 03–04 | bulk upload and duplicate handling | PASS | repository CSV import tests exercise synthetic import and duplicate detection. |
| 05–06 | unsupported/oversized file | PASS | document-ingestion validation tests. Target malware/quarantine operation remains blocked. |
| 07 | extraction success | PASS | local deterministic metadata-preview tests; no provider AI. |
| 08 | extraction failure/manual fallback | PASS | unreadable/no-text states leave manual metadata path available. |
| 09 | human verification | PARTIAL | manual entry/verification exists; complete field-level pre-production record remains required. |
| 10 | rejected AI suggestion | N/A | external AI is disabled; denial is tested and no suggestion exists to reject. |
| 11 | record provenance | PASS | provenance service tests and synthetic seed records. |
| 12–14 | private access, tenant denial, revocation | PASS | object-read/private document/repository tests include negative paths. |
| 15 | permission-aware search/non-leakage | PASS | search/repository enforcement covers denied results, facets and fail-closed paths. |
| 16–18 | date correction, renewal, overdue reminder | PARTIAL | local obligation/renewal tests cover modeled states; no real worker/email delivery evidence. |
| 19 | export authorization | PASS | owner/member organization-security export tests. |
| 20 | audit evidence | PASS | audit-integrity tests cover chain/append-only behavior locally. |
| 21 | job failure and retry | PASS | async job tests exercise synthetic failure/retry behavior. |
| 22 | backup and restore | BLOCKED | restore-service tests pass locally; no PostgreSQL/object-store restoration drill. |
| 23 | production-like deployment | BLOCKED | no isolated pre-production TLS/IAM/worker/monitoring/deploy record. |
| 24 | customer offboarding/export | BLOCKED | procedure exists; no authorized target-environment rehearsal or customer terms. |

**Acceptance result:** not accepted for production. BLOCKED rows include
critical/high launch gates; see the defect register and final recommendation.
