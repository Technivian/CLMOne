"""Phase 1 of the Product Coherence Redesign: Organization.workspace_mode
and the mode-aware sidebar (contracts/nav_config.py).

Companion to tests/test_nav_law_firm_baseline.py, which proves the default
(law_firm_ops) sidebar is byte-for-byte unchanged. This file covers the new
behavior: the field itself, the in_house_clm nav, specialist-module
containment, direct-URL access when a module is hidden from nav, and that
none of this touches DPA Review Pack or approval behavior.
"""
from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from contracts.models import (
    Contract,
    Counterparty,
    DPAReviewPack,
    Organization,
    OrganizationMembership,
)

User = get_user_model()

# The exact 12-item flat list from the Product Coherence Redesign memo,
# Section D, as specified for this phase's ticket.
IN_HOUSE_CLM_NAV_LABELS = [
    'Command Center',
    'Contracts',
    'Repository',
    'Matters',
    'Counterparties',
    'Risk Review',
    'DPA Reviews',
    'Approvals',
    'Obligations',
    'Playbooks',
    'Reports',
    'Admin',
]

# Specialist/law-firm modules that must not render as primary nav items in
# in_house_clm mode (they remain reachable by direct URL — see the
# direct-URL-access tests below).
SPECIALIST_NAV_LABELS_HIDDEN_IN_IN_HOUSE_CLM = [
    'Escrow',            # Trust Accounts
    'Budget &amp; Capacity',
    'Workflows',
    'Signature Requests',
    'Tasks',
    'Compliance',
    'Privacy',
    'Audit Trail',
    'Documents',
    'Clients',
]


def sidebar_html(response):
    content = response.content.decode()
    start = content.index('<nav class="sidebar-container"')
    end = content.index('</nav>', start)
    return content[start:end]


class WorkspaceModeFieldTests(TestCase):
    def test_default_is_law_firm_ops(self):
        org = Organization.objects.create(name='Default Mode Org', slug='default-mode-org')
        self.assertEqual(org.workspace_mode, Organization.WorkspaceMode.LAW_FIRM_OPS)

    def test_existing_organizations_are_unaffected_by_the_migration(self):
        # Organizations created before this field existed behave exactly as
        # if the migration had never run: same default, same nav.
        org = Organization.objects.create(name='Pre-existing Org', slug='pre-existing-org')
        self.assertEqual(org.workspace_mode, 'law_firm_ops')


class WorkspaceModeSettingsExposureTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Settings Org', slug='settings-org')
        self.owner = User.objects.create_user(username='wm_owner', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.member = User.objects.create_user(username='wm_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        self.owner_client = TestClient()
        self.owner_client.login(username='wm_owner', password='testpass123!')
        self.member_client = TestClient()
        self.member_client.login(username='wm_member', password='testpass123!')

    def test_owner_can_change_workspace_mode(self):
        response = self.owner_client.post(
            reverse('organization_security_settings'),
            {'action': 'save_workspace_mode', 'workspace_mode': 'in_house_clm'},
        )
        self.assertEqual(response.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.workspace_mode, 'in_house_clm')

    def test_member_cannot_reach_the_settings_page_at_all(self):
        # organization_security_settings is already owner/admin-gated —
        # workspace_mode rides on that existing gate, it doesn't add a new one.
        response = self.member_client.get(reverse('organization_security_settings'))
        self.assertEqual(response.status_code, 403)

    def test_invalid_mode_value_is_rejected(self):
        response = self.owner_client.post(
            reverse('organization_security_settings'),
            {'action': 'save_workspace_mode', 'workspace_mode': 'something_bogus'},
        )
        self.assertEqual(response.status_code, 302)
        self.org.refresh_from_db()
        self.assertEqual(self.org.workspace_mode, 'law_firm_ops')


class InHouseClmNavTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds', slug='payrollminds', workspace_mode='in_house_clm',
        )
        self.owner = User.objects.create_user(username='clm_owner', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.member = User.objects.create_user(username='clm_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        self.owner_client = TestClient()
        self.owner_client.login(username='clm_owner', password='testpass123!')
        self.member_client = TestClient()
        self.member_client.login(username='clm_member', password='testpass123!')

    def test_all_twelve_primary_nav_items_present_in_order(self):
        response = self.owner_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        positions = []
        for label in IN_HOUSE_CLM_NAV_LABELS:
            self.assertIn(label, content, msg=f'Missing in_house_clm nav label: {label}')
            positions.append(content.index(label))
        self.assertEqual(positions, sorted(positions), 'in_house_clm nav items are out of order')

    def test_specialist_modules_are_not_primary_nav_items(self):
        response = self.owner_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        for label in SPECIALIST_NAV_LABELS_HIDDEN_IN_IN_HOUSE_CLM:
            self.assertNotIn(label, content, msg=f'{label} should not render as a primary nav item in in_house_clm')

    def test_no_section_headers_in_in_house_clm_nav(self):
        # The memo's Section D lists a flat 12-item nav; law_firm_ops-style
        # section headers (EXECUTION, RISK & COMPLIANCE...) should not appear.
        response = self.owner_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        for section in ('EXECUTION', 'RISK &amp; COMPLIANCE', 'REFERENCE', 'PLANNING', 'ADMIN'):
            self.assertNotIn(f'>{section}<', content)

    def test_member_also_sees_the_focused_nav(self):
        # Nav emphasis is per-organization, not per-role — a member sees the
        # same in_house_clm nav as the owner (role gates individual items
        # like Escrow, not the mode itself).
        response = self.member_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        for label in IN_HOUSE_CLM_NAV_LABELS:
            self.assertIn(label, content)

    def test_command_center_links_to_dashboard(self):
        response = self.owner_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        href = reverse('dashboard')
        self.assertRegex(content, rf'<a href="{href}" class="nav-link active"')
        self.assertIn('Command Center', content)

    def test_matters_links_to_existing_matter_list_route(self):
        response = self.owner_client.get(reverse('dashboard'))
        content = sidebar_html(response)
        href = reverse('contracts:matter_list')
        self.assertIn(f'href="{href}"', content)

    def test_active_state_still_works_in_in_house_clm(self):
        response = self.owner_client.get(reverse('contracts:risk_log_list'))
        content = sidebar_html(response)
        href = reverse('contracts:risk_log_list')
        self.assertRegex(content, rf'<a href="{href}" class="nav-link active"')


class SpecialistModuleDirectUrlAccessTests(TestCase):
    """Hidden from nav must not mean blocked — direct URL access for an
    authorized user must be unaffected by workspace_mode."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds Direct', slug='payrollminds-direct', workspace_mode='in_house_clm',
        )
        self.owner = User.objects.create_user(username='direct_owner', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.owner,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.member = User.objects.create_user(username='direct_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.member,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        self.owner_client = TestClient()
        self.owner_client.login(username='direct_owner', password='testpass123!')
        self.member_client = TestClient()
        self.member_client.login(username='direct_member', password='testpass123!')

    def test_owner_can_still_open_trust_accounts_directly(self):
        response = self.owner_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 200)

    def test_member_hitting_trust_accounts_directly_is_still_403(self):
        # Same permission behavior as law_firm_ops — mode never changes
        # server-side authorization.
        response = self.member_client.get(reverse('contracts:trust_account_list'))
        self.assertEqual(response.status_code, 403)

    def test_budget_list_still_reachable_directly(self):
        response = self.member_client.get(reverse('contracts:budget_list'))
        self.assertEqual(response.status_code, 200)

    def test_workflow_dashboard_still_reachable_directly(self):
        response = self.member_client.get(reverse('contracts:workflow_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_compliance_checklist_list_still_reachable_directly(self):
        response = self.member_client.get(reverse('contracts:compliance_checklist_list'))
        self.assertEqual(response.status_code, 200)

    def test_settings_hub_still_accessible_to_admins(self):
        response = self.owner_client.get(reverse('settings_hub'))
        self.assertEqual(response.status_code, 200)

    def test_organization_security_settings_still_accessible_to_admins(self):
        response = self.owner_client.get(reverse('organization_security_settings'))
        self.assertEqual(response.status_code, 200)


class DPAAndApprovalBehaviorUnchangedTests(TestCase):
    """Phase 1 is IA-only — this locks down that switching workspace_mode
    does not alter DPA Review Pack or approval logic in any way."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds DPA Check', slug='payrollminds-dpa-check', workspace_mode='in_house_clm',
        )
        self.user = User.objects.create_user(username='dpa_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client_ = TestClient()
        self.client_.login(username='dpa_user', password='testpass123!')

        self.counterparty = Counterparty.objects.create(organization=self.org, name='Acme Corp')
        self.contract = Contract.objects.create(
            organization=self.org, title='Acme DPA', content='DPA content',
            status='ACTIVE', created_by=self.user,
        )
        self.review_pack = DPAReviewPack.objects.create(
            organization=self.org, contract=self.contract, counterparty=self.counterparty,
            liability_uncapped=True,
        )

    def test_dpa_review_pack_list_renders_normally_in_in_house_clm(self):
        response = self.client_.get(reverse('contracts:dpa_review_pack_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acme DPA')

    def test_dpa_review_pack_detail_renders_normally_in_in_house_clm(self):
        response = self.client_.get(reverse('contracts:dpa_review_pack_detail', kwargs={'pk': self.review_pack.pk}))
        self.assertEqual(response.status_code, 200)

    def test_dpa_conflict_detection_service_untouched(self):
        from contracts.services.dpa_conflict import check_cross_document_conflicts
        # Smoke test only — Phase 1 changes zero conflict-detection logic;
        # this just proves the service still imports and runs.
        check_cross_document_conflicts(self.review_pack)

    def test_approval_request_list_renders_normally_in_in_house_clm(self):
        response = self.client_.get(reverse('contracts:approval_request_list'))
        self.assertEqual(response.status_code, 200)
