# PayrollMinds backup and restoration evidence

**Status:** Proposed evidence plan — no isolated pre-production or production
restore has been performed for this pilot.

This explicit status preserves the launch-readiness finding PM-OPS-01. Existing
local tests and scripts establish procedure only; they do not prove RPO, RTO,
object storage, permissions, encryption, or restoration in the proposed
environment.

## Required recovery design

| Asset | Backup requirement | Restore validation |
|---|---|---|
| PostgreSQL | encrypted custom-format backup before every release plus provider-managed point-in-time recovery; retention/RPO approved by owner and customer | restore to a separate pre-production database, migrate check, tenant audit, audit-chain verification, authorized smoke |
| Released documents | encrypted private object versioning plus a provider recovery mechanism aligned to the database recovery point | sample authorized downloads, stored hash comparison, no public URL exposure |
| Quarantine objects | separately classified encrypted backup only when ingestion is approved; restricted worker/operator access | reconcile object keys to ingestion attempts; no preview/download; preserve failed/rejected evidence per retention policy |
| Secrets/configuration | secret-manager version/metadata and redacted inventory; never database or object-store backup contents | service boots from references; rotation/revocation rehearsal |
| Audit/events/jobs | included in PostgreSQL backup; never selectively deleted for rollback | `verify_audit_chain`, queue/job reconciliation, immutable evidence review |

## Required restoration drill

1. Use an isolated pre-production project/database/buckets with no production
   traffic and no sharing of production credentials.
2. Record target SHA, source backup ID/time, source/target region evidence,
   operator, expected RPO/RTO, and approval to handle the selected test data.
3. Restore PostgreSQL into a new scratch target. Run:

   ```bash
   python manage.py migrate --check
   python manage.py audit_null_organizations
   python manage.py verify_audit_chain
   ```

4. Restore the corresponding released-object version/recovery point. Verify a
   sample selected by the operator through the authenticated download endpoint
   and compare each stored file hash to its database record.
5. Reconcile document versions, `DocumentIngestionAttempt` rows where enabled,
   `BackgroundJob`/`ScheduledJobRun` rows, memberships, and tenant counts.
6. Measure backup completion, restoration, database boot, object validation,
   and smoke-test durations against the agreed RPO/RTO. Destroy the isolated
   restore target using the provider-approved deletion procedure after evidence
   retention is complete.
7. Attach redacted console output and evidence IDs below. A failed or incomplete
   drill is a no-go; do not convert it into a pass by changing the target.

## Evidence record to complete by operator

| Field | Required value |
|---|---|
| Environment and region | Not supplied |
| Release SHA / backup IDs | Not supplied |
| Backup encryption and retention evidence | Not supplied |
| Start/end and measured RPO/RTO | Not supplied |
| Database restore result | Not performed |
| Object-store restore/hash result | Not performed |
| Tenant/audit/smoke output | Not performed |
| Operator and release decision | Not supplied |

## Local validation available now

`scripts/db_backup.sh` verifies a PostgreSQL custom-format archive is non-empty
and readable by `pg_restore`; `scripts/db_restore_drill.sh` restores an archive
to a scratch database and runs migration/tenant checks. The unit suite
`tests.test_restore_drill` validates the in-app drill record service. None has
been run against an approved PayrollMinds infrastructure target in this PR.
