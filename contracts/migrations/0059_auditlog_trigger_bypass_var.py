"""Update the append-only trigger to honour the cms.audit_bypass session variable.

Setting ``SET LOCAL cms.audit_bypass = 'true'`` within a transaction allows the
Python model (AuditLog.save / AuditLog.delete with _allow_audit_update/
_allow_audit_delete) to write tamper-simulation rows in tests.  The variable is
transaction-scoped so it cannot leak across requests.
"""
from django.db import migrations

_UPDATE_SQL = """
CREATE OR REPLACE FUNCTION contracts_auditlog_append_only()
RETURNS trigger AS $$
BEGIN
    IF current_setting('cms.audit_bypass', true) = 'true' THEN
        -- UPDATE: return NEW to allow the modification.
        -- DELETE: return OLD to allow the deletion.
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;
    RAISE EXCEPTION 'contracts_auditlog is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;
"""

_REVERT_SQL = """
CREATE OR REPLACE FUNCTION contracts_auditlog_append_only()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'contracts_auditlog is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;
"""


def update_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_UPDATE_SQL)


def revert_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_REVERT_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0058_scheduledjobrun_alert_sent_at'),
    ]

    operations = [
        migrations.RunPython(update_trigger, reverse_code=revert_trigger),
    ]
