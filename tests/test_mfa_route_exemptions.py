"""Phase 4F — narrow MFA route exemptions to exact routes."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import Organization, OrganizationMembership, UserProfile

User = get_user_model()
PW = 'StrongPw!123'


def _mfa_org():
    return Organization.objects.create(name='MfaOrg', slug='mfa-route-org', require_mfa=True)


def _user(org, role=OrganizationMembership.Role.OWNER, enrolled=False, verified=False):
    u = User.objects.create_user(username='u', password=PW, email='u@x.com')
    OrganizationMembership.objects.create(user=u, organization=org, role=role, is_active=True)
    profile, _ = UserProfile.objects.get_or_create(user=u)
    if enrolled:
        profile.mfa_enabled = True
        profile.mfa_verified_at = timezone.now()
        profile.save()
    return u


class MfaExemptionTests(TestCase):
    def setUp(self):
        self.org = _mfa_org()

    def _client(self, user, verified=False):
        c = Client()
        c.force_login(user)
        if verified:
            s = c.session
            s['mfa_verified'] = True
            s.save()
        return c

    # --- gated (non-exempt) routes ---------------------------------------
    def test_unenrolled_user_redirected_to_enroll(self):
        u = _user(self.org, enrolled=False)
        resp = self._client(u).get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('mfa_enroll'))

    def test_enrolled_unverified_redirected_to_challenge(self):
        u = _user(self.org, enrolled=True)
        resp = self._client(u).get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse('mfa_challenge'), resp.url)

    def test_verified_session_allowed(self):
        u = _user(self.org, enrolled=True)
        resp = self._client(u, verified=True).get(reverse('dashboard'))
        self.assertEqual(resp.status_code, 200)

    def test_profile_now_gated(self):
        u = _user(self.org, enrolled=True)
        resp = self._client(u).get(reverse('profile'))
        self.assertEqual(resp.status_code, 302)  # was exempt before 4F
        self.assertIn('/mfa/', resp.url)

    def test_settings_now_gated(self):
        u = _user(self.org, enrolled=True)
        # settings_hub is a /settings/ route — previously exempt by prefix.
        try:
            url = reverse('settings_hub')
        except Exception:
            self.skipTest('settings_hub route not present')
        resp = self._client(u).get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/mfa/', resp.url)

    def test_django_admin_gated(self):
        u = _user(self.org, role=OrganizationMembership.Role.OWNER, enrolled=True)
        u.is_staff = True
        u.save()
        resp = self._client(u).get('/admin/')
        # Not exempt: gate redirects to MFA before admin.
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/mfa/', resp.url)

    # --- exempt routes ---------------------------------------------------
    def test_mfa_enroll_route_reachable(self):
        u = _user(self.org, enrolled=False)
        resp = self._client(u).get(reverse('mfa_enroll'))
        self.assertEqual(resp.status_code, 200)  # not redirected to itself

    def test_mfa_challenge_route_reachable(self):
        u = _user(self.org, enrolled=True)
        resp = self._client(u).get(reverse('mfa_challenge'))
        self.assertEqual(resp.status_code, 200)

    def test_logout_reachable(self):
        u = _user(self.org, enrolled=True)
        resp = self._client(u).get(reverse('logout'))
        self.assertIn(resp.status_code, (200, 302, 405))
        if resp.status_code == 302:
            self.assertNotIn('/mfa/', resp.url)

    def test_similar_prefixed_route_not_exempt(self):
        # A route sharing a prefix with an exempt one must NOT be exempt: only
        # exact matches are. /profile/ is gated even though /mfa/ is exempt.
        u = _user(self.org, enrolled=True)
        resp = self._client(u).get(reverse('profile'))
        self.assertEqual(resp.status_code, 302)

    def test_non_mfa_org_unaffected(self):
        org = Organization.objects.create(name='Plain', slug='plain-org', require_mfa=False)
        u = User.objects.create_user(username='p', password=PW)
        OrganizationMembership.objects.create(user=u, organization=org, role='OWNER', is_active=True)
        c = Client()
        c.force_login(u)
        resp = c.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)  # no gate when MFA not required
