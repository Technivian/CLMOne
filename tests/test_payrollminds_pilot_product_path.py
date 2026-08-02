"""End-to-end safeguards for the bounded PayrollMinds pilot path.

These tests exercise existing canonical objects under the existing
PAR-SEC-002 default-off activation boundary.  They intentionally add no pilot
models or roles.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import Contract, Deadline, Document, Organization, OrganizationMembership


User = get_user_model()

PILOT_PRIVATE_REPOSITORY = {
    'DJANGO_ENV': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': 'payrollminds-pilot',
}


class PayrollMindsPrivatePathTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='PayrollMinds Pilot', slug='payrollminds-pilot'
        )
        self.owner = User.objects.create_user(username='pilot-owner', password='test-pass-123')
        self.member = User.objects.create_user(username='pilot-member', password='test-pass-123')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        self.private_contract = Contract.objects.create(
            organization=self.organization,
            title='Private PayrollMinds agreement',
            owner=self.owner,
            created_by=self.owner,
        )
        self.private_document = Document.objects.create(
            organization=self.organization,
            contract=self.private_contract,
            title='Private PayrollMinds source',
            uploaded_by=self.owner,
        )
        self.private_deadline = Deadline.objects.create(
            title='Private renewal notice',
            contract=self.private_contract,
            due_date='2030-01-01',
            created_by=self.owner,
        )
        self.client.force_login(self.member)

    @override_settings(**PILOT_PRIVATE_REPOSITORY)
    def test_member_cannot_discover_private_record_document_or_reminder(self):
        repository = self.client.get(reverse('contracts:contracts_api'))
        document_list = self.client.get(reverse('contracts:document_list'))
        obligations = self.client.get(reverse('contracts:obligations_workspace'))
        direct_contract = self.client.get(
            reverse('contracts:contract_detail', args=[self.private_contract.pk])
        )
        direct_document = self.client.get(
            reverse('contracts:document_detail', args=[self.private_document.pk])
        )

        self.assertEqual(repository.status_code, 200)
        self.assertEqual(repository.json()['total_count'], 0)
        self.assertEqual(list(document_list.context['documents']), [])
        self.assertEqual(obligations.context['obligations'], [])
        self.assertNotContains(obligations, self.private_deadline.title)
        self.assertEqual(direct_contract.status_code, 404)
        self.assertEqual(direct_document.status_code, 404)

    @override_settings(**PILOT_PRIVATE_REPOSITORY)
    def test_owner_can_find_private_record_and_reminder(self):
        self.client.force_login(self.owner)
        repository = self.client.get(reverse('contracts:contracts_api'))
        obligations = self.client.get(reverse('contracts:obligations_workspace'))

        self.assertEqual(repository.json()['total_count'], 1)
        self.assertEqual(
            [row['id'] for row in repository.json()['contracts']],
            [str(self.private_contract.pk)],
        )
        self.assertEqual(
            [deadline.pk for deadline in obligations.context['obligations']],
            [self.private_deadline.pk],
        )
