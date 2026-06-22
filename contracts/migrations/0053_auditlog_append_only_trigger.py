"""Database-level append-only protection for AuditLog (PostgreSQL only).

Defense-in-depth on top of the application guards (model save/delete overrides,
read-only admin, queryset update/delete blocks): a trigger that rejects UPDATE
and DELETE on contracts_auditlog. This is a no-op on SQLite (used in tests),
where the application-level guards still apply.

This makes the store tamper-EVIDENT and application-append-only. It does not
defend against a database superuser who disables the trigger; a privileged
repair path must drop/recreate it explicitly and should be separately recorded.
"""
from django.db import migrations

_TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION contracts_auditlog_append_only()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'contracts_auditlog is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS contracts_auditlog_no_update ON contracts_auditlog;
CREATE TRIGGER contracts_auditlog_no_update
    BEFORE UPDATE ON contracts_auditlog
    FOR EACH ROW EXECUTE FUNCTION contracts_auditlog_append_only();

DROP TRIGGER IF EXISTS contracts_auditlog_no_delete ON contracts_auditlog;
CREATE TRIGGER contracts_auditlog_no_delete
    BEFORE DELETE ON contracts_auditlog
    FOR EACH ROW EXECUTE FUNCTION contracts_auditlog_append_only();
"""

_DROP_SQL = """
DROP TRIGGER IF EXISTS contracts_auditlog_no_update ON contracts_auditlog;
DROP TRIGGER IF EXISTS contracts_auditlog_no_delete ON contracts_auditlog;
DROP FUNCTION IF EXISTS contracts_auditlog_append_only();
"""


def install_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_TRIGGER_SQL)


def remove_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_DROP_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0052_audit_chain_fields'),
    ]

    operations = [
        migrations.RunPython(install_trigger, remove_trigger),
    ]
