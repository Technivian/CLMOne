# PayrollMinds production operations readiness

**Status:** **NO-GO for PayrollMinds customer onboarding.**

**Evidence capture date:** 2026-08-17
**Canonical production code SHA:** `935baf83d981204928ba4ca38984076e7b451085`
**Evidence boundary:** This record distinguishes operator attestation and
repository evidence from facts independently observed in a provider console.
It creates no production configuration, data, deployment, provider account,
or contract-type change.

## Current production scope

The Product/Release Owner attests that the deployed controlled-pilot scope is:

| Contract type | Current state |
| --- | --- |
| MSA | ACTIVE |
| NDA | ACTIVE |
| DPA | ACTIVE |
| Order Confirmation | ACTIVE |
| Purchase Order | ACTIVE |
| Every other contract type | INACTIVE |

The single production launch-eligibility control is:

```text
PAYROLLMINDS_ENABLED_CONTRACT_TYPES=MSA,NDA,DPA,ORDER_CONFIRMATION,PURCHASE_ORDER
```

The operator attests that the prior and rollback value is
`MSA,NDA,DPA`; `CONTROLLED_PILOT_ENABLED` remains on; private-by-default
access under PDR-0008 is live; Render Auto-Deploy remains off; no schema
migration was required; and the activation did not modify production contract
data. Health and application/login checks are operator-verified green. This
repository has not independently inspected the Render console, so none of
those attestations is represented as provider-console evidence.

The allowlist changes only contract-type launch eligibility. It does not alter
tenant isolation, private owner/creator access, document/workflow/export
inheritance, or the AI boundary. External AI, inbound email, signatures,
portals, integrations, generic/legacy imports, and new sharing behavior remain
outside this release.

## Gate matrix

