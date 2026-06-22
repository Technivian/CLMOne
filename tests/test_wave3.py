"""Wave 3 tests: C15, SEC-1, SEC-2, SEC-3."""
import hashlib
import json
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    AuditLog,
    Organization,
    OrganizationAPIToken,
    OrganizationInvitation,
    OrganizationMembership,
    OrgPolicy,
    UserProfile,
)
from contracts.middleware import log_action

User = get_user_model()


def _make_user(username, email=None):
    u = User.objects.create_user(username=username, password='pass', email=email or f'{username}@test.com')
    return u


def _make_org(name='Acme'):
    return Organization.objects.create(name=name, slug=name.lower().replace(' ', '-'), is_active=True)


def _membership(user, org, role='MEMBER'):
    return OrganizationMembership.objects.create(
        organization=org, user=user, role=role, is_active=True
    )


# ---------------------------------------------------------------------------
# C15: Invite acceptance flow
# ---------------------------------------------------------------------------

class InviteAcceptFlowTest(TestCase):
    def setUp(self):
        self.org = _make_org('InvOrg')
        self.user = _make_user('invitee', email='invitee@test.com')
        self.token_val = uuid.uuid4()
        self.client = Client()
        self.client.login(username='invitee', password='pass')
        self.invitation = OrganizationInvitation.objects.create(
            organization=self.org,
            email='invitee@test.com',
            role='MEMBER',
            token=self.token_val,
            status=OrganizationInvitation.Status.PENDING,
            expires_at=timezone.now() + timedelta(days=7),
        )
        self.url = reverse('contracts:accept_organization_invite', args=[str(self.token_val)])

    def test_get_renders_invite_details(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'InvOrg')
        self.assertContains(r, 'invitee@test.com')

    def test_post_accepts_invite_and_creates_membership(self):
        r = self.client.post(self.url)
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, OrganizationInvitation.Status.ACCEPTED)
        self.assertTrue(
            OrganizationMembership.objects.filter(
                organization=self.org, user=self.user, is_active=True
            ).exists()
        )

    def test_expired_invite_redirects_with_error(self):
        self.invitation.expires_at = timezone.now() - timedelta(hours=1)
        self.invitation.save()
        r = self.client.get(self.url)
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)

    def test_email_mismatch_redirects_to_login(self):
        other_user = _make_user('other', email='other@test.com')
        c = Client()
        c.login(username='other', password='pass')
        r = c.get(self.url)
        self.assertRedirects(r, '/login/', fetch_redirect_response=False)

    def test_already_accepted_invite_returns_error(self):
        self.invitation.status = OrganizationInvitation.Status.ACCEPTED
        self.invitation.save()
        r = self.client.get(self.url)
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)


# ---------------------------------------------------------------------------
# SEC-2: API key expiry
# ---------------------------------------------------------------------------

