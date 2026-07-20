"""Settings configuration hub — compact landing page for personal, workspace,
and security destinations with permission-aware Admin-only cards."""
from django.contrib.auth import get_user_model
from django.test import Client as TestClient
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from contracts.models import Organization, OrganizationMembership
from contracts.nav_config import get_nav_for
from pathlib import Path

from django.conf import settings

User = get_user_model()


class SettingsHubViewTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Settings Hub Org', slug='settings-hub-org')
        self.member = User.objects.create_user(username='settings_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        self.admin = User.objects.create_user(username='settings_admin', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )
        self.member_client = TestClient()
        self.member_client.login(username='settings_member', password='testpass123!')
        self.admin_client = TestClient()
        self.admin_client.login(username='settings_admin', password='testpass123!')

    def test_hub_renders_compact_groups_and_subtitle(self):
        response = self.admin_client.get(reverse('settings_hub'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        groups = {group['title'] for group in response.context['settings_groups']}
        labels = {
            card['label']
            for group in response.context['settings_groups']
            for card in group['cards']
        }
        self.assertIn('settings-hub-page', body)
        self.assertIn('Manage personal preferences, workspace configuration, security and governance.', body)
        self.assertEqual(groups, {'Personal', 'Workspace', 'Security and governance'})
        self.assertIn('Team and roles', labels)
        self.assertNotIn('Configuration areas', body)
        self.assertNotIn('Organization Team', body)
        self.assertNotIn('Admin workspace', body)
        self.assertNotIn('Operations Dashboard', body)
        # Operations lives in Admin nav, not as a settings hub card.
        self.assertNotIn('>Operations</', ''.join(
            f'>{card["label"]}</' for group in response.context['settings_groups'] for card in group['cards']
        ))

    def test_hub_uses_navigation_cards_with_icons_and_arrows(self):
        response = self.admin_client.get(reverse('settings_hub'))
        body = response.content.decode()
        self.assertIn('dc-ds-card-grid dc-ds-card-grid--3', body)
        self.assertIn('dc-ds-setup-action', body)
        self.assertIn('dc-ds-setup-action__icon', body)
        self.assertIn('dc-ds-setup-action__arrow', body)
        self.assertIn('Team and roles', body)
        self.assertIn('Approval policies', body)
        self.assertIn('Active sessions', body)
        self.assertIn('Audit activity', body)

    def test_member_sees_personal_and_workspace_without_admin_cards(self):
        response = self.member_client.get(reverse('settings_hub'))
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn('Profile', body)
        self.assertIn('Notifications', body)
        self.assertIn('Templates', body)
        self.assertIn('Playbooks', body)
        self.assertNotIn('Team and roles', body)
        self.assertNotIn('Authentication', body)
        self.assertNotIn('Active sessions', body)
        self.assertNotIn('Admin only', body)
        self.assertFalse(response.context['can_manage_settings'])

    def test_admin_sees_admin_only_badges_on_gated_cards(self):
        response = self.admin_client.get(reverse('settings_hub'))
        body = response.content.decode()
        self.assertTrue(response.context['can_manage_settings'])
        self.assertIn('Admin only', body)
        self.assertContains(response, reverse('contracts:organization_team'))
        self.assertContains(response, reverse('organization_security_settings'))
        self.assertContains(response, reverse('organization_session_audit'))
        self.assertContains(response, reverse('organization_identity_settings'))

    def test_hub_sections_are_labelled_for_accessibility(self):
        response = self.admin_client.get(reverse('settings_hub'))
        body = response.content.decode()
        self.assertIn('aria-labelledby="settings-group-personal"', body)
        self.assertIn('id="settings-group-personal"', body)
        self.assertIn('aria-labelledby="settings-group-workspace"', body)
        self.assertIn('aria-labelledby="settings-group-security"', body)

    def test_anonymous_user_is_redirected(self):
        anon = TestClient()
        response = anon.get(reverse('settings_hub'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class SettingsHubNavigationTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Settings Nav Org', slug='settings-nav-org')
        self.member = User.objects.create_user(username='settings_nav_member', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        self.admin = User.objects.create_user(username='settings_nav_admin', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.admin,
            role=OrganizationMembership.Role.ADMIN,
            is_active=True,
        )

    def test_sidebar_no_longer_exposes_admin_group(self):
        for user in (self.admin, self.member):
            nav = get_nav_for(self.org, user)
            labels = [entry.get('label') for entry in nav]
            self.assertNotIn('Admin', labels)
            self.assertNotIn('Settings', labels)
            self.assertNotIn('Operations', labels)

    def test_admin_profile_menu_exposes_settings_and_operations(self):
        client = TestClient()
        client.login(username='settings_nav_admin', password='testpass123!')
        response = client.get(reverse('dashboard'))
        body = response.content.decode()
        self.assertIn('href="' + reverse('profile') + '"', body)
        self.assertIn('profile-menu-header__name', body)
        self.assertNotIn('role="menuitem">Account</a>', body)
        self.assertIn('role="menuitem">Settings</a>', body)
        self.assertIn('role="menuitem">Operations</a>', body)
        self.assertIn('role="menuitem">Notifications</a>', body)
        self.assertIn(reverse('settings_hub'), body)
        self.assertIn(reverse('operations_dashboard'), body)
        self.assertNotIn('class="nav-group"', body)

    def test_member_profile_menu_hides_operations(self):
        client = TestClient()
        client.login(username='settings_nav_member', password='testpass123!')
        response = client.get(reverse('dashboard'))
        body = response.content.decode()
        self.assertIn('href="' + reverse('profile') + '"', body)
        self.assertIn('profile-menu-header__name', body)
        self.assertNotIn('role="menuitem">Account</a>', body)
        self.assertIn('role="menuitem">Settings</a>', body)
        self.assertIn('role="menuitem">Notifications</a>', body)
        self.assertNotIn('role="menuitem">Operations</a>', body)

class SettingsHubResponsiveContractTests(SimpleTestCase):
    def test_card_grid_collapses_on_narrow_viewports(self):
        components = (
            Path(settings.BASE_DIR) / 'theme' / 'static_src' / 'src' / 'design-system' / 'components.css'
        ).read_text()
        self.assertIn('.dc-ds-card-grid--3', components)
        self.assertIn('@media (max-width: 1024px)', components)
        self.assertIn('@media (max-width: 640px)', components)
        # Compact cards remain single-column on small screens.
        self.assertIn(
            '.dc-ds-card-grid--3,\n  .dc-ds-summary { grid-template-columns: 1fr; }',
            components,
        )

    def test_setup_action_supports_admin_badge_markup(self):
        partial = (
            Path(settings.BASE_DIR) / 'theme' / 'templates' / 'design_system' / 'setup_action.html'
        ).read_text()
        self.assertIn('badge_label', partial)
        self.assertIn('dc-ds-badge--phase', partial)
        self.assertIn('dc-ds-setup-action__arrow', partial)
