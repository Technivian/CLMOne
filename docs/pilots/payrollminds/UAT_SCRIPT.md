# PayrollMinds synthetic UAT script

**Status:** Draft execution script. Run only against a reset synthetic local or
approved isolated pre-production workspace. Do not use real data.

Use the seeded fictional workspace and a second synthetic workspace for tenant
tests. Keep `CONTROLLED_PILOT_ENABLED=true`, `GEMINI_AI_ENABLED=false`, and
email ingestion disabled. Record SHA, environment, tester, timestamp, test ID,
expected and actual result in the acceptance sheet; never record document bodies
or secrets.

| ID | Scenario | Action / expected result |
|---|---|---|
| UAT-01 | Authorized upload | Authorized owner uploads a clean synthetic fixture; canonical Document and immutable DocumentVersion have workspace and provenance. |
| UAT-02 | Unauthorized upload | Unauthorised member posts to known contract upload URL; receive content-free deny/404 and create nothing. |
| UAT-03/04 | Bulk and duplicate | Import synthetic CSV once and repeat it; duplicate outcome is explicit/idempotent. |
| UAT-05/06 | Invalid file | Submit unsupported then over-limit file; each fails before release with usable error. |
| UAT-07/08 | Extraction/manual fallback | Preview readable synthetic agreement; use unreadable/no-text fixture and complete metadata manually without provider processing. |
| UAT-09/10 | Verification/rejection | Verify manual authoritative fields. Attempt external AI only as negative case: controlled pilot returns 403 and persists no suggestion. |
| UAT-11 | Provenance | Inspect Contract, Document and DocumentVersion provenance/workspace after release. |
| UAT-12–15 | Access/search | Check owner; other workspace denial; revoke membership and recheck; search restricted text/metadata and confirm no result/count leak. |
| UAT-16–18 | Dates/reminders | Confirm/correct date, create renewal/notice and overdue synthetic deadlines, then inspect reminder outcomes. |
| UAT-19/20 | Export/audit | Owner exports controlled evidence; member is denied. Inspect immutable upload, metadata, permission and export events. |
| UAT-21 | Job failure/retry | Force synthetic job failure; confirm explicit failure, retry count and dead-letter state. |
| UAT-22 | Backup/restore | In isolated pre-production, restore a synthetic backup and validate hashes, tenant/audit chain and authorized download. |
| UAT-23 | Production-like deploy | In isolated pre-production, deploy reviewed SHA with private storage, TLS, worker, alert and backup; do not activate public access. |
| UAT-24 | Offboarding/export | Exercise authorized synthetic export/offboarding; verify session/API revocation and retain redacted evidence. |

Stop on a tenant/object leak, public object URL, unlogged export, audit mutation,
provider egress, restoration mismatch, or critical/high defect. Do not work
around a failed control.