| Gate | Status | Evidence | Owner | Remaining action |
| ---- | ------ | -------- | ----- | ---------------- |
| Production environment | GREEN | Owner attests Render/Frankfurt service live at the canonical SHA; public health/login checks previously returned 200 | Haroon Wahed | Retain operator release record; no deployment action in this evidence task. |
| Private-by-default authorization | GREEN | PDR-0008 production deployment closure and preservation/security evidence in `PRIVATE_BY_DEFAULT_ACCESS_IMPLEMENTATION.md` | Haroon Wahed | Preserve existing access regression coverage. |
| Contract-type scope | GREEN | Owner-attested allowlist above; OC/PO technical evidence and default-off implementation in `ORDER_CONFIRMATION_PO_ACTIVATION_EVIDENCE.md` | Haroon Wahed | Keep every non-listed type off; restore the rollback value on a type-activation incident. |
| Database recovery | GREEN | Haroon Wahed completed an isolated Neon recovery-branch drill on 2026-08-17. Source and recovered read-only manifests matched exactly: 128 public tables, 149 Django migrations, 4 Contracts, identifier-only Contract fingerprint `ff9e0fc04dc813d818adc966f1dbdcdd`, 29 audit events, and zero Documents, DocumentVersions, and WorkflowInstances. The recovered database was queryable; no production restore or production write occurred. | Haroon Wahed | Repeat and retain evidence quarterly and after material database/storage architecture changes; ownership review by 2026-09-30. |
| Document recovery | GREEN | The retained synthetic recovery drill remains separate evidence. On 2026-08-18 the deployed, scheduled-only R2 Worker completed a provider Cron run against the two explicit EU bindings, wrote immutable version-addressed copies and a `SUCCESS` manifest, and advanced last-success only after success. | Haroon Wahed | Retain daily-run evidence and repeat the synthetic restore drill quarterly and after material storage changes. |
| Monitoring | BLOCKED | No external uptime monitor, health alert, deployment/runtime notification, error-reporting sink, alert test, or named notification destination is evidenced; repository configuration alone is not provider proof | Haroon Wahed | Configure and test the minimum monitoring controls below. |
| Security | GREEN | PDR-0008 authorization/tenant/export/audit evidence and operator-attested production deployment; excluded capabilities remain off | Haroon Wahed | Preserve operational access/audit evidence. |
| Dependency scanning | GREEN | Exact-SHA PR #181 security scans, Bandit, pip-audit, npm audit, and TruffleHog are recorded green in `ORDER_CONFIRMATION_PO_ACTIVATION_EVIDENCE.md` | Haroon Wahed | Maintain normal scan gates for later releases. |
| Browser/UAT | GREEN | PR #181 Linux browser matrix 8/8, OC/PO browser 3/3, PayrollMinds UAT, and normalized regression delta `NEW=0`, `MUTATED=0` | Haroon Wahed | Preserve the governed test baseline; do not infer production write smoke. |
| Support ownership | GREEN | Owner decision dated 2026-08-17 assigns Haroon Wahed as bootstrap Support Owner through 2026-09-30 | Haroon Wahed | Replace earlier when a qualified separate owner is formally appointed; the separate support-channel gate remains blocked. |
| Support contact/channel | BLOCKED | Bootstrap Support Owner is assigned, but no authenticated customer contact/channel or test receipt is recorded | Haroon Wahed | Create, publish to the controlled launch audience, and test one authenticated support channel with an escalation path. |
| Incident ownership | GREEN | Owner decision dated 2026-08-17 assigns Haroon Wahed as bootstrap Incident Owner through 2026-09-30 | Haroon Wahed | Replace earlier when a qualified separate owner is formally appointed. |
| Privacy ownership | GREEN | Owner decision dated 2026-08-17 assigns Haroon Wahed as bootstrap Privacy Owner through 2026-09-30 | Haroon Wahed | Replace earlier when a qualified separate owner is formally appointed; retain the separate retention/offboarding gate. |
| Deployment approval | GREEN | PDR-0010 names Haroon Wahed as repository Product, Engineering, Security, and Release Authority; deployment/activation instructions are explicit and SHA-scoped | Haroon Wahed | Retain scoped owner authorization and operator release evidence for each release. |
| Infrastructure/Backup ownership | GREEN | Existing operations evidence and Owner decision dated 2026-08-17 assign Haroon Wahed as Infrastructure/Backup Owner through 2026-09-30 | Haroon Wahed | Replace earlier when a qualified separate owner is formally appointed. |
| Neon retention decision | GREEN | Owner temporarily accepts the documented 6-hour PITR window as one recovery component only, through 2026-09-30 | Haroon Wahed | Reconsider earlier if volume, sensitivity, or dependency materially increases; it does not close database recovery. |
| Rollback | BLOCKED | A configuration rollback value is recorded for type activation; no deliberate operational rollback drill is evidenced | Haroon Wahed | Exercise and record a controlled rollback under an approved window. |
| Audit/provenance | GREEN | PDR-0008 access/provenance evidence and OC/PO canonical lifecycle coverage; activation did not modify production data | Haroon Wahed | Preserve append-only audit and provenance checks. |
| Customer offboarding and production access revocation | BLOCKED | Application access revocation is covered, but no customer support route, retention/offboarding basis, or operational rehearsal is recorded | Haroon Wahed | Record the support route and approved retention/offboarding basis; rehearse the existing access-revocation/offboarding procedure without customer data. |

## Database recovery and Neon retention

### Existing recovery evidence

The prior production migration from Render PostgreSQL to Neon is real recovery
mechanism evidence, not merely a procedure: an operator performed
`pg_dump`/`pg_restore` twice, including a final cutover pass, and compared all
122 tables. It proves that export and restore mechanics can work.

It does **not** prove a recoverable operating posture: the target was the new
production database, no isolated recovery branch was used, RPO/RTO was not
measured, restored access controls were not audited, and no routine backup
schedule or current backup identifier is recorded.

### Retention position

The current canonical repository evidence records Neon free-tier point-in-time
recovery as **6 hours**, verified 2026-08-08. This is the only stated recovery
window. The current value must be checked in the Neon project dashboard before
any decision because retention is a provider-plan property; this evidence task
has no provider access and does not claim a current console reading.

The Owner has temporarily accepted this 6-hour window as one component of the
controlled PayrollMinds recovery posture through **2026-09-30**. It is not
accepted as the sole recovery mechanism; it does not waive backup/restore,
tenant isolation, private-by-default access, audit, provenance, export, or
retention/offboarding requirements; and it must be reconsidered earlier if
production volume, sensitivity, or operational dependency materially
increases. This temporary risk decision does not create a contractual RTO/RPO
SLA. The database-recovery gate is supported by the successful isolated drill
recorded below, and remains subject to the recurring-control requirement.

### Isolated Neon recovery drill evidence — 2026-08-17

