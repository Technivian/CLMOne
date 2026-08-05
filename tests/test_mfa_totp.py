from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contracts.models import AuditLog, Organization, OrganizationMembership, UserProfile
from contracts.services.mfa_totp import (
    begin_totp_enrollment,
    confirm_totp_enrollment,
    decrypt_totp_secret,
    encrypt_totp_secret,
    hotp_code,
    pending_totp_secret,
    totp_code,
    totp_provisioning_uri,
    totp_qr_data_uri,
    verify_totp_challenge,
)


User = get_user_model()
TEST_FERNET_KEY = Fernet.generate_key().decode('ascii')
TEST_TIME = 1_700_000_000


@override_settings(
    MFA_TOTP_ENROLLMENT_ENABLED=True,
    MFA_TOTP_ENCRYPTION_KEY=TEST_FERNET_KEY,
    MFA_TOTP_ISSUER='CLM One Test',
)
class TotpServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='totp-user',
            email='totp@example.com',
            password='StrongPass!123',
        )
        self.profile = UserProfile.objects.create(user=self.user)

    def test_hotp_matches_rfc_4226_vectors(self):
        secret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
        expected = ('755224', '287082', '359152', '969429', '338314')
        self.assertEqual(
            tuple(hotp_code(secret, counter) for counter in range(len(expected))),
            expected,
        )

    def test_secret_is_encrypted_and_round_trips(self):
        secret = 'JBSWY3DPEHPK3PXP'
        encrypted = encrypt_totp_secret(secret)
        self.assertTrue(encrypted.startswith('enc:v1:'))
        self.assertNotIn(secret, encrypted)
        self.assertEqual(decrypt_totp_secret(encrypted), secret)

    def test_confirmation_and_challenge_are_replay_safe(self):
        secret = begin_totp_enrollment(self.profile)
        first_code = totp_code(secret, at_time=TEST_TIME)
        self.assertTrue(
            confirm_totp_enrollment(self.profile, first_code, at_time=TEST_TIME)
        )
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.uses_totp)
        self.assertFalse(
            verify_totp_challenge(self.profile, first_code, at_time=TEST_TIME)
        )

        next_code = totp_code(secret, at_time=TEST_TIME + 30)
        self.assertTrue(
            verify_totp_challenge(self.profile, next_code, at_time=TEST_TIME + 30)
        )
        self.assertFalse(
            verify_totp_challenge(self.profile, next_code, at_time=TEST_TIME + 30)
        )

    def test_provisioning_material_is_local_and_scannable(self):
        secret = begin_totp_enrollment(self.profile)
        uri = totp_provisioning_uri(secret=secret, account_name=self.user.email)
        self.assertTrue(uri.startswith('otpauth://totp/'))
        self.assertIn('issuer=CLM+One+Test', uri)
        self.assertIn(f'secret={secret}', uri)
        qr = totp_qr_data_uri(secret=secret, account_name=self.user.email)
        self.assertTrue(qr.startswith('data:image/png;base64,'))

    def test_pending_secret_is_not_returned_after_confirmation(self):
        secret = begin_totp_enrollment(self.profile)
        self.assertEqual(pending_totp_secret(self.profile), secret)
        self.assertTrue(
            confirm_totp_enrollment(
                self.profile,
                totp_code(secret, at_time=TEST_TIME),
                at_time=TEST_TIME,
            )
        )
        self.assertEqual(pending_totp_secret(self.profile), '')

    def test_previous_key_is_accepted_and_factor_is_lazily_rotated(self):
        old_key = Fernet.generate_key().decode('ascii')
        new_key = Fernet.generate_key().decode('ascii')
        with self.settings(MFA_TOTP_ENCRYPTION_KEY=old_key):
            secret = begin_totp_enrollment(self.profile)
            old_ciphertext = self.profile.mfa_totp_secret_encrypted

        with self.settings(
            MFA_TOTP_ENCRYPTION_KEY=new_key,
            MFA_TOTP_ENCRYPTION_PREVIOUS_KEYS=[old_key],
        ):
            self.assertTrue(
                confirm_totp_enrollment(
                    self.profile,
                    totp_code(secret, at_time=TEST_TIME),
                    at_time=TEST_TIME,
                )
            )
            self.profile.refresh_from_db()
            self.assertNotEqual(self.profile.mfa_totp_secret_encrypted, old_ciphertext)
            self.assertEqual(
                decrypt_totp_secret(self.profile.mfa_totp_secret_encrypted),
                secret,
            )

    def test_new_recovery_codes_are_high_entropy_normalized_and_single_use(self):
        codes = self.profile.issue_mfa_recovery_codes()
        self.assertEqual(len(codes), 8)
        self.assertTrue(all(len(code.replace('-', '')) == 20 for code in codes))
        entered_with_spaces = codes[0].lower().replace('-', ' ')
        self.assertTrue(self.profile.verify_mfa_recovery_code(entered_with_spaces))
        self.assertFalse(self.profile.verify_mfa_recovery_code(codes[0]))


