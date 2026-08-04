"""End-to-end safeguards for the bounded PayrollMinds pilot path.

These tests exercise existing canonical objects under the existing
PAR-SEC-002 default-off activation boundary.  They intentionally add no pilot
models or roles.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    Client,
    Contract,
    Deadline,
    Document,
    Matter,
    Organization,
    OrganizationMembership,
)


User = get_user_model()

PILOT_PRIVATE_REPOSITORY = {
    'DJANGO_ENV': 'test',
    'CONTROLLED_PILOT_ENABLED': False,
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': 'payrollminds-pilot',
}

PILOT_PRIVATE_SEARCH = {
    **PILOT_PRIVATE_REPOSITORY,
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST': 'payrollminds-pilot',
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
        self.private_client = Client.objects.create(
            organization=self.organization,
            name='Private PayrollMinds counterparty',
        )
        self.private_matter = Matter.objects.create(
            organization=self.organization,
            client=self.private_client,
            matter_number='PM-PRIVATE-001',
            title='Private PayrollMinds matter',
        )
        self.private_contract = Contract.objects.create(
            organization=self.organization,
            title='Private PayrollMinds agreement',
            client=self.private_client,
            matter=self.private_matter,
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
        client_list = self.client.get(reverse('contracts:client_list'))
        matter_list = self.client.get(reverse('contracts:matter_list'))
        direct_client = self.client.get(
            reverse('contracts:client_detail', args=[self.private_client.pk])
        )
        direct_matter = self.client.get(
            reverse('contracts:matter_detail', args=[self.private_matter.pk])
        )

        self.assertEqual(repository.status_code, 200)
        self.assertEqual(repository.json()['total_count'], 0)
        self.assertEqual(list(document_list.context['documents']), [])
        self.assertEqual(obligations.context['obligations'], [])
        self.assertNotContains(obligations, self.private_deadline.title)
        self.assertEqual(direct_contract.status_code, 404)
        self.assertEqual(direct_document.status_code, 404)
        self.assertEqual(client_list.status_code, 302)
        self.assertNotIn(self.private_client.name, client_list.content.decode())
        self.assertEqual(list(matter_list.context['matters']), [])
        self.assertEqual(direct_client.status_code, 302)
        self.assertNotIn(self.private_client.name, direct_client.content.decode())
        self.assertEqual(direct_matter.status_code, 404)

    @override_settings(**PILOT_PRIVATE_SEARCH)
    def test_search_does_not_leak_private_relationship_metadata_or_counts(self):
        response = self.client.get(reverse('contracts:global_search'), {'q': 'Private PayrollMinds'})

        self.assertEqual(response.status_code, 200)
        for result_key in ('contracts', 'clients', 'matters', 'documents'):
            self.assertEqual(list(response.context['results'][result_key]), [])
        self.assertNotContains(response, self.private_contract.title)
        self.assertNotContains(response, self.private_client.name)
        self.assertNotContains(response, self.private_matter.title)

    @override_settings(**PILOT_PRIVATE_REPOSITORY)
    def test_client_surface_filters_private_relationship_metadata_when_available(self):
        # The pilot's in-house navigation deliberately redirects the Client
        # surface. Exercise the canonical surface too: authorization is still
        # enforced if the surface remains reachable in another workspace mode.
        self.organization.workspace_mode = Organization.WorkspaceMode.LAW_FIRM_OPS
        self.organization.save(update_fields=['workspace_mode'])

        listing = self.client.get(reverse('contracts:client_list'))
        direct = self.client.get(
            reverse('contracts:client_detail', args=[self.private_client.pk])
        )
        client_edit = self.client.get(
            reverse('contracts:client_update', args=[self.private_client.pk])
        )
        matter_edit = self.client.get(
            reverse('contracts:matter_update', args=[self.private_matter.pk])
        )
        matter_create = self.client.get(reverse('contracts:matter_create'))
        forged_matter = self.client.post(
            reverse('contracts:matter_create'),
            {
                'title': 'Forged private-client link',
                'client': self.private_client.pk,
            },
        )

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(list(listing.context['clients']), [])
        self.assertEqual(listing.context['total_clients'], 0)
        self.assertEqual(direct.status_code, 404)
        self.assertEqual(client_edit.status_code, 404)
        self.assertEqual(matter_edit.status_code, 404)
        self.assertEqual(list(matter_create.context['form'].fields['client'].queryset), [])
        self.assertEqual(forged_matter.status_code, 200)
        self.assertIn('client', forged_matter.context['form'].errors)
        self.assertFalse(Matter.objects.filter(title='Forged private-client link').exists())

    @override_settings(**PILOT_PRIVATE_REPOSITORY)
    def test_membership_revocation_removes_previously_owned_record_access(self):
        member_contract = Contract.objects.create(
            organization=self.organization,
            title='Member-owned agreement',
            owner=self.member,
            created_by=self.member,
        )
        allowed = self.client.get(reverse('contracts:contracts_api'))
        self.assertEqual(allowed.json()['total_count'], 1)

        OrganizationMembership.objects.filter(
            organization=self.organization,
            user=self.member,
        ).update(is_active=False)
        revoked = self.client.get(reverse('contracts:contracts_api'))
        direct = self.client.get(reverse('contracts:contract_detail', args=[member_contract.pk]))

        self.assertEqual(revoked.json()['total_count'], 0)
        self.assertEqual(direct.status_code, 404)

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
