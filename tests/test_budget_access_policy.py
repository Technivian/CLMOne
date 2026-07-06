"""Follow-up to the trust-account RBAC fix: confirms department budget access
is a deliberate policy decision, not an oversight. Budget/BudgetExpense hold
firm-operations data (allocations, spend, department/quarter) — not client
funds — so, unlike TrustAccount (see test_trust_account_permissions.py),
every active org member (MEMBER/ADMIN/OWNER) is intended to have full
list/detail/create/update access. Cross-tenant isolation is covered
separately by BudgetIsolationTest in test_cross_tenant_isolation.py; this
file only asserts the role policy."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from contracts.models import Budget, Organization, OrganizationMembership

User = get_user_model()


class BudgetAccessPolicyTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Budget Policy Org', slug='budget-policy-org')

        self.member_user = User.objects.create_user(username='budget_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member_user,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )

        self.admin_user = User.objects.create_user(username='budget_admin', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.admin_user,
            role=OrganizationMembership.Role.ADMIN, is_active=True,
        )

        self.owner_user = User.objects.create_user(username='budget_owner', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner_user,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )

        self.budget = Budget.objects.create(
            organization=self.org, year=2026, quarter=Budget.Quarter.Q1,
            department='Litigation', allocated_amount=Decimal('50000.00'),
        )

        self.member_client = TestClient()
        self.member_client.login(username='budget_member', password='testpass123!')
        self.admin_client = TestClient()
        self.admin_client.login(username='budget_admin', password='testpass123!')
        self.owner_client = TestClient()
        self.owner_client.login(username='budget_owner', password='testpass123!')

    # ---- MEMBER has full access (the policy this follow-up confirms) ----

    def test_member_can_list_budgets(self):
        response = self.member_client.get(reverse('contracts:budget_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Litigation')

    def test_member_can_view_budget_detail(self):
        response = self.member_client.get(reverse('contracts:budget_detail', args=[self.budget.pk]))
        self.assertEqual(response.status_code, 200)

    def test_member_can_load_create_budget_form(self):
        response = self.member_client.get(reverse('contracts:budget_create'))
        self.assertEqual(response.status_code, 200)

    def test_member_can_create_budget(self):
        response = self.member_client.post(reverse('contracts:budget_create'), {
            'year': 2026, 'quarter': Budget.Quarter.Q2,
            'department': 'Compliance', 'allocated_amount': '10000.00', 'description': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Budget.objects.filter(organization=self.org, department='Compliance').exists())

    def test_member_can_update_budget(self):
        response = self.member_client.post(
            reverse('contracts:budget_update', args=[self.budget.pk]),
            {
                'year': 2026, 'quarter': Budget.Quarter.Q1,
                'department': 'Litigation', 'allocated_amount': '75000.00', 'description': 'Revised',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.allocated_amount, Decimal('75000.00'))

    # ---- ADMIN and OWNER retain the same access (no regression) ----

    def test_admin_can_list_budgets(self):
        response = self.admin_client.get(reverse('contracts:budget_list'))
        self.assertEqual(response.status_code, 200)

    def test_owner_can_list_budgets(self):
        response = self.owner_client.get(reverse('contracts:budget_list'))
        self.assertEqual(response.status_code, 200)

    # ---- unauthenticated users are redirected to login, not admitted ----

    def test_anonymous_user_is_redirected_to_login(self):
        anonymous_client = TestClient()
        response = anonymous_client.get(reverse('contracts:budget_list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
