"""PAR-ID-001 R1 CERTAIN non-ADMIN remediation tests."""

from __future__ import annotations

import json
import uuid
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from contracts.models import (
    Organization,
    OrganizationMembership,
    ProcessRoleAssignment,
    UserProfile,
)
from contracts.services.process_role_assignment import create_process_role_assignment
from contracts.services.process_role_r1_remediation import (
    R1_AUTHORIZED_KEYS,
    R1ScopeError,
    apply_r1_remediation,
    plan_r1_remediation,
    rollback_r1_remediation,
)
from contracts.services.role_definition import ensure_canonical_role_definitions


User = get_user_model()

CORPUS = [
    ('demo-firm', 'jsmith', UserProfile.Role.PARTNER, 'partner_reviewer'),
    ('demo-firm', 'sjones', UserProfile.Role.SENIOR_ASSOCIATE, 'senior_reviewer'),
    ('demo-firm', 'mwilson', UserProfile.Role.PARALEGAL, 'paralegal_reviewer'),
    ('clmone-demo', 'demo_partner', UserProfile.Role.PARTNER, 'partner_reviewer'),
    ('clmone-demo', 'demo_associate', UserProfile.Role.SENIOR_ASSOCIATE, 'senior_reviewer'),
    ('clmone-demo', 'demo_paralegal', UserProfile.Role.PARALEGAL, 'paralegal_reviewer'),
    ('clmone-mvp', 'mvp_owner', UserProfile.Role.ASSOCIATE, 'legal_reviewer'),
    ('clmone-mvp', 'mvp_reviewer', UserProfile.Role.SENIOR_ASSOCIATE, 'senior_reviewer'),
    ('controlled-pilot-org', 'pilot_requester', UserProfile.Role.PARALEGAL, 'paralegal_reviewer'),
    ('controlled-pilot-org', 'pilot_legal', UserProfile.Role.ASSOCIATE, 'legal_reviewer'),
    ('payrollminds-demo', 'payrollminds_legal', UserProfile.Role.SENIOR_ASSOCIATE, 'senior_reviewer'),
    ('payrollminds-demo', 'payrollminds_procurement', UserProfile.Role.ASSOCIATE, 'legal_reviewer'),
]

ADMIN_EXCLUSIONS = [
    ('demo-firm', 'admin', UserProfile.Role.ADMIN),
    ('clmone-demo', 'demo_admin', UserProfile.Role.ADMIN),
    ('clmone-mvp', 'mvp_admin', UserProfile.Role.ADMIN),
    ('controlled-pilot-org', 'pilot_owner', UserProfile.Role.ADMIN),
    ('controlled-pilot-org', 'pilot_admin', UserProfile.Role.ADMIN),
    ('controlled-pilot-org', 'pilot_finance', UserProfile.Role.ADMIN),
    ('payrollminds-demo', 'payrollminds_admin', UserProfile.Role.ADMIN),
    ('payrollminds-demo', 'payrollminds_finance', UserProfile.Role.ADMIN),
]


