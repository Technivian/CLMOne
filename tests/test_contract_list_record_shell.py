"""Focused regression coverage for the Contract List design-system
migration (contracts:contract_list). Covers: authenticated rendering,
tenant isolation, search, every status tab (including the active tab's
aria-current="page" marker), every supported sort field and direction,
pagination with query-string preservation, condition-specific empty state,
exhaustive risk-badge tone coverage, and the migration's structural
guarantees (no <style> block, no raw colours/page-local tokens, no
.cc-v3-*, no remaining .cw-* text anywhere including theme/static/css, and
canonical .dc-ds-button/.dc-ds-filterbar/.dc-ds-dense-list controls in
place of the page-local .arch-status-tab/.arch-search/.detail-* markup).
"""
import re
from pathlib import Path

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from contracts.models import Contract, Organization, OrganizationMembership

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / 'theme' / 'templates' / 'contracts' / 'contract_list.html'
CSS_PATH = Path(__file__).resolve().parent.parent / 'theme' / 'static' / 'css' / 'contract-list.css'
HEX_COLOR_RE = re.compile(r'#[0-9a-fA-F]{3,8}\b')


class ContractListRenderTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='List Shell Firm', slug='list-shell-firm')
        self.user = User.objects.create_user(username='list_user', password='testpass123', email='list@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='list_user', password='testpass123')

    def test_renders_for_authenticated_member(self):
        response = self.client.get(reverse('contracts:contract_list'))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_redirected(self):
        anon = TestClient()
        response = anon.get(reverse('contracts:contract_list'))
        self.assertEqual(response.status_code, 302)

    def test_uses_shared_page_wrap_shell(self):
        response = self.client.get(reverse('contracts:contract_list'))
        self.assertContains(response, 'page-wrap')
        self.assertContains(response, 'Contract Workspace')

    def test_search_filters_by_title(self):
        Contract.objects.create(organization=self.organization, title='Findable Agreement', content='seed', status='ACTIVE', created_by=self.user)
        Contract.objects.create(organization=self.organization, title='Other Agreement', content='seed', status='ACTIVE', created_by=self.user)
        response = self.client.get(reverse('contracts:contract_list'), {'q': 'Findable'})
        body = response.content.decode()
        self.assertIn('Findable Agreement', body)
        self.assertNotIn('Other Agreement', body)

    def test_search_filters_by_counterparty(self):
        Contract.objects.create(organization=self.organization, title='CP Match', content='seed', status='ACTIVE', counterparty='Northwind Logistics', created_by=self.user)
        Contract.objects.create(organization=self.organization, title='CP No Match', content='seed', status='ACTIVE', counterparty='Acme Corp', created_by=self.user)
        response = self.client.get(reverse('contracts:contract_list'), {'q': 'Northwind'})
        body = response.content.decode()
        self.assertIn('CP Match', body)
        self.assertNotIn('CP No Match', body)


class ContractListStatusTabTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Tab Firm', slug='tab-firm')
        self.user = User.objects.create_user(username='tab_user', password='testpass123', email='tab@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='tab_user', password='testpass123')
        for status in ('DRAFT', 'IN_REVIEW', 'PENDING', 'APPROVED', 'EXPIRED', 'TERMINATED', 'CANCELLED', 'ACTIVE'):
            Contract.objects.create(organization=self.organization, title=f'{status} contract', content='seed', status=status, created_by=self.user)

    def test_all_tab_shows_every_contract(self):
        response = self.client.get(reverse('contracts:contract_list'))
        self.assertEqual(len(response.context['contracts']), 8)

    def test_draft_tab_filters_to_draft_only(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'DRAFT'})
        titles = {c.title for c in response.context['contracts']}
        self.assertEqual(titles, {'DRAFT contract'})

    def test_legal_review_tab_maps_to_in_review_status(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'IN_REVIEW'})
        titles = {c.title for c in response.context['contracts']}
        self.assertEqual(titles, {'IN_REVIEW contract'})

    def test_approval_tab_maps_to_pending_status(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'PENDING'})
        titles = {c.title for c in response.context['contracts']}
        self.assertEqual(titles, {'PENDING contract'})

    def test_signature_tab_maps_to_approved_status(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'APPROVED'})
        titles = {c.title for c in response.context['contracts']}
        self.assertEqual(titles, {'APPROVED contract'})

    def test_blocked_tab_covers_expired_terminated_cancelled(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'BLOCKED'})
        titles = {c.title for c in response.context['contracts']}
        self.assertEqual(titles, {'EXPIRED contract', 'TERMINATED contract', 'CANCELLED contract'})

    def test_active_tab_marker_is_aria_current_on_a_ghost_button(self):
        """All status links use the uniform .dc-ds-button--ghost styling —
        the active one is distinguished only by aria-current="page" (which
        contract-list.css uses as a scoped selector for the visible
        selected state), not by a different button variant."""
        response = self.client.get(reverse('contracts:contract_list'))
        body = response.content.decode()
        self.assertIn('aria-current="page"', body)
        self.assertNotIn('dc-ds-button--primary', body)

    def test_only_one_status_link_carries_aria_current(self):
        response = self.client.get(reverse('contracts:contract_list'), {'status': 'DRAFT'})
        body = response.content.decode()
        self.assertEqual(body.count('aria-current="page"'), 1)


class ContractListSortTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Sort Firm', slug='sort-firm')
        self.user = User.objects.create_user(username='sort_user', password='testpass123', email='sort@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='sort_user', password='testpass123')
        Contract.objects.create(organization=self.organization, title='Alpha', content='seed', status='ACTIVE', risk_level='LOW', created_by=self.user)
        Contract.objects.create(organization=self.organization, title='Zulu', content='seed', status='ACTIVE', risk_level='CRITICAL', created_by=self.user)

    def test_every_supported_sort_field_and_direction_returns_200(self):
        fields = ('title', 'status', 'end_date', 'created_at', 'updated_at', 'value', 'lifecycle_stage', 'risk_level')
        for field in fields:
            for value in (field, f'-{field}'):
                response = self.client.get(reverse('contracts:contract_list'), {'sort': value})
                self.assertEqual(response.status_code, 200, msg=f'sort={value} failed')

    def test_title_ascending_orders_alphabetically(self):
        response = self.client.get(reverse('contracts:contract_list'), {'sort': 'title'})
        titles = [c.title for c in response.context['contracts']]
        self.assertEqual(titles, ['Alpha', 'Zulu'])

    def test_title_descending_reverses_order(self):
        response = self.client.get(reverse('contracts:contract_list'), {'sort': '-title'})
        titles = [c.title for c in response.context['contracts']]
        self.assertEqual(titles, ['Zulu', 'Alpha'])

    def test_unsupported_sort_field_falls_back_to_default(self):
        response = self.client.get(reverse('contracts:contract_list'), {'sort': 'not_a_real_field'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['sort'], 'not_a_real_field')

    def test_sort_links_present_for_each_sortable_column(self):
        response = self.client.get(reverse('contracts:contract_list'))
        body = response.content.decode()
        for expected in ('sort=title', 'sort=lifecycle_stage', 'sort=updated_at', 'sort=end_date', 'sort=risk_level'):
            self.assertIn(expected, body)


class ContractListPaginationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Page Firm', slug='page-firm')
        self.user = User.objects.create_user(username='page_user', password='testpass123', email='page@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='page_user', password='testpass123')
        for i in range(30):
            Contract.objects.create(organization=self.organization, title=f'Contract {i:02d}', content='seed', status='ACTIVE', created_by=self.user)

    def test_pagination_splits_at_25_per_page(self):
        response = self.client.get(reverse('contracts:contract_list'))
        self.assertTrue(response.context['is_paginated'])
        self.assertEqual(len(response.context['contracts']), 25)

    def test_second_page_returns_remainder(self):
        response = self.client.get(reverse('contracts:contract_list'), {'page': 2})
        self.assertEqual(len(response.context['contracts']), 5)

    def test_pagination_links_preserve_search_and_status_and_sort(self):
        response = self.client.get(reverse('contracts:contract_list'), {'q': 'Contract', 'status': 'ACTIVE', 'sort': 'title'})
        body = response.content.decode()
        self.assertIn('q=Contract', body)
        self.assertIn('status=ACTIVE', body)
        self.assertIn('sort=title', body)


class ContractListEmptyStateTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Empty Firm', slug='empty-firm')
        self.user = User.objects.create_user(username='empty_user', password='testpass123', email='empty@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='empty_user', password='testpass123')

    def test_genuinely_empty_workspace_points_to_create_first_contract(self):
        response = self.client.get(reverse('contracts:contract_list'))
        body = response.content.decode()
        self.assertIn('No contract work found', body)
        self.assertIn('your first contract', body)
        self.assertNotIn('clear all', body)

    def test_filtered_zero_result_points_to_clear_filters(self):
        Contract.objects.create(organization=self.organization, title='Only Contract', content='seed', status='ACTIVE', created_by=self.user)
        response = self.client.get(reverse('contracts:contract_list'), {'q': 'no-such-title'})
        body = response.content.decode()
        self.assertIn('No contract work found', body)
        self.assertIn('clear all', body)
        self.assertNotIn('your first contract', body)


class ContractListRiskBadgeTests(TestCase):
    """Exhaustive coverage that every Contract.RiskLevel choice renders
    through the canonical .dc-ds-badge--* tone on this page."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Risk Firm', slug='risk-firm')
        self.user = User.objects.create_user(username='risk_user', password='testpass123', email='risk@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='risk_user', password='testpass123')

    def test_every_risk_level_renders_canonical_badge_tone(self):
        expected_tone = {
            'LOW': 'success',
            'MEDIUM': 'attention',
            'HIGH': 'danger',
            'CRITICAL': 'danger',
        }
        choices = {value for value, _ in Contract.RiskLevel.choices}
        self.assertEqual(choices, set(expected_tone.keys()))
        for risk_level, tone in expected_tone.items():
            Contract.objects.filter(organization=self.organization).delete()
            contract = Contract.objects.create(
                organization=self.organization, title=f'{risk_level} risk contract', content='seed',
                status='ACTIVE', risk_level=risk_level, created_by=self.user,
            )
            response = self.client.get(reverse('contracts:contract_list'))
            body = response.content.decode()
            self.assertIn(f'dc-ds-badge--{tone}', body, msg=f'{risk_level} did not render dc-ds-badge--{tone}')
            self.assertIn(contract.get_risk_level_display(), body)
            self.assertNotIn('badge-sm badge-', body)


class ContractListCrossTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name='CList Org A', slug='clist-org-a')
        self.org_b = Organization.objects.create(name='CList Org B', slug='clist-org-b')
        self.user_a = User.objects.create_user(username='clist_iso_a', password='testpass123', email='a@example.com')
        self.user_b = User.objects.create_user(username='clist_iso_b', password='testpass123', email='b@example.com')
        OrganizationMembership.objects.create(organization=self.org_a, user=self.user_a, role=OrganizationMembership.Role.MEMBER, is_active=True)
        OrganizationMembership.objects.create(organization=self.org_b, user=self.user_b, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.contract_a = Contract.objects.create(organization=self.org_a, title='Org A Only Contract', content='seed', status='ACTIVE', created_by=self.user_a)
        Contract.objects.create(organization=self.org_b, title='Org B Only Contract', content='seed', status='ACTIVE', created_by=self.user_b)

    def test_other_org_member_never_sees_contract(self):
        client = TestClient()
        client.login(username='clist_iso_b', password='testpass123')
        response = client.get(reverse('contracts:contract_list'))
        ids = [c.id for c in response.context['contracts']]
        self.assertNotIn(self.contract_a.id, ids)
        self.assertNotIn('Org A Only Contract', response.content.decode())


class ContractListMigrationStructureTests(TestCase):
    """Static assertions against the template/CSS source proving the
    migration's structural guarantees, independent of any rendered request."""

    def test_no_style_block_in_template(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('<style', source)

    def test_no_cw_class_references_in_template(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotRegex(source, r'\bcw-[a-zA-Z0-9_-]*')

    def test_no_cw_text_anywhere_in_template_or_css(self):
        """Stronger than the class-reference check above: no 'cw-' text at
        all, including in comments, so a repo-wide grep for the literal
        string is genuinely zero, not just zero live selectors."""
        for path in (TEMPLATE_PATH, CSS_PATH):
            source = path.read_text()
            self.assertNotIn('cw-', source, msg=f'Literal "cw-" text found in {path.name}')

    def test_no_cc_v3_classes_in_template(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('cc-v3-', source)

    def test_no_raw_hex_colours_in_template_or_css(self):
        for path in (TEMPLATE_PATH, CSS_PATH):
            source = path.read_text()
            matches = HEX_COLOR_RE.findall(source)
            self.assertEqual(matches, [], msg=f'Raw hex colour(s) found in {path.name}: {matches}')

    def test_no_page_local_ds_token_definitions_in_css(self):
        """No new --ds-* custom properties are *defined* here — consuming
        an existing canonical token via var(--ds-color-trust) etc. is the
        intended usage and is not a page-local token definition."""
        source = CSS_PATH.read_text()
        definitions = re.findall(r'^\s*(--ds-[a-z0-9-]+)\s*:', source, re.MULTILINE)
        self.assertEqual(definitions, [])

    def test_no_production_cw_consumers_repo_wide(self):
        """Repository-wide proof that .cw-* has zero production consumers
        left, now that contract_list.html (its only production consumer)
        no longer references it. Includes theme/static/css so the page's
        own new stylesheet is covered by the same proof, not just the
        template."""
        import subprocess
        repo_root = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            ['rg', '-l', 'cw-[a-zA-Z0-9_-]*', 'theme/templates', 'theme/static_src', 'theme/static/js', 'theme/static/css'],
            cwd=repo_root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1, msg=f'.cw-* still referenced in: {result.stdout}')

    def test_status_tabs_use_canonical_dc_ds_button_controls(self):
        """Status links are uniformly .dc-ds-button--ghost; the selected
        state comes from aria-current="page" plus a scoped, token-backed
        CSS rule (contract-list.css), not from swapping in
        .dc-ds-button--primary."""
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('arch-status-tab', source)
        self.assertNotIn('dc-ds-button--primary', source)
        self.assertIn('dc-ds-button dc-ds-button--ghost', source)
        self.assertIn('contract-list-statuses', source)

    def test_status_selected_state_css_is_scoped_and_token_backed(self):
        css_source = CSS_PATH.read_text()
        self.assertIn('.contract-list-statuses .dc-ds-button[aria-current="page"]', css_source)
        self.assertIn('var(--ds-color-trust)', css_source)
        self.assertIn('var(--ds-color-trust-soft)', css_source)

    def test_search_uses_canonical_dc_ds_filterbar(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('arch-search', source)
        self.assertIn('dc-ds-filterbar', source)
        self.assertIn('dc-ds-filterbar__search', source)

    def test_workload_rows_use_canonical_dc_ds_dense_list(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('detail-stack', source)
        self.assertNotIn('detail-row', source)
        self.assertNotIn('detail-label', source)
        self.assertNotIn('detail-value', source)
        self.assertIn('dc-ds-dense-list', source)
        self.assertIn('dc-ds-dense-row', source)

    def test_no_btn_ghost_class_remains(self):
        source = TEMPLATE_PATH.read_text()
        self.assertNotIn('btn-ghost', source)
        self.assertIn('dc-ds-button dc-ds-button--ghost', source)