**DATABASE RECOVERY = GREEN.** Haroon Wahed completed an authorized isolated
Neon recovery-branch drill. The operator did not supply Neon-console metadata
for publication; this repository therefore records only the supplied
non-secret verification evidence below.

| Manifest metric | Production source at 2026-08-17 15:04:19.345088+00 | Isolated recovered branch at 2026-08-17 15:08:30.910053+00 |
| --- | ---: | ---: |
| Public table count | 128 | 128 |
| Django migration-history count | 149 | 149 |
| Contract count | 4 | 4 |
| Identifier-only Contract fingerprint | `ff9e0fc04dc813d818adc966f1dbdcdd` | `ff9e0fc04dc813d818adc966f1dbdcdd` |
| Document count | 0 | 0 |
| DocumentVersion count | 0 | 0 |
| WorkflowInstance count | 0 | 0 |
| Audit-event count | 29 | 29 |

The recovered database was queryable and the manifest reconciliation was an
**EXACT MATCH**. Schema/table count, Django migration history, application
Contract count, identifier-only Contract fingerprint, and audit-event count
all reconciled. No observed loss existed relative to the selected verified
state. Production writes during the drill were **NONE**; no production restore
was performed.

The elapsed time from source-manifest capture to a successful recovered query
was 251.564965 seconds. Record this conservatively as **end-to-end recovery
drill duration <= 4m12s**. It is not a measurement of Neon branch provisioning
time because separate branch-create and branch-ready timestamps were not
recorded. It does not establish a contractual RTO/RPO SLA.

The current Neon recovery/history-window position remains the previously
accepted temporary **6-hour** constraint. This drill demonstrated successful
recovery to the selected point, not a guarantee for every possible point in
that window. The zero source counts for Documents, DocumentVersions, and
WorkflowInstances mean this drill did not prove recovery of populated examples
of those row types. Document-object recovery is governed separately by the
R2/document-recovery gate and is recorded GREEN below.

The exact non-sensitive aggregate manifest is
`NEON_DATABASE_RECOVERY_MANIFEST.sql`; the operator procedure and retained
evidence requirements are in `OPERATOR_BACKUP_RESTORE_DRILL_RUNBOOK.md` §17.
The temporary isolated recovery branch **may be deleted only after recovery
evidence has been retained**. Its deletion is not claimed by this record.

## Document recovery

**R2 DAILY BACKUP CONTROL = GREEN — DEPLOYED / PROVIDER PROOF VERIFIED.**
**DOCUMENT RECOVERY = GREEN.** The historical 2026-08-17 synthetic recovery
drill remains distinct evidence of deletion isolation and byte-for-byte
restoration. It did not establish the routine control described below.

On 2026-08-18, Cloudflare account `4ef24e2b71c28a8a0272e186db71f889` received
Worker version `7240fb43-a9f2-4cbd-baf5-8348874ea861` from merged main SHA
`aad4e5d175d42072044e921955e679189d15d3d7`. Provider version metadata confirms
only the `scheduled` handler and the exact bindings `PRIMARY_DOCUMENTS` →
`clmone-documents` (`eu`) and `BACKUP_DOCUMENTS` →
`clmone-documents-backup` (`eu`). The Worker remains non-public
(`workers_dev = false`), has no HTTP handler or route, and has no delete
operation. Its sole canonical Cron Trigger is `15 2 * * *` UTC.

For the controlled first-run proof, the trigger was temporarily replaced (not
supplemented) with `*/5 * * * *`, then immediately restored to the sole
canonical daily trigger after one genuine provider Cron execution. That
execution was scheduled at `2026-08-18T19:50:39.000Z`, completed at
`2026-08-18T19:50:44.133Z`, and reported `SUCCESS` with two primary objects
examined, two immutable copies written, 147 bytes copied, and no failures.

The new synthetic non-customer canary key was
`synthetic-backup-control-canaries/20260818T194629Z-3764d7af-ae02-4818-b86c-02720c72c115.txt`.
Its source version was `7e5fe996bfbda816aced8e36387979e8`, source ETag was
`2762dd90fe83f030b204e31c15f1f65a`, and source SHA-256 was
`a0cc555c5f532308ed716b01941e9bb938f7c7e73b7ea8ae6c9a0dfd08900a41`.
The immutable backup key is
`_backup_versions/v1/c3ludGhldGljLWJhY2t1cC1jb250cm9sLWNhbmFyaWVzLzIwMjYwODE4VDE5NDYyOVotMzc2NGQ3YWYtYWUwMi00ODE4LWI4NmMtMDI3MjBjNzJjMTE1LnR4dA/N2U1ZmU5OTZiZmJkYTgxNmFjZWQ4ZTM2Mzg3OTc5ZTg`;
its downloaded SHA-256 matched exactly. The immutable run manifest
`_backup_runs/2026-08-18T19-50-44.133Z-dbca24d3-36fe-4ea2-90be-c7be53bac5cc.json`
has `result = SUCCESS`, and `_backup_control/last-success.json` references
that run only after success.

