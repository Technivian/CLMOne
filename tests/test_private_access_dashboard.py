"""Command Center projections must inherit canonical contract visibility."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from contracts.models import CommandCenterWorkItem, Contract, Organization, OrganizationMembership


User = get_user_model()


class PrivateAccessDashboardTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Private dashboard', slug='private-dashboard')
        self.other_organization = Organization.objects.create(name='Other dashboard', slug='other-dashboard')
        self.owner = User.objects.create_user(username='dashboard-owner', password='testpass123')
        self.member = User.objects.create_user(username='dashboard-member', password='testpass123')
        self.outsider = User.objects.create_user(username='dashboard-outsider', password='testpass123')
        for organization, user, role in (
            (self.organization, self.owner, OrganizationMembership.Role.OWNER),
            (self.organization, self.member, OrganizationMembership.Role.MEMBER),
            (self.other_organization, self.outsider, OrganizationMembership.Role.OWNER),
        ):
            OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=role,
                is_active=True,
            )
        self.visible_contract = Contract.objects.create(
            organization=self.organization,
            title='Owner-visible dashboard contract',
            created_by=self.owner,
        )
        self.hidden_contract = Contract.objects.create(
            organization=self.organization,
            title='Member-private dashboard contract',
            created_by=self.member,
        )
        self.other_contract = Contract.objects.create(
            organization=self.other_organization,
            title='Cross-workspace dashboard contract',
            created_by=self.outsider,
        )
        for contract, user in (
            (self.visible_contract, self.owner),
            (self.hidden_contract, self.member),
            (self.other_contract, self.outsider),
        ):
            CommandCenterWorkItem.objects.create(
                organization=contract.organization,
                source_type=CommandCenterWorkItem.SourceType.CONTRACT,
                source_model='Contract',
                source_object_id=contract.pk,
                title=f'Projection: {contract.title}',
                contract=contract,
                owner=user,
            )

    def _dashboard(self, user):
        client = Client()
        client.force_login(user)
        return client.get(reverse('dashboard'))

    def test_dashboard_filters_counts_rows_and_detail_by_canonical_visibility(self):
        response = self._dashboard(self.owner)
        rows = response.context['priority_queue_rows']
        titles = {row['title'] for row in rows}

        self.assertEqual(response.context['case_stats']['total'], 1)
        self.assertEqual(titles, {f'Projection: {self.visible_contract.title}'})
        self.assertContains(response, self.visible_contract.title)
        self.assertNotContains(response, self.hidden_contract.title)
        self.assertEqual(
            self._dashboard(self.member).context['case_stats']['total'],
            1,
        )
        self.assertEqual(
            self._dashboard(self.outsider).context['case_stats']['total'],
            1,
        )

        owner_client = Client()
        owner_client.force_login(self.owner)
        self.assertEqual(
            owner_client.get(reverse('contracts:contract_detail', args=[self.visible_contract.pk])).status_code,
            200,
        )
        self.assertEqual(
            owner_client.get(reverse('contracts:contract_detail', args=[self.hidden_contract.pk])).status_code,
            404,
        )
