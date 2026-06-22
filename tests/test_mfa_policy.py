from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import AuditLog, Organization, OrganizationMembership, UserProfile


User = get_user_model()


class MfaPolicyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='mfa-user',
            email='mfa@example.com',
            password='testpass123',
            first_name='Mfa',
            last_name='User',
        )
        self.org = Organization.objects.create(name='MFA Org', slug='mfa-org', require_mfa=True)
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)

    def _verify_session(self):
        # Phase 4F: profile MFA-management requires a completed MFA session
        # (initial enrollment uses the dedicated, exempt mfa_enroll route).
        session = self.client.session
        session['mfa_verified'] = True
        session.save()

    def _profile_payload(self):
        return {
            'first_name': 'Mfa',
            'last_name': 'User',
            'email': 'mfa@example.com',
            'role': self.profile.role,
            'phone': '',
            'bar_number': '',
            'department': '',
            'hourly_rate': '',
            'bio': 'Security focused',
            'mfa_enabled': 'on',
            'mfa_enrollment_code': '123456',
        }

    @patch('contracts.views_domains.actions.send_mail')
    @patch('contracts.models.secrets.randbelow', return_value=123456)
    def test_mfa_required_org_blocks_dashboard_until_profile_enabled(self, mock_randbelow, mock_send_mail):
        self.assertTrue(self.client.login(username='mfa-user', password='testpass123'))

        blocked = self.client.get(reverse('dashboard'))
        self.assertEqual(blocked.status_code, 302)
        # Fail-closed MFA gate sends un-enrolled users to the dedicated (exempt)
        # enrollment page. Dashboard is blocked until MFA is satisfied. Profile
        # is now gated too (Phase 4F) — enrollment goes through mfa_enroll.
        self.assertIn(reverse('mfa_enroll'), blocked.url)

        enroll_page = self.client.get(reverse('mfa_enroll'))
        self.assertEqual(enroll_page.status_code, 200)

        # Complete enrollment via the dedicated route: send code, then verify.
        self.client.post(reverse('mfa_enroll'), data={'action': 'send'})
        submit = self.client.post(reverse('mfa_enroll'), data={'code': '123456'})
        self.assertEqual(submit.status_code, 302)

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.mfa_enabled)
        self.assertIsNotNone(self.profile.mfa_verified_at)

        allowed = self.client.get(reverse('dashboard'))
        self.assertEqual(allowed.status_code, 200)

        update = self.client.post(
            reverse('profile'),
            data={
                'first_name': 'Mfa',
                'last_name': 'User',
                'email': 'mfa@example.com',
                'role': self.profile.role,
                'phone': '555-0100',
                'bar_number': '',
                'department': '',
                'hourly_rate': '',
                'bio': 'Updated bio',
                'mfa_enabled': 'on',
                'mfa_enrollment_code': '',
            },
        )
        self.assertEqual(update.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.bio, 'Updated bio')

    def test_mfa_enrollment_requires_verification_code(self):
        self.assertTrue(self.client.login(username='mfa-user', password='testpass123'))

        # Enrollment via the dedicated route requires a valid code; a wrong code
        # must not enable MFA.
        submit = self.client.post(reverse('mfa_enroll'), data={'code': '000000'})
        self.assertEqual(submit.status_code, 200)
        self.assertContains(submit, 'Invalid or expired code', html=False)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.mfa_enabled)
        self.assertIsNone(self.profile.mfa_verified_at)

    def test_recovery_codes_can_be_generated_and_used(self):
        self.assertTrue(self.client.login(username='mfa-user', password='testpass123'))
        self.profile.mfa_enabled = True
        self.profile.mfa_verified_at = self.profile.mfa_verified_at or timezone.now()
        self.profile.save(update_fields=['mfa_enabled', 'mfa_verified_at', 'updated_at'])
        # Managing recovery codes on the profile page requires a verified session.
        self._verify_session()

        response = self.client.post(reverse('profile'), data={'action': 'generate_mfa_recovery_codes'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recovery codes', html=False)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.mfa_recovery_code_count, 8)
        recovery_codes = None
        for context in response.context:
            if 'recovery_codes_preview' in context:
                recovery_codes = context['recovery_codes_preview']
                break
        self.assertIsNotNone(recovery_codes)
        self.assertEqual(len(recovery_codes), 8)

        submit = self.client.post(
            reverse('profile'),
            data={
                'first_name': 'Mfa',
                'last_name': 'User',
                'email': 'mfa@example.com',
                'role': self.profile.role,
                'phone': '',
                'bar_number': '',
                'department': '',
                'hourly_rate': '',
                'bio': 'Security focused',
                'mfa_enabled': 'on',
                'mfa_enrollment_code': '',
                'mfa_recovery_code': recovery_codes[0],
            },
        )
        self.assertEqual(submit.status_code, 302)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.mfa_recovery_code_count, 7)
        self.assertTrue(
            AuditLog.objects.filter(
                user=self.user,
                model_name='UserProfile',
                changes__event='mfa_recovery_codes_generated',
            ).exists()
        )