Provider metadata after the run shows the retained historical primary
`document-recovery-canary.txt` and the pre-existing recovery-bucket object of
the same key remain present with their 2026-08-17 timestamps and unchanged
ETags. The run created only the two version-addressed copies, immutable
manifest, and allowed last-success marker; it did not delete or overwrite a
primary or an existing recovery object, and no source deletion propagated.
No customer/application document, database record, or production contract data
was changed. This is bucket-level recovery isolation only; it does not claim
Cloudflare-account or provider disaster independence or a contractual RTO/RPO.

The continuing operator procedure is in
`OPERATOR_BACKUP_RESTORE_DRILL_RUNBOOK.md` §18 and the daily-control procedure
is in `R2_DAILY_DOCUMENT_BACKUP_DEPLOYMENT_RUNBOOK.md`. Preserve non-secret
provider evidence for each future run; no access key, secret, or document
content belongs in this repository.

## Minimum monitoring requirement

The smallest sufficient monitoring configuration for this deployment is:

1. an external HTTPS monitor for `https://www.clmone.com/_health/` that alerts
   on non-200 or timeout;
2. a named, authenticated notification destination and escalation owner;
3. Render failed-deploy/runtime notification to the same destination; and
4. an application/runtime error sink with redaction and a confirmed test
   alert, or equivalent provider capability that records and notifies on
   unhandled runtime exceptions.

Operator steps: configure the external health monitor without credentials in
the URL; add the approved recipient; configure Render deployment/runtime
notifications; configure the selected error sink without logging documents,
DSNs, tokens, or customer data; trigger one controlled test alert; then record
the monitor URL, recipient role (not address), timestamp, and receipt result.
No external monitoring provider is configured or claimed by this record.

## Bootstrap operational ownership — active Owner decision

On 2026-08-17, the Product/Release Owner assigned the following transparent
bootstrap responsibilities to **Haroon Wahed**. These are not independent
authorities. Each assignment is reviewed by **2026-09-30** and ends earlier
when a qualified separate owner is formally appointed for that responsibility.

| Role | Status | Responsibility and escalation duty |
| --- | --- | --- |
| Support Owner | GREEN | Receive and triage PayrollMinds production issues; coordinate response; maintain an available support contact/channel; immediately escalate security or privacy incidents. |
| Incident Owner | GREEN | Lead incident coordination; decide containment/escalation; preserve evidence; coordinate rollback/recovery; maintain incident records. |
| Privacy Owner | GREEN | Own controlled-launch privacy-impact decisions and privacy escalation; coordinate breach/privacy-event handling; keep sensitive-data handling within approved scope. |
| Deployment Approver | GREEN | Authorize production releases and production configuration changes under the applicable release gate. |
| Infrastructure/Backup Owner | GREEN | Own database/document backup and restore controls; execute and evidence recovery drills; maintain provider/operator recovery procedures. |

The operational Support Owner assignment does **not** create a customer-facing
channel. That channel, its authenticated intake, escalation destination, and
test receipt remain a separate **BLOCKED** gate. Likewise, the Privacy Owner
assignment does not supply the required retention/offboarding basis.

## Onboarding decision

**PayrollMinds customer onboarding remains NO-GO.** Current release and
contract-type activation are not sufficient to onboard customer users or data.
The mandatory remaining actions are:

1. configure and test the minimum external health, deploy/runtime, and
   application-error monitoring with a named notification destination;
2. create and test one authenticated support channel with customer escalation,
   then record it without publishing personal contact details in repository
   evidence; and
3. record an approved retention/offboarding basis before accepting customer
   data, then rehearse the existing user/access offboarding and production
   access-revocation procedure without customer data.

The R2 Worker deployment and synthetic provider proof above did not modify
production application data or activate an additional contract type.
