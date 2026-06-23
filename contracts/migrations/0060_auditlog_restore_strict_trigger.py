"""Restore the append-only trigger to unconditionally reject UPDATE and DELETE.

Migration 0059 introduced a cms.audit_bypass session variable that allowed
application code to enable audit mutations through the same database role as
ordinary requests. This violates the Phase 3 guarantee: the append-only guard
must be enforced at the database boundary and must not be bypassable by normal
application code.

This migration reverts to the strict form: any UPDATE or DELETE on
contracts_auditlog always raises an exception, regardless of session state.
Genuine audit repair is reserved for a separately privileged operator procedure
(documented in the runbook); test tampering uses trigger-disable SQL that
requires ALTER TABLE privilege, which is unavailable to the application role.
"""
from django.db import migrations

_STRICT_SQL = """
CREATE OR REPLACE FUNCTION contracts_auditlog_append_only()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'contracts_auditlog is append-only: % is not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;
"""

_BYPASS_SQL = """
CREATE OR REPLACE FUNCTION contracts_auditlog_append_only()
RETURNS trigger AS $$
BEGIN
    IF current_setting('cms.audit_bypass', true) = 'true' THEN
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


def restore_strict_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_STRICT_SQL)


def revert_to_bypass_trigger(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(_BYPASS_SQL)


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0059_auditlog_trigger_bypass_var'),
    ]

    operations = [
        migrations.RunPython(restore_strict_trigger, reverse_code=revert_to_bypass_trigger),
    ]
