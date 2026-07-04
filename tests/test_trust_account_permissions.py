"""IOLTA trust accounting is normally restricted to attorneys/firm admins,
not paralegals or other support staff. TrustAccountListView/DetailView/
CreateView and AddTrustTransactionView previously only enforced
LoginRequiredMixin + tenant scoping — any active org member, regardless of
role, could view balances and create accounts/transactions. This proves the
new TrustAccountingPermissionMixin (contracts/views_domains/trust_conflict.py)
blocks MEMBER-role users and admits OWNER/ADMIN-role users."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from contracts.models import Client, Organization, OrganizationMembership, TrustAccount

User = get_user_model()


class TrustAccountPermissionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Trust Perm Org', slug='trust-perm-org')

        self.member_user = User.objects.create_user(username='member_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member_user,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )

        self.admin_user = User.objects.create_user(username='admin_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.admin_user,
            role=OrganizationMembership.Role.ADMIN, is_active=True,
        )

        self.owner_user = User.objects.create_user(username='owner_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner_user,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )

        self.client_record = Client.objects.create(organization=self.org, name='Acme Client')
        self.trust_account = TrustAccount.objects.create(
            client=self.client_record, account_name='Acme IOLTA', balance=Decimal('500.00'),
        )

        self.member_client = TestClient()
        self.member_client.login(username='member_user', password='testpass123!')
        self.admin_client = TestClient()
        self.admin_client.login(username='admin_user', password='testpass123!')
        self.owner_client = TestClient()
        self.owner_client.login(username='owner_user', password='testpass123!')

    # ---- MEMBER is blocked everywhere ----

    def test_member_cannot_list_trust_accounts(self):
        response = self.member_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_view_trust_account_detail(self):
        response = self.member_client.get(
            reverse('contracts:trust_account_detail', args=[self.trust_account.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_load_create_trust_account_form(self):
        response = self.member_client.get(reverse('contracts:trust_account_create'))
        self.assertEqual(response.status_code, 403)

    def test_member_cannot_create_trust_account_via_post(self):
        response = self.member_client.post(reverse('contracts:trust_account_create'), {
            'client': self.client_record.pk,
            'account_name': 'Forged IOLTA',
            'balance': '1000.00',
        })
        self.assertEqual(response.status_code, 403)
        self.assertFalse(TrustAccount.objects.filter(account_name='Forged IOLTA').exists())

    def test_member_cannot_add_trust_transaction(self):
        response = self.member_client.post(
            reverse('contracts:add_trust_transaction', args=[self.trust_account.pk]),
            {'transaction_type': 'DEPOSIT', 'amount': '100.00', 'description': 'Forged deposit'},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.trust_account.transactions.count(), 0)

    # ---- ADMIN and OWNER retain access ----

    def test_admin_can_list_trust_accounts(self):
        response = self.admin_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_list_trust_accounts(self):
        response = self.owner_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_trust_account_detail(self):
        response = self.admin_client.get(
            reverse('contracts:trust_account_detail', args=[self.trust_account.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_admin_can_load_create_trust_account_form(self):
        response = self.admin_client.get(reverse('contracts:trust_account_create'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_trust_account(self):
        response = self.admin_client.post(reverse('contracts:trust_account_create'), {
            'client': self.client_record.pk,
            'account_name': 'New Admin IOLTA',
            'balance': '250.00',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TrustAccount.objects.filter(account_name='New Admin IOLTA').exists())

    def test_admin_can_add_trust_transaction(self):
        response = self.admin_client.post(
            reverse('contracts:add_trust_transaction', args=[self.trust_account.pk]),
            {'transaction_type': 'DEPOSIT', 'amount': '100.00', 'description': 'Legitimate deposit'},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.trust_account.transactions.count(), 1)

    # ---- unauthenticated users are redirected to login, not 403'd ----

    def test_anonymous_user_is_redirected_to_login_not_forbidden(self):
        anonymous_client = TestClient()
        response = anonymous_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
