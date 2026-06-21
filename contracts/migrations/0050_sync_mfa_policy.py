"""Backfill OrgPolicy for every organization and reconcile the MFA flags.

Blocker A3: enforcement now reads Organization.require_mfa authoritatively, with
OrgPolicy.mfa_required kept as a mirror. This migration:

  1. Creates an OrgPolicy for any org missing one.
  2. Reconciles the two flags FAIL-CLOSED: if either field currently indicates
     MFA is required, both are set to required. This guarantees no org that had
     MFA configured (via either field) silently loses it during the cutover.
"""
from django.db import migrations


def sync_mfa_flags(apps, schema_editor):
    Organization = apps.get_model('contracts', 'Organization')
    OrgPolicy = apps.get_model('contracts', 'OrgPolicy')

    for org in Organization.objects.all().iterator():
        policy, _ = OrgPolicy.objects.get_or_create(
            organization=org,
            defaults={'mfa_required': org.require_mfa},
        )
        effective = bool(org.require_mfa) or bool(policy.mfa_required)
        if org.require_mfa != effective:
            org.require_mfa = effective
            org.save(update_fields=['require_mfa', 'updated_at'])
        if policy.mfa_required != effective:
            policy.mfa_required = effective
            policy.save(update_fields=['mfa_required', 'updated_at'])


def noop_reverse(apps, schema_editor):
    # Data reconciliation is not reversible; leaving flags as-is is safe.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0049_auditlog_entry_hash'),
    ]

    operations = [
        migrations.RunPython(sync_mfa_flags, noop_reverse),
    ]
