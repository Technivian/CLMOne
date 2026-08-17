-- PayrollMinds Neon isolated-recovery drill: read-only state manifest.
--
-- Run this unchanged against (1) the production branch at the selected source
-- point and (2) the isolated Neon recovery branch.  It contains no DDL, DML,
-- secrets, contract titles, document content, counterparties, names, email
-- addresses, or payroll/salary fields.  It intentionally fails if a required
-- table is absent: that is schema-recovery evidence, not an error to hide.
--
-- Derived from the current Django model metadata:
--   Contract        contracts_contract        id, organization_id,
--                                            contract_type, owner_id, created_by_id
--   Document        contracts_document
--   DocumentVersion contracts_documentversion
--   WorkflowInstance contracts_workflowinstance
--   AuditLog        contracts_auditlog
--
-- `md5` is PostgreSQL built-in and is used only as a deterministic,
-- non-sensitive structural fingerprint; it is not a cryptographic security
-- control.  Empty result sets deliberately fingerprint as the MD5 of an empty
-- string so the output remains deterministic.

BEGIN TRANSACTION READ ONLY;

WITH manifest_metrics AS (
    SELECT
        'public_schema_table_count'::text AS metric,
        COUNT(*)::text AS value
    FROM pg_catalog.pg_tables
    WHERE schemaname = 'public'

    UNION ALL

    SELECT
        'django_migrations_count',
        COUNT(*)::text
    FROM public.django_migrations

    UNION ALL

    SELECT
        'contract_count',
        COUNT(*)::text
    FROM public.contracts_contract

    UNION ALL

    SELECT
        'document_count',
        COUNT(*)::text
    FROM public.contracts_document

    UNION ALL

    SELECT
        'document_version_count',
        COUNT(*)::text
    FROM public.contracts_documentversion

    UNION ALL

    SELECT
        'workflow_instance_count',
        COUNT(*)::text
    FROM public.contracts_workflowinstance

    UNION ALL

    SELECT
        'audit_event_count',
        COUNT(*)::text
    FROM public.contracts_auditlog

    UNION ALL

    SELECT
        'contract_structural_fingerprint_md5',
        md5(
            COALESCE(
                string_agg(
                    concat_ws(
                        '|',
                        id::text,
                        COALESCE(organization_id::text, 'NULL'),
                        COALESCE(contract_type, 'NULL'),
                        COALESCE(owner_id::text, 'NULL'),
                        COALESCE(created_by_id::text, 'NULL')
                    ),
                    E'\n'
                    ORDER BY id
                ),
                ''
            )
        )
    FROM public.contracts_contract
)
SELECT metric, value
FROM manifest_metrics
ORDER BY metric;

COMMIT;
