
import os

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from contracts.models import Contract
from contracts.tenancy import get_user_organization


class RedesignLayoutTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
        )
        os.environ['FEATURE_REDESIGN'] = 'true'
        self.client.login(username='testuser', password='testpass123')

    def test_base_shell_and_theme_controls(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'DocClad')
        self.assertContains(response, 'data-theme="dark"')
        # Theme toggle is wired via a delegated handler (CSP: no inline onclick).
        self.assertContains(response, 'data-action="toggle-theme"')
        self.assertContains(response, 'js/csp-handlers.js')
        self.assertContains(response, 'title="Search"')

    def test_sidebar_navigation_sections_and_links(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'REFERENCE')
        self.assertContains(response, 'Contract Workspace')
        self.assertContains(response, 'RISK &amp; COMPLIANCE')
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Counterparties')
        self.assertContains(response, 'Workflows')

    def test_topbar_actions(self):
        response = self.client.get(reverse('dashboard'))
        # Sub-block C: hardcoded Dutch chrome replaced with English
        # (LANGUAGE_CODE is 'en-us' — see contracts/templatetags no i18n gate).
        self.assertContains(response, 'title="Notifications"')
        self.assertContains(response, 'New Contract')
        self.assertContains(response, 'Sign out')
        self.assertContains(response, '/profile/')

    def test_dashboard_kpis_and_panels(self):
        # The priority action strip and the workflow queue render on the
        # populated dashboard; empty workspaces get the onboarding checklist
        # instead. Seed a contract in the organization the login flow
        # auto-provisioned for this user.
        organization = get_user_organization(self.user)
        Contract.objects.create(
            organization=organization,
            title='Layout Contract',
            content='Seed so the dashboard renders its normal state.',
            status='ACTIVE',
            created_by=self.user,
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Needs Legal Review')
        self.assertContains(response, 'Awaiting Approval')
        self.assertContains(response, 'Signature Pending')
        self.assertContains(response, 'Expiring Soon')
        self.assertContains(response, 'Waiting on Me')
        self.assertContains(response, 'In Progress')
        self.assertContains(response, 'Layout Contract')

    def test_dashboard_right_rail(self):
        # The right rail (deadlines/risk/activity) only renders on the
        # populated dashboard; an empty workspace gets the onboarding
        # checklist instead.
        organization = get_user_organization(self.user)
        Contract.objects.create(
            organization=organization,
            title='Right Rail Contract',
            content='Seed so the dashboard renders its normal state.',
            status='ACTIVE',
            created_by=self.user,
        )
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'New Contract')
        self.assertContains(response, 'Upcoming Deadlines')
        self.assertContains(response, 'Risk Watch')
        self.assertContains(response, 'Recent Activity')

    def tearDown(self):
        if 'FEATURE_REDESIGN' in os.environ:
            del os.environ['FEATURE_REDESIGN']
