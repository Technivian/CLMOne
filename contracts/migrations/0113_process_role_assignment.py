# PAR-ID-001 — organization-scoped process-role assignment adapter (ADR-0014 / auth 0113).

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
from django.utils import timezone


PROFILE_ROLE_MAP = {
    'PARTNER': ('partner_reviewer', 'CERTAIN'),
    'SENIOR_ASSOCIATE': ('senior_reviewer', 'CERTAIN'),
    'ASSOCIATE': ('legal_reviewer', 'CERTAIN'),
    'PARALEGAL': ('paralegal_reviewer', 'CERTAIN'),
    'LEGAL_ASSISTANT': ('legal_assistant', 'CERTAIN'),
    'CLIENT': ('external_participant', 'CERTAIN'),
    'ADMIN': ('legacy_process_admin', 'AMBIGUOUS'),  # NOT workspace_admin
}


def forwards_backfill(apps, schema_editor):
    Organization = apps.get_model('contracts', 'Organization')
    OrganizationMembership = apps.get_model('contracts', 'OrganizationMembership')
    UserProfile = apps.get_model('contracts', 'UserProfile')
    RoleDefinition = apps.get_model('contracts', 'RoleDefinition')
    ProcessRoleAssignment = apps.get_model('contracts', 'ProcessRoleAssignment')

    now = timezone.now()
    for org in Organization.objects.order_by('id'):
        # Ensure catalogue seeds exist (idempotent with 0112 seed).
        # 0112 already seeded; skip if missing codes rather than inventing.
        memberships = OrganizationMembership.objects.filter(organization_id=org.pk, is_active=True)
        for membership in memberships:
            try:
                profile = UserProfile.objects.get(user_id=membership.user_id)
            except UserProfile.DoesNotExist:
                continue
            role_value = (profile.role or '').strip().upper()
            if not role_value:
                continue
            mapped = PROFILE_ROLE_MAP.get(role_value)
            if mapped is None:
                code, confidence = 'legacy_unknown', 'UNKNOWN'
            else:
                code, confidence = mapped
            role_def = RoleDefinition.objects.filter(organization_id=org.pk, code=code).first()
            if role_def is None:
                continue
            exists = ProcessRoleAssignment.objects.filter(
                organization_id=org.pk,
                user_id=membership.user_id,
                role_definition_id=role_def.pk,
                is_active=True,
            ).exists()
            if exists:
                continue
            ProcessRoleAssignment.objects.create(
                organization_id=org.pk,
                user_id=membership.user_id,
                membership_id=membership.pk,
                role_definition_id=role_def.pk,
                assignment_source='LEGACY_BACKFILL',
                legacy_source_field='profile_role',
                legacy_source_value=profile.role,
                mapping_confidence=confidence,
                is_active=True,
                is_system_managed=True,
                effective_start=now,
                assignment_reason='0113 truthful legacy backfill from UserProfile.role',
                correlation_id=uuid.uuid4(),
            )


def backwards_unseed(apps, schema_editor):
    ProcessRoleAssignment = apps.get_model('contracts', 'ProcessRoleAssignment')
    ProcessRoleAssignment.objects.filter(assignment_source='LEGACY_BACKFILL').delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contracts', '0112_role_definition_registry'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessRoleAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assignment_source', models.CharField(
                    choices=[
                        ('MANUAL', 'Manual'),
                        ('LEGACY_BACKFILL', 'Legacy backfill'),
                        ('SYSTEM', 'System'),
                        ('IMPORT', 'Import'),
                    ],
                    max_length=32,
                )),
                ('legacy_source_field', models.CharField(blank=True, default='', max_length=64)),
                ('legacy_source_value', models.CharField(blank=True, default='', max_length=64)),
                ('mapping_confidence', models.CharField(
                    choices=[
                        ('CERTAIN', 'Certain'),
                        ('AMBIGUOUS', 'Ambiguous'),
                        ('UNKNOWN', 'Unknown'),
                    ],
                    default='CERTAIN',
                    max_length=16,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('is_system_managed', models.BooleanField(default=False)),
                ('effective_start', models.DateTimeField()),
                ('effective_end', models.DateTimeField(blank=True, null=True)),
                ('assignment_reason', models.TextField(blank=True, default='')),
                ('correlation_id', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assigned_by', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='process_role_assignments_made', to=settings.AUTH_USER_MODEL,
                )),
                ('membership', models.ForeignKey(
                    blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='process_role_assignments', to='contracts.organizationmembership',
                )),
                ('organization', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='process_role_assignments', to='contracts.organization',
                )),
                ('role_definition', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='assignments', to='contracts.roledefinition',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='process_role_assignments', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['organization_id', 'user_id', 'role_definition_id', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='processroleassignment',
            index=models.Index(fields=['organization', 'user', 'is_active'], name='prole_org_user_active_ix'),
        ),
        migrations.AddIndex(
            model_name='processroleassignment',
            index=models.Index(fields=['organization', 'role_definition', 'is_active'], name='prole_org_role_active_ix'),
        ),
        migrations.AddIndex(
            model_name='processroleassignment',
            index=models.Index(fields=['organization', 'legacy_source_field'], name='prole_org_legacy_ix'),
        ),
        migrations.AddConstraint(
            model_name='processroleassignment',
            constraint=models.UniqueConstraint(
                condition=models.Q(is_active=True),
                fields=('organization', 'user', 'role_definition'),
                name='prole_active_org_user_role_uniq',
            ),
        ),
        migrations.RunPython(forwards_backfill, backwards_unseed),
    ]
