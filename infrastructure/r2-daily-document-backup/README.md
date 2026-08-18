# CLM One daily R2 document backup Worker

This isolated Cloudflare Worker is the default-off, deployable implementation
of the at-least-daily PayrollMinds released-document backup control. It has no
HTTP handler and no public route: production execution is `scheduled()` only.

`PRIMARY_DOCUMENTS` binds `clmone-documents`; `BACKUP_DOCUMENTS` binds
`clmone-documents-backup`. Credentials are never present in source: Cloudflare
R2 bindings provide bucket access at deployment.

See [`../../docs/pilots/payrollminds/R2_DAILY_DOCUMENT_BACKUP_DEPLOYMENT_RUNBOOK.md`](../../docs/pilots/payrollminds/R2_DAILY_DOCUMENT_BACKUP_DEPLOYMENT_RUNBOOK.md)
for the operator-only deployment and first-run proof procedure.
