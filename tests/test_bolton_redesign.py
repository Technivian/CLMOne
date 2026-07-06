
import os
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from contracts.models import Contract, Organization, OrganizationMembership


class BoltonRedesignTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.organization = Organization.objects.create(name='Bolton Firm', slug='bolton-firm')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Set feature flag
        os.environ['FEATURE_REDESIGN'] = 'true'

    def _seed_contract(self):
        """The KPI strip and portfolio panels only render once the workspace
        has data; empty workspaces get the onboarding checklist instead."""
        return Contract.objects.create(
            organization=self.organization,
            title='Seeded Contract',
            content='Seeded content',
            status='ACTIVE',
            created_by=self.user,
        )

    def test_dashboard_kpi_cards(self):
        self._seed_contract()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Active contracts')
        self.assertContains(response, 'Pending approval')
        self.assertContains(response, 'Expiring soon')
        self.assertContains(response, 'High risk')
        self.assertContains(response, 'kpi-card')

    def test_dashboard_empty_state_hides_kpis(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Start building your legal workspace')
        # The CSS definitions always mention the kpi classes; assert on the
        # rendered markup instead: no KPI tile labels in the onboarding state.
        self.assertNotContains(response, 'Active contracts')
        self.assertNotContains(response, 'Pending signatures')

    def test_dashboard_container_constraint(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'max-width: 1400px')

    def test_dashboard_top_bar(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'title="Search"')
        self.assertContains(response, 'title="Toggle theme"')
        self.assertContains(response, 'title="Notifications"')
        self.assertContains(response, 'New Contract')
        self.assertContains(response, 'Sign out')

    def test_dashboard_panels(self):
        # The dashboard is a workflow queue first: saved-view tabs + a single
        # queue table, with the KPI strip and activity feed as secondary
        # panels. The old placeholder-only "Recent Contracts" / "Case
        # Portfolio" panels were removed as part of that conversion.
        self._seed_contract()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'In Progress')
        self.assertContains(response, 'Waiting on Me')
        self.assertContains(response, 'Needs Review')
        self.assertContains(response, 'Renewals')
        self.assertContains(response, 'Completed')
        self.assertContains(response, 'Task Signals')
        self.assertContains(response, 'Recent activity')

    def test_contracts_table_structure(self):
        Contract.objects.create(
            organization=self.organization,
            title='Test Contract',
            content='Test content',
            status='DRAFT',
            created_by=self.user
        )

        response = self.client.get(reverse('contracts:contract_list'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Title')
        self.assertContains(response, 'Contract type')
        self.assertContains(response, 'Stage')
        self.assertContains(response, 'Complexity')
        self.assertContains(response, 'Counterparty')
        self.assertContains(response, 'Test Contract')

    def test_contracts_list_filters_and_actions(self):
        response = self.client.get(reverse('contracts:contract_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Search contracts...')
        self.assertContains(response, 'In progress')
        self.assertContains(response, 'Search')
        self.assertContains(response, 'New Contract')

    def test_accessibility_features(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'title="Search"')
        self.assertContains(response, 'title="Toggle theme"')
        self.assertContains(response, 'title="Search"')
        self.assertContains(response, 'type="submit"')

    def test_typography_and_spacing(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Inter is the sole product typeface per the approved brand kit and
        # the "Ledger" design system (DOCCLAD_DESIGN_SYSTEM.md) — Manrope/Sora
        # were retired in the 2026-07-05 rebrand.
        self.assertContains(response, "font-family: 'Inter'")
        self.assertNotContains(response, "font-family: 'Manrope'")
        self.assertContains(response, 'dash-grid')
        self.assertContains(response, 'gap: 20px')

    def tearDown(self):
        """Clean up environment variables"""
        if 'FEATURE_REDESIGN' in os.environ:
            del os.environ['FEATURE_REDESIGN']
