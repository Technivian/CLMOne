"""PAR-ID-001 Slice 3 — feature-flagged shadow sync and parity tests."""

from __future__ import annotations

import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from contracts.models import (
    AuditLog,
    Organization,
    OrganizationMembership,
    ProcessRoleAssignment,
    RoleDefinition,
    UserProfile,
)
from contracts.services.process_role_shadow_sync import (
    EVENT_ASSIGNMENT_SHADOW_SYNC_FAILED,
    maybe_shadow_sync_profile_role,
    shadow_sync_profile_role_for_organization,
)
from contracts.services.role_definition import ensure_canonical_role_definitions


User = get_user_model()


class ProcessRoleShadowSyncTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Shadow Org', slug='shadow-org')
        self.org_b = Organization.objects.create(name='Shadow Org B', slug='shadow-org-b')
        self.user = User.objects.create_user(username='shadow-user', password='pass12345')
        self.owner = User.objects.create_user(username='shadow-owner', password='pass12345')
        self.membership = OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        ensure_canonical_role_definitions(self.org)
        ensure_canonical_role_definitions(self.org_b)

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=False)
    def test_flag_off_leaves_behavior_unchanged(self):
        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        self.assertEqual(
            ProcessRoleAssignment.objects.filter(organization=self.org, user=self.user, is_active=True).count(),
            0,
        )
        profile.role = UserProfile.Role.PARALEGAL
        profile.save()
        self.assertEqual(
            ProcessRoleAssignment.objects.filter(organization=self.org, user=self.user, is_active=True).count(),
            0,
        )
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).role, UserProfile.Role.PARALEGAL)

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_flag_on_idempotent_certain_mapping(self):
        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        qs = ProcessRoleAssignment.objects.filter(
            organization=self.org, user=self.user, is_active=True, role_definition__code='legal_reviewer',
        )
        self.assertEqual(qs.count(), 1)
        # Repeated save — no duplicate
        profile.save()
        self.assertEqual(qs.count(), 1)
        profile.role = UserProfile.Role.ASSOCIATE
        profile.save()
        self.assertEqual(qs.count(), 1)

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_ambiguous_admin_and_membership_admin_not_mapped(self):
        admin_member = User.objects.create_user(username='shadow-admin-m', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org, user=admin_member, role=OrganizationMembership.Role.ADMIN, is_active=True,
        )
        profile = UserProfile.objects.create(user=admin_member, role=UserProfile.Role.ADMIN)
        codes = set(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=admin_member, is_active=True,
            ).values_list('role_definition__code', flat=True)
        )
        self.assertIn('legacy_process_admin', codes)
        self.assertNotIn('workspace_admin', codes)
        # Membership ADMIN alone does not create process assignment for another user
        self.assertFalse(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.owner, role_definition__code='workspace_admin', is_active=True,
            ).exists()
        )
        self.assertEqual(profile.role, UserProfile.Role.ADMIN)

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_role_change_deactivates_previous_assignment(self):
        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        self.assertTrue(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.user, role_definition__code='legal_reviewer', is_active=True,
            ).exists()
        )
        profile.role = UserProfile.Role.PARALEGAL
        profile.save()
        self.assertFalse(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.user, role_definition__code='legal_reviewer', is_active=True,
            ).exists()
        )
        self.assertTrue(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.user, role_definition__code='paralegal_reviewer', is_active=True,
            ).exists()
        )

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_tenant_mismatch_fails_closed_and_preserves_legacy(self):
        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        # Force sync against org without membership
        with self.assertRaises(PermissionError):
            shadow_sync_profile_role_for_organization(
                organization=self.org_b,
                user=self.user,
                profile_role=UserProfile.Role.ASSOCIATE,
            )
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).role, UserProfile.Role.ASSOCIATE)
        self.assertFalse(
            ProcessRoleAssignment.objects.filter(organization=self.org_b, user=self.user).exists()
        )

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_shadow_failure_preserves_legacy_and_audits(self):
        from unittest.mock import patch

        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        # Inject shadow failure after legacy write path; UserProfile.role must remain authoritative.
        with patch(
            'contracts.services.process_role_shadow_sync.shadow_sync_profile_role_for_organization',
            side_effect=RuntimeError('injected shadow failure'),
        ):
            profile.role = UserProfile.Role.PARTNER
            profile.save()
        self.assertEqual(UserProfile.objects.get(pk=profile.pk).role, UserProfile.Role.PARTNER)
        self.assertTrue(
            AuditLog.objects.filter(
                organization=self.org,
                event_type=EVENT_ASSIGNMENT_SHADOW_SYNC_FAILED,
            ).exists()
        )

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_queryset_update_triggers_shadow(self):
        profile = UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        UserProfile.objects.filter(pk=profile.pk).update(role=UserProfile.Role.CLIENT)
        self.assertTrue(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.user, role_definition__code='external_participant', is_active=True,
            ).exists()
        )

    @override_settings(PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
    def test_seed_style_update_or_create(self):
        UserProfile.objects.update_or_create(
            user=self.user, defaults={'role': UserProfile.Role.SENIOR_ASSOCIATE},
        )
        self.assertTrue(
            ProcessRoleAssignment.objects.filter(
                organization=self.org, user=self.user, role_definition__code='senior_reviewer', is_active=True,
            ).exists()
        )


@override_settings(PROCESS_ROLE_PARITY_REPORTING_ENABLED=True, PROCESS_ROLE_SHADOW_WRITE_ENABLED=True)
class ProcessRoleParityReportTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Parity Org', slug='parity-org')
        self.user = User.objects.create_user(username='parity-user', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        ensure_canonical_role_definitions(self.org)

    def test_parity_clean_after_shadow(self):
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        out = StringIO()
        # Should exit 0 — no critical drift
        try:
            call_command('process_role_parity_report', '--organization-id', str(self.org.pk), stdout=out)
            code = 0
        except SystemExit as exc:
            code = exc.code
        self.assertEqual(code, 0)

    def test_parity_json_and_critical_drift_exit(self):
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        # Remove canonical assignment to force critical drift
        ProcessRoleAssignment.objects.filter(organization=self.org, user=self.user).update(is_active=False)
        # Bypass queryset guard for is_active-only update — use save path
        for a in ProcessRoleAssignment.objects.filter(organization=self.org, user=self.user):
            a.is_active = False
            a.save()
        out = StringIO()
        with self.assertRaises(SystemExit) as ctx:
            call_command(
                'process_role_parity_report',
                '--organization-id', str(self.org.pk),
                '--json',
                stdout=out,
            )
        self.assertEqual(ctx.exception.code, 1)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload['summary']['authoritative_for_runtime'])
        self.assertGreaterEqual(payload['summary']['critical_drift_rows'], 1)