class APITokenExpiryTest(TestCase):
    def setUp(self):
        self.org = _make_org('TokenOrg')
        self.raw_token = 'myrawtoken123'

    def _make_token(self, expires_at=None):
        return OrganizationAPIToken.objects.create(
            organization=self.org,
            label='Test token',
            token_hash=OrganizationAPIToken._hash_token(self.raw_token),
            scopes=['contracts:read'],
            is_active=True,
            expires_at=expires_at,
        )

    def test_token_without_expiry_is_not_expired(self):
        token = self._make_token(expires_at=None)
        self.assertFalse(token.is_expired)

    def test_token_with_future_expiry_is_not_expired(self):
        token = self._make_token(expires_at=timezone.now() + timedelta(days=30))
        self.assertFalse(token.is_expired)

    def test_token_with_past_expiry_is_expired(self):
        token = self._make_token(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertTrue(token.is_expired)

    def test_expired_token_rejected_by_api(self):
        self._make_token(expires_at=timezone.now() - timedelta(hours=1))
        c = Client()
        r = c.get(
            '/api/v1/contracts/',
            HTTP_AUTHORIZATION=f'Bearer {self.raw_token}',
        )
        self.assertNotEqual(r.status_code, 200)

    def test_valid_token_accepted_by_api(self):
        user = _make_user('apiuser')
        _membership(user, self.org, role='ADMIN')
        self._make_token(expires_at=timezone.now() + timedelta(days=1))
        c = Client()
        r = c.get(
            '/api/v1/contracts/',
            HTTP_AUTHORIZATION=f'Bearer {self.raw_token}',
        )
        self.assertNotIn(r.status_code, [401, 403])


# ---------------------------------------------------------------------------
# SEC-3: Audit log tamper detection
# ---------------------------------------------------------------------------

class AuditLogHashTest(TestCase):
    def setUp(self):
        self.user = _make_user('auditor')

    def test_log_action_sets_entry_hash(self):
        log_action(self.user, AuditLog.Action.VIEW, 'Contract', object_id=1)
        entry = AuditLog.objects.filter(user=self.user, model_name='Contract').latest('timestamp')
        self.assertTrue(bool(entry.entry_hash), 'entry_hash must be set')
        self.assertEqual(len(entry.entry_hash), 64)  # SHA-256 hex

    def test_entry_hash_is_deterministic(self):
        # Phase 3: entry_hash is now the per-org CHAIN hash (covers prev_hash,
        # seq, org, actor, outcome, ...), computed by contracts.services.audit.
        # Verify it is deterministic by recomputing from the stored fields.
        log_action(self.user, AuditLog.Action.VIEW, 'Document', object_id=99)
        entry = AuditLog.objects.filter(user=self.user, model_name='Document').latest('timestamp')
        from contracts.services.audit import compute_entry_hash
        expected = compute_entry_hash(
            prev_hash=entry.prev_hash, organization_id=entry.organization_id, seq=entry.seq,
            event_type=entry.event_type, action=entry.action, actor_type=entry.actor_type,
            actor_id=entry.user_id, model_name=entry.model_name, object_id=entry.object_id,
            outcome=entry.outcome, request_id=entry.request_id, job_run_id=entry.job_run_id,
            changes=entry.changes,
        )
        self.assertEqual(entry.entry_hash, expected)

    def test_compute_hash_changes_when_action_changes(self):
        log_action(self.user, AuditLog.Action.VIEW, 'Matter', object_id=7)
        entry = AuditLog.objects.filter(user=self.user, model_name='Matter').latest('timestamp')
        original = entry.entry_hash
        entry.action = AuditLog.Action.DELETE
        tampered = entry.compute_hash()
        self.assertNotEqual(original, tampered)

    def test_entry_hash_field_max_length(self):
        f = AuditLog._meta.get_field('entry_hash')
        self.assertEqual(f.max_length, 64)


# ---------------------------------------------------------------------------
# SEC-1: MFA enforcement
# ---------------------------------------------------------------------------

class MFAEnforcementTest(TestCase):
    def setUp(self):
        self.org = _make_org('MFAOrg')
        # Phase 1 made Organization.require_mfa the authoritative MFA flag
        # (OrgPolicy.mfa_required is now a mirror). Set both for clarity.
        self.org.require_mfa = True
        self.org.save(update_fields=['require_mfa'])
        self.policy, _ = OrgPolicy.objects.get_or_create(organization=self.org)
        self.policy.mfa_required = True
        self.policy.save()
        self.user = _make_user('mfauser', email='mfauser@test.com')
        _membership(self.user, self.org, role='ADMIN')
        # Put the org in the session via active_organization_id
        self.client = Client()
        self.client.login(username='mfauser', password='pass')
        session = self.client.session
        session['active_organization_id'] = self.org.pk
        session.save()

    @patch('contracts.views_domains.core._send_mfa_email')
    def test_login_redirects_to_challenge_when_mfa_enabled(self, mock_send):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.mfa_enabled = True
        profile.save()
        c = Client()
        with patch('contracts.views_domains.core._send_mfa_email'):
            r = c.post(reverse('login'), {
                'username': 'mfauser',
                'password': 'pass',
            })
        self.assertRedirects(r, reverse('mfa_challenge'), fetch_redirect_response=False)

    @patch('contracts.views_domains.core._send_mfa_email')
    def test_login_redirects_to_enroll_when_mfa_not_enabled(self, mock_send):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.mfa_enabled = False
        profile.save()
        c = Client()
        r = c.post(reverse('login'), {'username': 'mfauser', 'password': 'pass'})
        self.assertRedirects(r, reverse('mfa_enroll'), fetch_redirect_response=False)

    def test_challenge_correct_code_sets_session_flag(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        code = profile.issue_mfa_enrollment_code()
        r = self.client.post(reverse('mfa_challenge'), {'code': code, 'next': '/dashboard/'})
        self.assertRedirects(r, '/dashboard/', fetch_redirect_response=False)
        self.assertTrue(self.client.session.get('mfa_verified'))

    def test_challenge_wrong_code_shows_error(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.issue_mfa_enrollment_code()
        r = self.client.post(reverse('mfa_challenge'), {'code': '000000', 'next': '/dashboard/'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Invalid or expired code')
        self.assertFalse(self.client.session.get('mfa_verified', False))

    @patch('contracts.views_domains.core._send_mfa_email')
    def test_enroll_send_issues_code(self, mock_send):
        r = self.client.post(reverse('mfa_enroll'), {'action': 'send'})
        self.assertRedirects(r, reverse('mfa_enroll'), fetch_redirect_response=False)
        profile = UserProfile.objects.get(user=self.user)
        self.assertTrue(bool(profile.mfa_enrollment_code_hash))

    def test_enroll_valid_code_enables_mfa_and_sets_session(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        code = profile.issue_mfa_enrollment_code()
        r = self.client.post(reverse('mfa_enroll'), {'code': code})
        self.assertRedirects(r, reverse('dashboard'), fetch_redirect_response=False)
        profile.refresh_from_db()
        self.assertTrue(profile.mfa_enabled)
        self.assertTrue(self.client.session.get('mfa_verified'))

    def test_check_mfa_code_clears_hash_after_success(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        code = profile.issue_mfa_enrollment_code()
        result = profile.check_mfa_code(code)
        self.assertTrue(result)
        profile.refresh_from_db()
        self.assertFalse(bool(profile.mfa_enrollment_code_hash))

    def test_check_mfa_code_wrong_code_returns_false(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        profile.issue_mfa_enrollment_code()
        self.assertFalse(profile.check_mfa_code('999999'))


# ---------------------------------------------------------------------------
# C10/D15: Open-redirect prevention on `next`
# ---------------------------------------------------------------------------

class OpenRedirectTest(TestCase):
    def setUp(self):
        self.user = _make_user('redirectuser', email='redirectuser@test.com')

    def test_login_next_external_url_ignored(self):
        r = self.client.post(
            reverse('login') + '?next=https://evil.com',
            {'username': 'redirectuser', 'password': 'pass'},
        )
        location = r.get('Location', '')
        self.assertNotIn('evil.com', location)

    def test_login_next_protocol_relative_ignored(self):
        r = self.client.post(
            reverse('login') + '?next=//evil.com/steal',
            {'username': 'redirectuser', 'password': 'pass'},
        )
        location = r.get('Location', '')
        self.assertNotIn('evil.com', location)

    def test_login_next_relative_allowed(self):
        r = self.client.post(
            reverse('login') + '?next=/contracts/',
            {'username': 'redirectuser', 'password': 'pass'},
        )
        location = r.get('Location', '')
        self.assertIn('/contracts/', location)

    def test_mfa_challenge_next_external_url_ignored(self):
        self.client.login(username='redirectuser', password='pass')
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        code = profile.issue_mfa_enrollment_code()
        r = self.client.post(
            reverse('mfa_challenge') + '?next=https://evil.com',
            {'code': code, 'next': 'https://evil.com'},
        )
        location = r.get('Location', '')
        self.assertNotIn('evil.com', location)