@override_settings(
    PROCESS_ROLE_SHADOW_WRITE_ENABLED=False,
    PROCESS_ROLE_PARITY_REPORTING_ENABLED=False,
    PROCESS_ROLE_RESOLVER_PARITY_ENABLED=False,
    PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED=False,
)
class R1CertainRemediationTests(TestCase):
    def setUp(self):
        self.orgs = {}
        for slug, username, role, _code in CORPUS:
            if slug not in self.orgs:
                self.orgs[slug] = Organization.objects.create(name=slug, slug=slug)
                ensure_canonical_role_definitions(self.orgs[slug])
            org = self.orgs[slug]
            user = User.objects.create_user(username=username, password='pass12345')
            OrganizationMembership.objects.create(
                organization=org,
                user=user,
                role=OrganizationMembership.Role.MEMBER,
                is_active=True,
            )
            UserProfile.objects.create(user=user, role=role)

        for slug, username, role in ADMIN_EXCLUSIONS:
            org = self.orgs[slug]
            user = User.objects.create_user(username=username, password='pass12345')
            OrganizationMembership.objects.create(
                organization=org,
                user=user,
                role=OrganizationMembership.Role.ADMIN,
                is_active=True,
            )
            UserProfile.objects.create(user=user, role=role)

        self.foreign = Organization.objects.create(name='Foreign', slug='foreign-tenant')
        ensure_canonical_role_definitions(self.foreign)
        fu = User.objects.create_user(username='foreign_user', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.foreign, user=fu, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        # Non-CERTAIN / out-of-manifest role so discovery does not expand R1 scope.
        UserProfile.objects.create(user=fu, role=UserProfile.Role.ADMIN)

    def test_dry_run_exact_scope(self):
        plan = plan_r1_remediation()
        self.assertTrue(plan['scope_valid'])
        self.assertEqual(plan['to_create_count'], 12)
        self.assertEqual(plan['authorized_count'], 12)
        keys = {
            (r['organization_slug'], r['username'], r['profile_role'], r['mapped_code'], r['rule_id'])
            for r in plan['to_create']
        }
        self.assertEqual(keys, R1_AUTHORIZED_KEYS)

    def test_scope_mismatch_fails_closed(self):
        User.objects.filter(username='jsmith').delete()
        with self.assertRaises(R1ScopeError):
            plan_r1_remediation()

    def test_apply_creates_exactly_twelve(self):
        result = apply_r1_remediation()
        self.assertEqual(result['created_count'], 12)
        self.assertEqual(result['skipped_count'], 0)
        self.assertTrue(result['remediation_run_id'])
        active = ProcessRoleAssignment.objects.filter(is_active=True)
        self.assertEqual(active.count(), 12)
        self.assertEqual(active.filter(mapping_confidence='CERTAIN').count(), 12)
        self.assertEqual(active.filter(role_definition__code='legacy_process_admin').count(), 0)
        self.assertEqual(ProcessRoleAssignment.objects.filter(organization=self.foreign).count(), 0)

    def test_idempotent_second_apply(self):
        first = apply_r1_remediation()
        second = apply_r1_remediation()
        self.assertEqual(first['created_count'], 12)
        self.assertEqual(second['created_count'], 0)
        self.assertEqual(second['skipped_count'], 12)
        self.assertEqual(ProcessRoleAssignment.objects.filter(is_active=True).count(), 12)

    def test_admin_exclusion(self):
        apply_r1_remediation()
        for _slug, username, _role in ADMIN_EXCLUSIONS:
            user = User.objects.get(username=username)
            self.assertFalse(
                ProcessRoleAssignment.objects.filter(user=user, is_active=True).exists(),
                msg=f'ADMIN user {username} must not receive PRA',
            )

    def test_preserve_existing_assignment(self):
        org = self.orgs['demo-firm']
        user = User.objects.get(username='jsmith')
        membership = OrganizationMembership.objects.get(organization=org, user=user)
        role_def = org.role_definitions.get(code='partner_reviewer')
        create_process_role_assignment(
            organization=org,
            user=user,
            membership=membership,
            role_definition=role_def,
            assignment_source='MANUAL',
            mapping_confidence='CERTAIN',
            assignment_reason='pre-existing',
            actor=None,
            skip_authz=True,
        )
        result = apply_r1_remediation()
        self.assertEqual(result['created_count'], 11)
        self.assertEqual(result['skipped_count'], 1)
        existing = ProcessRoleAssignment.objects.get(
            organization=org, user=user, role_definition=role_def, is_active=True,
        )
        self.assertEqual(existing.assignment_source, 'MANUAL')
        self.assertEqual(existing.assignment_reason, 'pre-existing')

    def test_provenance_and_run_id(self):
        run_id = str(uuid.uuid4())
        result = apply_r1_remediation(run_id=run_id)
        self.assertEqual(result['remediation_run_id'], run_id)
        for row in result['created']:
            self.assertEqual(row['remediation_run_id'], run_id)
            self.assertEqual(row['provenance']['mapping_confidence'], 'CERTAIN')
            self.assertEqual(row['provenance']['assignment_source'], 'LEGACY_BACKFILL')
        for a in ProcessRoleAssignment.objects.filter(is_active=True):
            self.assertIn(f'r1_remediation_run_id={run_id}', a.assignment_reason)
            self.assertEqual(a.legacy_source_field, 'profile_role')

    def test_rollback_by_run_id(self):
        run_id = str(uuid.uuid4())
        apply_r1_remediation(run_id=run_id)
        org = self.orgs['demo-firm']
        other = User.objects.create_user(username='other_manual', password='pass12345')
        OrganizationMembership.objects.create(
            organization=org, user=other, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        create_process_role_assignment(
            organization=org,
            user=other,
            membership=OrganizationMembership.objects.get(organization=org, user=other),
            role_definition=org.role_definitions.get(code='legal_reviewer'),
            assignment_source='MANUAL',
            mapping_confidence='CERTAIN',
            assignment_reason='keep-me',
            skip_authz=True,
        )
        rb = rollback_r1_remediation(run_id=run_id)
        self.assertEqual(rb['deactivated_count'], 12)
        self.assertEqual(
            ProcessRoleAssignment.objects.filter(is_active=True, assignment_reason__contains=run_id).count(),
            0,
        )
        self.assertTrue(
            ProcessRoleAssignment.objects.filter(user=other, is_active=True, assignment_reason='keep-me').exists()
        )

    def test_feature_flags_remain_false(self):
        from django.conf import settings

        apply_r1_remediation()
        self.assertFalse(settings.PROCESS_ROLE_SHADOW_WRITE_ENABLED)
        self.assertFalse(settings.PROCESS_ROLE_PARITY_REPORTING_ENABLED)
        self.assertFalse(settings.PROCESS_ROLE_RESOLVER_PARITY_ENABLED)
        self.assertFalse(settings.PROCESS_ROLE_CANONICAL_RESOLVER_ENABLED)

    def test_management_command_dry_run_and_apply(self):
        out = StringIO()
        call_command('process_role_r1_certain_remediation', '--dry-run', '--json', stdout=out)
        plan = json.loads(out.getvalue())
        self.assertEqual(plan['to_create_count'], 12)
        out2 = StringIO()
        call_command('process_role_r1_certain_remediation', '--apply', '--json', stdout=out2)
        applied = json.loads(out2.getvalue())
        self.assertEqual(applied['created_count'], 12)
        run_id = applied['remediation_run_id']
        out3 = StringIO()
        call_command(
            'process_role_r1_certain_remediation', '--rollback', f'--run-id={run_id}', '--json', stdout=out3,
        )
        rolled = json.loads(out3.getvalue())
        self.assertEqual(rolled['deactivated_count'], 12)
