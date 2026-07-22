"""PAR-ID-001 characterization tests — lock interim dual-role semantics before reconciliation.

These tests document current behavior that MUST remain truthful during discovery
and MUST be preserved or explicitly migrated during Role Definition reconciliation.
No schema changes; no privilege model changes.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from contracts.models import (
    ApprovalRequest,
    ApprovalRule,
    Contract,
    Organization,
    OrganizationMembership,
    SignatureRequest,
    UserProfile,
    Workflow,
    WorkflowStep,
    WorkflowTemplate,
    WorkflowTemplateStep,
)
from contracts.nav_config import get_nav_for
from contracts.permissions import (
    ContractAction,
    can_access_contract_action,
    can_manage_organization,
)
from contracts.services.approval_workflow import ApprovalAccessDenied, authorize_approval_actor
from contracts.services.workflow_routing import resolve_rule_assignee


User = get_user_model()


class RoleDefinitionInterimCharacterizationTests(TestCase):
    """Baseline semantics while OrganizationMembership.Role and UserProfile.Role coexist."""

    def setUp(self):
        self.org = Organization.objects.create(name='Role Char Org', slug='role-char-org')
        self.owner_user = User.objects.create_user(username='role-owner', password='pass12345')
        self.member_user = User.objects.create_user(username='role-member', password='pass12345')

        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.owner_user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.member_user,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        UserProfile.objects.create(user=self.owner_user, role=UserProfile.Role.ADMIN)
        UserProfile.objects.create(user=self.member_user, role=UserProfile.Role.ASSOCIATE)

    def test_organization_membership_role_is_independent_of_user_profile_role(self):
        """Pilot pattern: MEMBER org role + ASSOCIATE process role is valid."""
        membership = OrganizationMembership.objects.get(user=self.member_user, organization=self.org)
        profile = UserProfile.objects.get(user=self.member_user)
        self.assertEqual(membership.role, OrganizationMembership.Role.MEMBER)
        self.assertEqual(profile.role, UserProfile.Role.ASSOCIATE)
        self.assertNotEqual(membership.role, profile.role)

    def test_admin_exists_in_both_enums_with_different_meaning(self):
        """ADMIN in org membership vs profile are distinct concepts — must not be conflated."""
        owner_membership = OrganizationMembership.objects.get(user=self.owner_user, organization=self.org)
        owner_profile = UserProfile.objects.get(user=self.owner_user)
        self.assertEqual(owner_membership.role, OrganizationMembership.Role.OWNER)
        self.assertEqual(owner_profile.role, UserProfile.Role.ADMIN)
        self.assertIn('ADMIN', OrganizationMembership.Role.values)
        self.assertIn('ADMIN', UserProfile.Role.values)

    def test_organization_membership_role_choices_are_workspace_scoped(self):
        self.assertEqual(
            set(OrganizationMembership.Role.values),
            {'OWNER', 'ADMIN', 'MEMBER'},
        )

    def test_user_profile_role_choices_are_process_scoped(self):
        self.assertEqual(
            set(UserProfile.Role.values),
            {
                'PARTNER',
                'SENIOR_ASSOCIATE',
                'ASSOCIATE',
                'PARALEGAL',
                'LEGAL_ASSISTANT',
                'ADMIN',
                'CLIENT',
            },
        )

    def test_membership_role_does_not_auto_sync_to_profile_role(self):
        """No automatic sync — profile is created separately with its own default."""
        new_user = User.objects.create_user(username='role-new', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=new_user,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )
        self.assertFalse(UserProfile.objects.filter(user=new_user).exists())
        profile, _ = UserProfile.objects.get_or_create(user=new_user)
        self.assertEqual(profile.role, UserProfile.Role.ASSOCIATE)  # model default
        membership = OrganizationMembership.objects.get(user=new_user, organization=self.org)
        self.assertEqual(membership.role, OrganizationMembership.Role.ADMIN)
        self.assertNotEqual(membership.role, profile.role)


class WorkspaceRoleCharacterizationTests(TestCase):
    """OrganizationMembership.Role gates workspace authority — not process roles."""

    def setUp(self):
        self.org = Organization.objects.create(name='WS Role Org', slug='ws-role-org')
        self.owner = User.objects.create_user(username='ws-owner', password='pass12345')
        self.admin = User.objects.create_user(username='ws-admin', password='pass12345')
        self.member = User.objects.create_user(username='ws-member', password='pass12345')
        for user, role in [
            (self.owner, OrganizationMembership.Role.OWNER),
            (self.admin, OrganizationMembership.Role.ADMIN),
            (self.member, OrganizationMembership.Role.MEMBER),
        ]:
            OrganizationMembership.objects.create(
                organization=self.org, user=user, role=role, is_active=True,
            )
            UserProfile.objects.create(user=user, role=UserProfile.Role.ASSOCIATE)

    def test_owner_and_admin_can_manage_organization(self):
        self.assertTrue(can_manage_organization(self.owner, self.org))
        self.assertTrue(can_manage_organization(self.admin, self.org))
        self.assertFalse(can_manage_organization(self.member, self.org))

    def test_member_cannot_edit_others_contract_without_ownership(self):
        contract = Contract.objects.create(
            organization=self.org,
            title='WS Contract',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.owner,
            owner=self.owner,
        )
        self.assertTrue(can_access_contract_action(self.owner, contract, ContractAction.EDIT))
        self.assertTrue(can_access_contract_action(self.admin, contract, ContractAction.EDIT))
        self.assertFalse(can_access_contract_action(self.member, contract, ContractAction.EDIT))

    def test_member_can_edit_own_contract(self):
        contract = Contract.objects.create(
            organization=self.org,
            title='Member Contract',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.member,
            owner=self.member,
        )
        self.assertTrue(can_access_contract_action(self.member, contract, ContractAction.EDIT))


class WorkflowRoleDefinitionCharacterizationTests(TestCase):
    """UserProfile.Role used for template assignee and approval rule resolution."""

    def setUp(self):
        self.org = Organization.objects.create(name='WF Role Org', slug='wf-role-org')
        self.associate = User.objects.create_user(username='wf-associate', password='pass12345')
        self.paralegal = User.objects.create_user(username='wf-paralegal', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.associate, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.paralegal, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        UserProfile.objects.create(user=self.associate, role=UserProfile.Role.ASSOCIATE)
        UserProfile.objects.create(user=self.paralegal, role=UserProfile.Role.PARALEGAL)
        self.contract = Contract.objects.create(
            organization=self.org,
            title='WF Role Contract',
            contract_type=Contract.ContractType.MSA,
            status=Contract.Status.IN_PROGRESS,
            created_by=self.associate,
        )
        self.template = WorkflowTemplate.objects.create(
            name='Role Template',
            organization=self.org,
            category=WorkflowTemplate.Category.GENERAL,
            version=1,
            is_active=True,
        )
        self.step = WorkflowTemplateStep.objects.create(
            template=self.template,
            name='Review',
            order=1,
            step_kind=WorkflowTemplateStep.StepKind.TASK,
            assignee_role=UserProfile.Role.ASSOCIATE,
        )
        self.rule = ApprovalRule.objects.create(
            organization=self.org,
            name='Legal rule',
            trigger_type=ApprovalRule.TriggerType.CONTRACT_TYPE,
            trigger_value=Contract.ContractType.MSA,
            approval_step='LEGAL',
            approver_role=UserProfile.Role.ASSOCIATE,
            order=1,
            is_active=True,
        )

    def test_template_step_resolve_assignee_matches_profile_role_in_org(self):
        resolved = self.step.resolve_assignee(self.contract)
        self.assertEqual(resolved, self.associate)

    def test_approval_rule_resolve_assignee_matches_profile_role_in_org(self):
        resolved = resolve_rule_assignee(self.rule, self.contract)
        self.assertEqual(resolved, self.associate)

    def test_missing_profile_role_returns_none_assignee(self):
        self.step.assignee_role = UserProfile.Role.PARTNER
        self.step.save(update_fields=['assignee_role'])
        self.assertIsNone(self.step.resolve_assignee(self.contract))


class RuntimeAssignmentCharacterizationTests(TestCase):
    """Runtime assigned_to is separate from configuration role labels."""

    def setUp(self):
        self.org = Organization.objects.create(name='RT Assign Org', slug='rt-assign-org')
        self.user = User.objects.create_user(username='rt-user', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        UserProfile.objects.create(user=self.user, role=UserProfile.Role.ASSOCIATE)
        self.contract = Contract.objects.create(
            organization=self.org,
            title='RT Contract',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.user,
        )
        self.workflow = Workflow.objects.create(
            organization=self.org,
            title='RT Workflow',
            contract=self.contract,
            created_by=self.user,
        )
        self.step = WorkflowStep.objects.create(
            workflow=self.workflow,
            name='Manual Step',
            order=1,
            assigned_to=self.user,
        )

    def test_runtime_step_assignment_persists_independently_of_template(self):
        self.assertEqual(self.step.assigned_to_id, self.user.id)
        profile = UserProfile.objects.get(user=self.user)
        profile.role = UserProfile.Role.PARALEGAL
        profile.save(update_fields=['role'])
        self.step.refresh_from_db()
        self.assertEqual(self.step.assigned_to_id, self.user.id)


class DelegationCharacterizationTests(TestCase):
    """Delegation grants acting authority without changing original assignee."""

    def setUp(self):
        self.org = Organization.objects.create(name='Del Org', slug='del-org')
        self.assignee = User.objects.create_user(username='del-assignee', password='pass12345')
        self.delegate = User.objects.create_user(username='del-delegate', password='pass12345')
        self.owner = User.objects.create_user(username='del-owner', password='pass12345')
        for user, role in [
            (self.assignee, OrganizationMembership.Role.MEMBER),
            (self.delegate, OrganizationMembership.Role.MEMBER),
            (self.owner, OrganizationMembership.Role.OWNER),
        ]:
            OrganizationMembership.objects.create(
                organization=self.org, user=user, role=role, is_active=True,
            )
            UserProfile.objects.create(user=user, role=UserProfile.Role.ASSOCIATE)
        self.contract = Contract.objects.create(
            organization=self.org,
            title='Del Contract',
            contract_type=Contract.ContractType.MSA,
            status=Contract.Status.IN_PROGRESS,
            created_by=self.owner,
            owner=self.owner,
        )
        self.approval = ApprovalRequest.objects.create(
            organization=self.org,
            contract=self.contract,
            approval_step='LEGAL',
            assigned_to=self.assignee,
            delegated_to=self.delegate,
            status=ApprovalRequest.Status.PENDING,
        )

    def test_delegate_may_act_on_approval(self):
        authorize_approval_actor(self.approval, self.delegate, action='approve')

    def test_original_assignee_preserved_on_delegation(self):
        self.assertEqual(self.approval.assigned_to_id, self.assignee.id)
        self.assertEqual(self.approval.delegated_to_id, self.delegate.id)


class SignerResolutionCharacterizationTests(TestCase):
    """Signer authority is email-based; signer_role is display metadata only."""

    def setUp(self):
        self.org = Organization.objects.create(name='Sig Org', slug='sig-org')
        self.creator = User.objects.create_user(
            username='sig-creator', password='pass12345', email='creator@example.com',
        )
        self.signer = User.objects.create_user(
            username='sig-signer', password='pass12345', email='signer@example.com',
        )
        OrganizationMembership.objects.create(
            organization=self.org, user=self.creator, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.contract = Contract.objects.create(
            organization=self.org,
            title='Sig Contract',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.creator,
        )
        self.packet = SignatureRequest.objects.create(
            organization=self.org,
            contract=self.contract,
            created_by=self.creator,
            signer_email='signer@example.com',
            signer_role='CEO',
            status=SignatureRequest.Status.SENT,
            order=1,
        )

    def test_signer_email_match_allows_sign_transition(self):
        self.assertTrue(
            self.packet.can_actor_transition(self.signer, SignatureRequest.Status.SIGNED),
        )

    def test_signer_role_label_does_not_grant_authority(self):
        outsider = User.objects.create_user(username='sig-outsider', password='pass12345')
        self.assertFalse(
            self.packet.can_actor_transition(outsider, SignatureRequest.Status.SIGNED),
        )


class NavigationVsAuthorizationCharacterizationTests(TestCase):
    """Nav visibility is broader than configuration authority."""

    def setUp(self):
        self.org = Organization.objects.create(name='Nav Org', slug='nav-org')
        self.member = User.objects.create_user(username='nav-member', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        UserProfile.objects.create(user=self.member, role=UserProfile.Role.ASSOCIATE)

    @override_settings(CONTROLLED_PILOT_ENABLED=False)
    def test_member_sees_reviews_nav_but_not_configuration(self):
        nav = get_nav_for(self.org, self.member)
        labels = []
        for entry in nav:
            if entry.get('kind') == 'item':
                labels.append(entry.get('label'))
            for child in entry.get('children', []):
                labels.append(child.get('label'))
        self.assertIn('Reviews & Approvals', labels)
        self.assertNotIn('Workflow Designer', labels)
        self.assertFalse(can_manage_organization(self.member, self.org))


class CrossTenantRoleCharacterizationTests(TestCase):
    """Cross-tenant role resolution and authorization must fail safely."""

    def setUp(self):
        self.org_a = Organization.objects.create(name='Org A', slug='org-a-x')
        self.org_b = Organization.objects.create(name='Org B', slug='org-b-x')
        self.user_a = User.objects.create_user(username='cta-user-a', password='pass12345')
        self.user_b = User.objects.create_user(username='cta-user-b', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.org_a, user=self.user_a, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org_b, user=self.user_b, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        UserProfile.objects.create(user=self.user_a, role=UserProfile.Role.ASSOCIATE)
        UserProfile.objects.create(user=self.user_b, role=UserProfile.Role.ASSOCIATE)
        self.contract_a = Contract.objects.create(
            organization=self.org_a,
            title='CTA Contract A',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.user_a,
        )
        self.approval_a = ApprovalRequest.objects.create(
            organization=self.org_a,
            contract=self.contract_a,
            approval_step='LEGAL',
            assigned_to=self.user_a,
            status=ApprovalRequest.Status.PENDING,
        )

    def test_cross_tenant_approval_actor_denied_as_not_found(self):
        with self.assertRaises(ApprovalAccessDenied) as ctx:
            authorize_approval_actor(self.approval_a, self.user_b, action='approve')
        self.assertEqual(ctx.exception.status_code, 404)

    def test_resolve_assignee_scoped_to_contract_organization(self):
        template = WorkflowTemplate.objects.create(
            name='CTA Template',
            organization=self.org_a,
            category=WorkflowTemplate.Category.GENERAL,
            version=1,
            is_active=True,
        )
        step = WorkflowTemplateStep.objects.create(
            template=template,
            name='CTA Step',
            order=1,
            step_kind=WorkflowTemplateStep.StepKind.TASK,
            assignee_role=UserProfile.Role.ASSOCIATE,
        )
        resolved = step.resolve_assignee(self.contract_a)
        self.assertEqual(resolved, self.user_a)
        contract_b = Contract.objects.create(
            organization=self.org_b,
            title='CTA Contract B',
            contract_type=Contract.ContractType.NDA,
            status=Contract.Status.ACTIVE,
            created_by=self.user_b,
        )
        self.assertEqual(step.resolve_assignee(contract_b), self.user_b)