@override_settings(
    MFA_TOTP_ENROLLMENT_ENABLED=True,
    MFA_TOTP_ENCRYPTION_KEY=TEST_FERNET_KEY,
    MFA_TOTP_ISSUER='CLM One Test',
)
class TotpFlowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='totp-flow',
            email='totp-flow@example.com',
            password='StrongPass!123',
        )
        self.org = Organization.objects.create(
            name='TOTP Workspace',
            slug='totp-workspace',
            require_mfa=True,
        )
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def _enroll(self, *, at_time=TEST_TIME):
        response = self.client.post(reverse('mfa_enroll'), {'action': 'start_totp'})
        self.assertRedirects(response, reverse('mfa_enroll'), fetch_redirect_response=False)
        self.profile.refresh_from_db()
        secret = pending_totp_secret(self.profile)
        self.assertTrue(secret)
        with patch('contracts.services.mfa_totp.time.time', return_value=at_time):
            response = self.client.post(
                reverse('mfa_enroll'),
                {'action': 'verify_totp', 'code': totp_code(secret, at_time=at_time)},
            )
        self.assertRedirects(response, reverse('profile'), fetch_redirect_response=False)
        self.profile.refresh_from_db()
        return secret

    def test_enrollment_renders_qr_confirms_and_records_secret_free_audit(self):
        self.client.post(reverse('mfa_enroll'), {'action': 'start_totp'})
        self.profile.refresh_from_db()
        secret = pending_totp_secret(self.profile)
        page = self.client.get(reverse('mfa_enroll'))
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'QR code for CLM One authenticator setup')
        self.assertContains(page, secret)
        self.assertNotIn(secret, self.profile.mfa_totp_secret_encrypted)

        with patch('contracts.services.mfa_totp.time.time', return_value=TEST_TIME):
            response = self.client.post(
                reverse('mfa_enroll'),
                {'action': 'verify_totp', 'code': totp_code(secret, at_time=TEST_TIME)},
            )
        self.assertRedirects(response, reverse('profile'), fetch_redirect_response=False)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.mfa_enabled)
        self.assertTrue(self.profile.uses_totp)
        self.assertEqual(self.profile.mfa_recovery_code_count, 8)
        event = AuditLog.objects.get(event_type='mfa.totp_enrolled')
        self.assertEqual(event.organization, self.org)
        self.assertNotIn(secret, str(event.changes))

    def test_login_does_not_send_email_for_totp_user(self):
        self._enroll()
        client = Client()
        with patch('contracts.views_domains.core._send_mfa_email') as send_email:
            response = client.post(
                reverse('login'),
                {'username': self.user.username, 'password': 'StrongPass!123'},
            )
        self.assertRedirects(response, reverse('mfa_challenge'), fetch_redirect_response=False)
        send_email.assert_not_called()

    def test_challenge_verifies_next_step_records_audit_and_rejects_replay(self):
        secret = self._enroll()
        session = self.client.session
        session['mfa_verified'] = False
        session.save()
        challenge_time = TEST_TIME + 30
        code = totp_code(secret, at_time=challenge_time)
        with patch('contracts.services.mfa_totp.time.time', return_value=challenge_time):
            response = self.client.post(reverse('mfa_challenge'), {'code': code})
        self.assertRedirects(response, '/dashboard/', fetch_redirect_response=False)
        self.assertTrue(self.client.session['mfa_verified'])
        event = AuditLog.objects.get(event_type='mfa.totp_verified')
        self.assertEqual(event.organization, self.org)

        session = self.client.session
        session['mfa_verified'] = False
        session.save()
        with patch('contracts.services.mfa_totp.time.time', return_value=challenge_time):
            replay = self.client.post(reverse('mfa_challenge'), {'code': code})
        self.assertEqual(replay.status_code, 200)
        self.assertContains(replay, 'was not accepted')
        self.assertFalse(self.client.session.get('mfa_verified', False))

    def test_corrupt_encrypted_secret_fails_closed(self):
        self.profile.mfa_enabled = True
        self.profile.mfa_totp_secret_encrypted = 'enc:v1:not-a-valid-token'
        self.profile.mfa_totp_confirmed_at = self.profile.updated_at
        self.profile.save()
        session = self.client.session
        session['mfa_verified'] = False
        session.save()
        response = self.client.post(reverse('mfa_challenge'), {'code': '123456'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'was not accepted')
        self.assertFalse(self.client.session.get('mfa_verified', False))

    def test_password_only_session_cannot_replace_existing_totp_factor(self):
        self._enroll()
        self.profile.refresh_from_db()
        original_ciphertext = self.profile.mfa_totp_secret_encrypted
        session = self.client.session
        session['mfa_verified'] = False
        session.save()

        response = self.client.post(reverse('mfa_enroll'), {'action': 'start_totp'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('mfa_challenge')))
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.mfa_totp_secret_encrypted, original_ciphertext)
        self.assertTrue(self.profile.uses_totp)

    def test_verified_email_factor_can_upgrade_to_authenticator(self):
        self.profile.mfa_enabled = True
        self.profile.mfa_verified_at = timezone.now()
        self.profile.save(update_fields=['mfa_enabled', 'mfa_verified_at', 'updated_at'])
        session = self.client.session
        session['mfa_verified'] = True
        session.save()
        response = self.client.post(
            reverse('profile'),
            {'action': 'start_totp_upgrade'},
        )
        self.assertRedirects(response, reverse('mfa_enroll'), fetch_redirect_response=False)

    @override_settings(MFA_RATE_LIMIT_REQUESTS=2, MFA_RATE_LIMIT_WINDOW_SECONDS=60)
    def test_challenge_is_rate_limited_per_user_and_ip(self):
        self._enroll()
        session = self.client.session
        session['mfa_verified'] = False
        session.save()
        for _ in range(2):
            response = self.client.post(
                reverse('mfa_challenge'),
                {'code': '000000'},
                REMOTE_ADDR='203.0.113.44',
            )
            self.assertEqual(response.status_code, 200)
        blocked = self.client.post(
            reverse('mfa_challenge'),
            {'code': '000000'},
            REMOTE_ADDR='203.0.113.44',
        )
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Retry-After', blocked)
