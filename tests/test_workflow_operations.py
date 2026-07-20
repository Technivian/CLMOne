"""Regression tests for Workflow Operations (instance queue, not Designer)."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from contracts.models import (
    ApprovalRequest,
    ApprovalRule,
    Contract,
    Organization,
    OrganizationMembership,
    UserProfile,
    Workflow,
    WorkflowStep,
)
from contracts.services.workflow_operations import (
    build_workflow_operations_row,
    split_exception_from_title,
)


User = get_user_model()


class WorkflowOperationsPageTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Ops Org', slug='ops-org')
        self.user = User.objects.create_user(
            username='ops-user',
            password='testpass123',
            first_name='Alex',
            last_name='Admin',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        UserProfile.objects.get_or_create(user=self.user, defaults={'role': UserProfile.Role.ADMIN})
        self.client.login(username='ops-user', password='testpass123')

        self.contract = Contract.objects.create(
            organization=self.organization,
            title='Northstar Consulting B.V. - Exception',
            contract_type=Contract.ContractType.MSA,
            status=Contract.Status.ACTIVE,
            counterparty='Northstar Consulting B.V.',
            business_unit='Enterprise Sales',
            jurisdiction='Netherlands',
            value=Decimal('125000.00'),
            currency=Contract.Currency.EUR,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=335),
            lifecycle_stage='INTERNAL_REVIEW',
            owner=self.user,
            created_by=self.user,
        )
        self.workflow = Workflow.objects.create(
            organization=self.organization,
            title='MSA Review',
            contract=self.contract,
            status=Workflow.Status.ACTIVE,
            created_by=self.user,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name='Legal Review',
            status=WorkflowStep.Status.IN_PROGRESS,
            order=1,
            assigned_to=self.user,
        )
        WorkflowStep.objects.create(
            workflow=self.workflow,
            name='Signature',
            status=WorkflowStep.Status.PENDING,
            order=2,
        )
        self.rule = ApprovalRule.objects.create(
            organization=self.organization,
            name='MSA value review',
            trigger_type=ApprovalRule.TriggerType.CONTRACT_TYPE,
            trigger_value=Contract.ContractType.MSA,
            approval_step='LEGAL',
            approver_role=UserProfile.Role.ADMIN,
            specific_approver=self.user,
            sla_hours=24,
            order=1,
        )
        ApprovalRequest.objects.create(
            organization=self.organization,
            contract=self.contract,
            rule=self.rule,
            approval_step='LEGAL',
            assigned_to=self.user,
            status=ApprovalRequest.Status.PENDING,
        )

    def test_split_exception_from_title(self):
        name, flagged = split_exception_from_title('Northstar Consulting B.V. - Exception')
        self.assertEqual(name, 'Northstar Consulting B.V.')
        self.assertTrue(flagged)

    def test_row_maps_stage_type_business_unit_and_progress(self):
        row = build_workflow_operations_row(self.workflow)
        self.assertEqual(row['display_name'], 'Northstar Consulting B.V.')
        self.assertTrue(row['has_exception'])
        self.assertEqual(row['stage'], 'Legal Review')
        self.assertEqual(row['agreement_type'], 'Master Service Agreement')
        self.assertEqual(row['business_unit'], 'Enterprise Sales')
        self.assertEqual(row['jurisdiction'], 'Netherlands')
        self.assertEqual(row['owner_label'], 'Alex Admin')
        self.assertEqual(row['progress_percentage'], 0)
        self.assertEqual(row['agreement_date'], self.contract.start_date)
        self.assertEqual(row['key_date'], self.contract.end_date)
        self.assertEqual(row['value'], self.contract.value)

    def test_operations_page_surface_and_tabs(self):
        response = self.client.get(reverse('contracts:workflow_dashboard'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('Workflow Operations', html)
        self.assertNotIn('Workflow Designer', html)
        self.assertNotIn('summary-grid', html)
        self.assertNotIn('Workflow pipeline', html)
        self.assertIn('Active workflows', html)
        self.assertIn('Approval requests', html)
        self.assertIn('Routing rules', html)
        self.assertIn('Templates', html)
        self.assertIn('Start workflow', html)
        self.assertIn('Northstar Consulting B.V.', html)
        self.assertNotIn('Northstar Consulting B.V. - Exception', html)
        self.assertIn('Exception', html)
        self.assertIn('Legal Review', html)
        self.assertIn('Master Service Agreement', html)
        self.assertIn('Enterprise Sales', html)
        self.assertIn('Netherlands', html)
        self.assertIn('Alex Admin', html)
        self.assertIn('0%', html)
        self.assertIn('workflow-ops-row', html)
        self.assertContains(response, reverse('contracts:approval_rule_list'))
        self.assertContains(response, reverse('contracts:approval_request_list'))
        self.assertContains(response, reverse('contracts:workflow_template_list'))

    def test_filters_status_and_type(self):
        response = self.client.get(reverse('contracts:workflow_dashboard'), {
            'status': 'ACTIVE',
            'contract_type': Contract.ContractType.MSA,
            'owner': str(self.user.pk),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Northstar Consulting B.V.')
        empty = self.client.get(reverse('contracts:workflow_dashboard'), {'status': 'COMPLETED'})
        self.assertContains(empty, 'No workflows match these filters')

    def test_related_surfaces_share_operations_tabs(self):
        for name in (
            'contracts:approval_request_list',
            'contracts:approval_rule_list',
            'contracts:workflow_template_list',
        ):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'Active workflows')
            self.assertContains(response, 'Approval requests')
            self.assertContains(response, 'Routing rules')
            self.assertContains(response, 'Templates')
