"""Account-page information architecture and self-service permission tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from contracts.models import Organization, OrganizationMembership, UserProfile


class ProfileAccountExperienceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='account-member',
            email='member@example.com',
            first_name='Morgan',
            last_name='Lee',
            password='testpass123',
        )
        self.organization = Organization.objects.create(name='Account Workspace', slug='account-workspace')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.ASSOCIATE,
            phone='555-0100',
            department='Legal',
            bar_number='BAR-100',
            hourly_rate='300.00',
            bio='Legacy professional profile data.',
            language=UserProfile.Language.EN,
            timezone='UTC',
            date_format=UserProfile.DateFormat.DMY_LONG,
            notify_contract_updates=True,
            notify_workflow_events=True,
            notify_security_alerts=True,
        )
        self.client.login(username='account-member', password='testpass123')

    def test_account_page_hides_legacy_fields_and_prepopulates_identity(self):
        response = self.client.get(reverse('profile'))

        self.assertContains(response, 'Workspace access')
        self.assertContains(response, 'Security')
        self.assertContains(response, 'Preferences')
        self.assertContains(response, 'value="Morgan"')
        self.assertContains(response, 'value="member@example.com"')
        self.assertNotContains(response, 'name="bar_number"')
        self.assertNotContains(response, 'name="hourly_rate"')
        self.assertNotContains(response, 'name="bio"')
        self.assertNotContains(response, 'name="role"')

    def test_account_header_is_compact_without_eyebrow(self):
        response = self.client.get(reverse('profile'))
        body = response.content.decode()
        main = body.split('<main class="profile-page"', 1)[-1].split('</main>', 1)[0]
        self.assertNotIn('CLM One account', main)
        self.assertNotIn('dc-ds-eyebrow', main)
        self.assertIn('Member since', main)
        self.assertIn('member@example.com', main)
        self.assertIn('Member', main)
        self.assertContains(response, 'Save changes')
        self.assertContains(response, 'id="account-save-button" disabled>Save changes</button>')

    def test_workspace_access_uses_clarified_labels(self):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Access level')
        self.assertContains(response, 'Permissions')
        self.assertContains(response, 'Your membership role in this workspace')
        self.assertNotContains(response, 'Workspace role')
        self.assertNotContains(response, 'Product role')

    def test_preferences_expose_language_timezone_date_and_notifications(self):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'name="language"')
        self.assertContains(response, 'name="timezone"')
        self.assertContains(response, 'name="date_format"')
        self.assertContains(response, 'name="notify_contract_updates"')
        self.assertContains(response, 'name="notify_workflow_events"')
        self.assertContains(response, 'name="notify_security_alerts"')
        self.assertContains(response, 'Notification settings')

    def test_mfa_setup_is_collapsed_until_started(self):
        response = self.client.get(reverse('profile'))
        self.assertContains(response, 'Set up MFA')
        self.assertContains(response, 'Prefer an authenticator app or passkey')
        self.assertNotContains(response, 'name="mfa_enrollment_code"')
        self.assertNotContains(response, 'Send verification code')

        started = self.client.post(reverse('profile'), {'action': 'start_mfa_setup'})
        self.assertEqual(started.status_code, 302)
        response = self.client.get(started['Location'])
        self.assertContains(response, 'Send email verification code')
        self.assertContains(response, 'name="mfa_enrollment_code"')
        self.assertContains(response, 'Email verification code')

    def test_role_post_is_ignored_by_self_service_account_update(self):
        response = self.client.post(reverse('profile'), {
            'action': 'save',
            'first_name': 'Morgan',
            'last_name': 'Lee',
            'email': 'member@example.com',
            'phone': '555-0200',
            'department': 'Legal Operations',
            'role': UserProfile.Role.ADMIN,
        })

        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.role, UserProfile.Role.ASSOCIATE)
        self.assertEqual(self.profile.department, 'Legal Operations')
        self.assertEqual(self.profile.language, UserProfile.Language.EN)
        self.assertTrue(self.profile.notify_contract_updates)

    def test_preferences_save_updates_controls(self):
        response = self.client.post(reverse('profile'), {
            'action': 'save',
            'first_name': 'Morgan',
            'last_name': 'Lee',
            'email': 'member@example.com',
            'phone': '555-0100',
            'department': 'Legal',
            'language': UserProfile.Language.NL,
            'timezone': 'Europe/Amsterdam',
            'date_format': UserProfile.DateFormat.ISO,
            'notify_contract_updates': 'on',
            'notify_security_alerts': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.language, UserProfile.Language.NL)
        self.assertEqual(self.profile.timezone, 'Europe/Amsterdam')
        self.assertEqual(self.profile.date_format, UserProfile.DateFormat.ISO)
        self.assertTrue(self.profile.notify_contract_updates)
        self.assertFalse(self.profile.notify_workflow_events)
        self.assertTrue(self.profile.notify_security_alerts)

    def test_account_page_hides_authenticated_footer(self):
        response = self.client.get(reverse('profile'))
        self.assertTrue(response.context['hide_app_footer'])
        self.assertNotContains(response, 'All rights reserved.')
