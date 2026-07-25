"""Sub-block C: default-language consistency (C2) and named copy defects (C3)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from contracts.models import ClauseCategory, ClauseTemplate, Contract, Organization, OrganizationMembership

User = get_user_model()

# Chrome strings the audit found hardcoded in Dutch (base.html topbar).
# LANGUAGE_CODE is 'en-us' (config/settings_base.py) — these should never render.
_BANNED_NON_ENGLISH_CHROME = [
    'Organisatieteam',
    'Instellingen',
    'Thema wisselen',
    'Meldingen',
    'Uitloggen',
]


class DefaultLanguageConsistencyTests(TestCase):
    """C2: the authenticated app shell must render entirely in English."""

    def setUp(self):
        self.user = User.objects.create_user(username='langcheck', password='testpass123!')
        self.org = Organization.objects.create(name='Lang Check Org', slug='lang-check-org')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client.login(username='langcheck', password='testpass123!')

    def test_dashboard_navbar_has_no_hardcoded_dutch_strings(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for banned in _BANNED_NON_ENGLISH_CHROME:
            self.assertNotIn(banned, content, f'Found hardcoded non-English chrome string: {banned!r}')

    def test_dashboard_navbar_uses_english_equivalents(self):
        response = self.client.get(reverse('dashboard'))
        content = response.content.decode()
        self.assertIn('title="Team"', content)
        self.assertIn('role="menuitem">Settings</a>', content)
        self.assertNotIn('title="Settings"', content)
        self.assertIn('title="Notifications"', content)
        self.assertIn('>Sign out<', content)


class NamedCopyDefectTests(TestCase):
    """C3: specific copy defects named in the audit."""

    def setUp(self):
        self.user = User.objects.create_user(username='copycheck', password='testpass123!')
        self.org = Organization.objects.create(name='Copy Check Org', slug='copy-check-org')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client.login(username='copycheck', password='testpass123!')

    def test_registration_hero_does_not_concatenate_words(self):
        response = self.client.get(reverse('register'))
        content = response.content.decode()
        self.assertNotIn('yourcontract', content)

    def test_reports_dashboard_does_not_duplicate_active_contracts_label(self):
        response = self.client.get(reverse('contracts:reports_dashboard'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('Active ContractsActive Contracts', content)

    def test_search_results_description_is_not_duplicated(self):
        response = self.client.get(reverse('contracts:global_search'), {'q': 'test'})
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('Search across cases, case matters', content)

    def test_empty_clause_library_has_helpful_cta_not_bare_message(self):
        response = self.client.get(reverse('contracts:clause_template_list'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('No clause library found', content)
        self.assertIn('Add first clause', content)

    def test_clause_library_exposes_its_search_filters_count_and_primary_action(self):
        ClauseTemplate.objects.create(
            organization=self.org,
            title='Governing law',
            content='This agreement is governed by Dutch law.',
        )

        response = self.client.get(reverse('contracts:clause_template_list'))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for value in ('Search clauses', 'All categories', 'All scopes', '1 clause', '>Add new<'):
            with self.subTest(value=value):
                self.assertIn(value, content)

    def test_clause_library_retains_active_search_category_and_scope_filters(self):
        category = ClauseCategory.objects.create(organization=self.org, name='Governing law')
        ClauseTemplate.objects.create(
            organization=self.org,
            category=category,
            title='Dutch governing law',
            content='This agreement is governed by Dutch law.',
            jurisdiction_scope=ClauseTemplate.JurisdictionScope.EU,
        )
        ClauseTemplate.objects.create(
            organization=self.org,
            title='Confidentiality',
            content='Keep confidential information protected.',
            jurisdiction_scope=ClauseTemplate.JurisdictionScope.GLOBAL,
        )

        response = self.client.get(
            reverse('contracts:clause_template_list'),
            {'q': 'Dutch', 'category': category.pk, 'scope': ClauseTemplate.JurisdictionScope.EU},
        )

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('1 clause', content)
        self.assertIn('value="EU" selected', content)
        self.assertIn(f'value="{category.pk}" selected', content)
        self.assertIn('Dutch governing law', content)
        self.assertNotIn('>Confidentiality<', content)

    def test_clause_template_edit_explains_versioned_save_and_groups_fields(self):
        clause = ClauseTemplate.objects.create(
            organization=self.org,
            title='Governing law',
            content='This agreement is governed by Dutch law.',
        )

        response = self.client.get(reverse('contracts:clause_template_update', kwargs={'pk': clause.pk}))

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        for value in (
            'Clause details', 'Clause text', 'Applicability', 'Negotiation guidance',
            'Versioned change', 'Saving creates a new draft version.', 'Save new version',
        ):
            with self.subTest(value=value):
                self.assertIn(value, content)

    def test_contract_detail_target_stage_is_not_a_raw_enum_key(self):
        contract = Contract.objects.create(
            organization=self.org,
            title='Underscore Regression Contract',
            content='Test content',
            status=Contract.Status.IN_PROGRESS,
            lifecycle_stage='INTERNAL_REVIEW',
            created_by=self.user,
        )
        response = self.client.get(reverse('contracts:contract_detail', args=[contract.pk]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertNotIn('Internal_Review', content)
        self.assertIn('Internal review', content)
