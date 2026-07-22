"""PAR-ID-001 — ProcessRoleAssignment adapter tests (migration 0113).

Non-authoritative dual-read / catalogue assignment only.
Must not change permissions, membership authority, or runtime resolvers.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from contracts.models import (
    AuditLog,
    Organization,
    OrganizationMembership,
    ProcessRoleAssignment,
    RoleDefinition,
    UserProfile,
)
from contracts.services.process_role_assignment import (
    EVENT_ASSIGNMENT_CREATED,
    EVENT_ASSIGNMENT_DEACTIVATED,
    EVENT_ASSIGNMENT_DRIFT_DETECTED,
    EVENT_ASSIGNMENT_LEGACY_MAPPED,
    EVENT_ASSIGNMENT_REPAIRED,
    ProcessRoleAssignmentError,
    backfill_process_role_assignments_for_organization,
    create_process_role_assignment,
    deactivate_process_role_assignment,
    dual_read_process_roles,
    repair_process_role_assignment,
    resolve_legacy_process_role_code,
)
from contracts.services.role_definition import ensure_canonical_role_definitions


User = get_user_model()


class ProcessRoleAssignmentTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='PRA Org', slug='pra-org')
        self.org_b = Organization.objects.create(name='PRA Org B', slug='pra-org-b')
        self.owner = User.objects.create_user(username='pra-owner', password='pass12345')
        self.member = User.objects.create_user(username='pra-member', password='pass12345')
        self.outsider = User.objects.create_user(username='pra-outsider', password='pass12345')
        self.m_owner = OrganizationMembership.objects.create(
            organization=self.org, user=self.owner, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.m_member = OrganizationMembership.objects.create(
            organization=self.org, user=self.member, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.outsider, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        UserProfile.objects.create(user=self.owner, role=UserProfile.Role.ADMIN)
        UserProfile.objects.create(user=self.member, role=UserProfile.Role.ASSOCIATE)
        ensure_canonical_role_definitions(self.org)
        ensure_canonical_role_definitions(self.org_b)
        self.legal = RoleDefinition.objects.get(organization=self.org, code='legal_reviewer')
        self.legacy_admin = RoleDefinition.objects.get(organization=self.org, code='legacy_process_admin')

    def test_organization_scoped_assignment(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
            assignment_reason='test',
        )
        self.assertEqual(a.organization_id, self.org.pk)
        self.assertEqual(a.role_definition.code, 'legal_reviewer')

    def test_cross_tenant_rejection(self):
        with self.assertRaises(PermissionDenied):
            create_process_role_assignment(
                organization=self.org,
                user=self.member,
                role_definition=self.legal,
                assignment_source='MANUAL',
                actor=self.outsider,
            )

    def test_membership_user_consistency(self):
        with self.assertRaises(ProcessRoleAssignmentError):
            create_process_role_assignment(
                organization=self.org,
                user=self.member,
                membership=self.m_owner,  # wrong membership user
                role_definition=self.legal,
                assignment_source='MANUAL',
                actor=self.owner,
            )

    def test_duplicate_active_assignment_protection(self):
        create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        with self.assertRaises(ProcessRoleAssignmentError):
            create_process_role_assignment(
                organization=self.org,
                user=self.member,
                membership=self.m_member,
                role_definition=self.legal,
                assignment_source='MANUAL',
                actor=self.owner,
            )

    def test_active_inactive_and_effective_dates(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        self.assertTrue(a.is_active)
        self.assertIsNotNone(a.effective_start)
        deactivate_process_role_assignment(a, actor=self.owner, reason='done')
        a.refresh_from_db()
        self.assertFalse(a.is_active)
        self.assertIsNotNone(a.effective_end)

    def test_immutable_identity_fields(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        a.organization = self.org_b
        with self.assertRaises(ProcessRoleAssignmentError):
            a.save()

    def test_authorized_and_unauthorized_administration(self):
        create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        with self.assertRaises(PermissionDenied):
            create_process_role_assignment(
                organization=self.org,
                user=self.member,
                role_definition=RoleDefinition.objects.get(organization=self.org, code='paralegal_reviewer'),
                assignment_source='MANUAL',
                actor=self.member,
            )

    def test_system_managed_requires_repair_to_deactivate(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='SYSTEM',
            is_system_managed=True,
            actor=self.owner,
        )
        with self.assertRaises(ProcessRoleAssignmentError):
            deactivate_process_role_assignment(a, actor=self.owner)
        repair_process_role_assignment(a, actor=self.owner, reason='deactivate system row', is_active=False)
        a.refresh_from_db()
        self.assertFalse(a.is_active)

    def test_truthful_legacy_mapping_and_ambiguous_admin(self):
        code, conf = resolve_legacy_process_role_code('profile_role', 'ASSOCIATE')
        self.assertEqual((code, conf), ('legal_reviewer', 'CERTAIN'))
        code, conf = resolve_legacy_process_role_code('profile_role', 'ADMIN')
        self.assertEqual(code, 'legacy_process_admin')
        self.assertEqual(conf, 'AMBIGUOUS')
        # Workspace ADMIN mapping remains separate in catalogue lookup — not this assignment code
        self.assertNotEqual(code, 'workspace_admin')

    def test_legacy_unknown(self):
        code, conf = resolve_legacy_process_role_code('profile_role', 'WIZARD')
        self.assertEqual((code, conf), ('legacy_unknown', 'UNKNOWN'))

    def test_backfill_and_dual_read_parity(self):
        stats = backfill_process_role_assignments_for_organization(self.org)
        self.assertGreaterEqual(stats['created'], 2)
        self.assertGreaterEqual(stats['ambiguous'], 1)  # owner profile ADMIN
        report = dual_read_process_roles(organization=self.org, user=self.member)
        self.assertFalse(report['authoritative_for_runtime'])
        codes = {row['code'] for row in report['canonical_assignments']}
        self.assertIn('legal_reviewer', codes)
        legacy_values = {row['source_value'] for row in report['legacy_assignments']}
        self.assertIn(UserProfile.Role.ASSOCIATE, legacy_values)
        # Owner ADMIN collision / ambiguity surfaced
        owner_report = dual_read_process_roles(organization=self.org, user=self.owner)
        self.assertTrue(
            any(c.get('type') in {'ambiguous_legacy', 'admin_name_collision'} for c in owner_report['conflicts'])
            or any(r['mapping_confidence'] == 'AMBIGUOUS' for r in owner_report['legacy_assignments'])
        )
        owner_codes = {row['code'] for row in owner_report['canonical_assignments']}
        self.assertIn('legacy_process_admin', owner_codes)
        self.assertNotIn('workspace_admin', owner_codes)

    def test_dual_read_does_not_mutate_legacy_roles(self):
        before_m = self.m_member.role
        before_p = UserProfile.objects.get(user=self.member).role
        dual_read_process_roles(organization=self.org, user=self.member)
        self.m_member.refresh_from_db()
        self.assertEqual(self.m_member.role, before_m)
        self.assertEqual(UserProfile.objects.get(user=self.member).role, before_p)

    def test_queryset_and_save_guards(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        with self.assertRaises(ProcessRoleAssignmentError):
            ProcessRoleAssignment.objects.filter(pk=a.pk).update(organization=self.org_b)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProcessRoleAssignment.objects.create(
                    organization=self.org,
                    user=self.member,
                    membership=self.m_member,
                    role_definition=self.legal,
                    assignment_source='MANUAL',
                    is_active=True,
                    effective_start=timezone.now(),
                )

    def test_audit_events(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='MANUAL',
            actor=self.owner,
        )
        deactivate_process_role_assignment(a, actor=self.owner, reason='cleanup')
        events = set(
            AuditLog.objects.filter(
                organization=self.org, model_name='ProcessRoleAssignment', object_id=a.pk,
            ).values_list('event_type', flat=True)
        )
        self.assertIn(EVENT_ASSIGNMENT_CREATED, events)
        self.assertIn(EVENT_ASSIGNMENT_DEACTIVATED, events)

    def test_backfill_emits_legacy_mapped_audit(self):
        backfill_process_role_assignments_for_organization(self.org)
        self.assertTrue(
            AuditLog.objects.filter(
                organization=self.org,
                model_name='ProcessRoleAssignment',
                event_type=EVENT_ASSIGNMENT_LEGACY_MAPPED,
            ).exists()
        )

    def test_repair_audit(self):
        a = create_process_role_assignment(
            organization=self.org,
            user=self.member,
            membership=self.m_member,
            role_definition=self.legal,
            assignment_source='SYSTEM',
            is_system_managed=True,
            actor=self.owner,
        )
        repair_process_role_assignment(a, actor=self.owner, reason='fix membership link', membership=self.m_member)
        self.assertTrue(
            AuditLog.objects.filter(
                organization=self.org, model_name='ProcessRoleAssignment',
                object_id=a.pk, event_type=EVENT_ASSIGNMENT_REPAIRED,
            ).exists()
        )

    def test_cross_org_role_definition_rejected(self):
        foreign_role = RoleDefinition.objects.get(organization=self.org_b, code='legal_reviewer')
        with self.assertRaises(ProcessRoleAssignmentError):
            create_process_role_assignment(
                organization=self.org,
                user=self.member,
                membership=self.m_member,
                role_definition=foreign_role,
                assignment_source='MANUAL',
                actor=self.owner,
            )
