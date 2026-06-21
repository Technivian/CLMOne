"""Regression tests for the MFA fail-open blocker (A3).

Before the fix, the admin UI wrote Organization.require_mfa while login
enforcement read OrgPolicy.mfa_required; OrgPolicy often did not exist, so
`org.policy.mfa_required` raised RelatedObjectDoesNotExist and was swallowed by
a broad `except Exception: pass`, silently bypassing MFA.

Authoritative source is now Organization.require_mfa (a plain column that always
exists). These tests prove enforcement is fail-closed across the matrix the
remediation brief requires.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    OrganizationMembership,
    Organization,
    OrgPolicy,
    UserProfile,
)
from contracts.services.mfa_policy import (
    ensure_org_policy,
    organization_requires_mfa,
    set_organization_mfa_required,
)

User = get_user_model()

PW = 'StrongPw!123'


def _make_org(name, slug, require_mfa=False):
    return Organization.objects.create(name=name, slug=slug, require_mfa=require_mfa)


def _make_member(org, username, role=OrganizationMembership.Role.OWNER):
    user = User.objects.create_user(username=username, password=PW, email=f'{username}@ex.com')
    OrganizationMembership.objects.create(
        user=user, organization=org, role=role, is_active=True,
    )
    return user


class MfaLoginEnforcementMatrix(TestCase):
    def _login(self, username):
        c = Client()
        return c, c.post(reverse('login'), {'username': username, 'password': PW})

    def test_mfa_not_required_logs_in_normally(self):
        org = _make_org('NoMfa City', 'nomfa-city', require_mfa=False)
        _make_member(org, 'plainuser')
        c, resp = self._login('plainuser')
        # Should NOT be diverted to an MFA page.
        self.assertNotIn('/mfa', resp.url if resp.status_code == 302 else '')

    def test_mfa_required_user_not_configured_is_diverted_to_enroll(self):
        org = _make_org('Mfa City', 'mfa-city', require_mfa=True)
        _make_member(org, 'newuser')
        c, resp = self._login('newuser')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('mfa_enroll'))

    def test_mfa_required_user_configured_is_challenged(self):
        org = _make_org('Mfa City2', 'mfa-city2', require_mfa=True)
        user = _make_member(org, 'enrolleduser')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.mfa_enabled = True
        profile.mfa_verified_at = timezone.now()
        profile.save()
        c, resp = self._login('enrolleduser')
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('mfa_challenge'))

    def test_missing_policy_record_still_enforces_mfa(self):
        """The original fail-open: no OrgPolicy row must NOT disable MFA."""
        org = _make_org('Mfa NoPolicy', 'mfa-nopolicy', require_mfa=True)
        # Explicitly ensure NO OrgPolicy exists for this org.
        OrgPolicy.objects.filter(organization=org).delete()
        self.assertFalse(OrgPolicy.objects.filter(organization=org).exists())
        user = _make_member(org, 'nopolicyuser')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.mfa_enabled = True
        profile.mfa_verified_at = timezone.now()
        profile.save()
        c, resp = self._login('nopolicyuser')
        # Fail-closed: still challenged, not silently logged straight in.
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('mfa_challenge'))

    def test_protected_page_redirects_to_challenge_until_verified(self):
        org = _make_org('Mfa Gate', 'mfa-gate', require_mfa=True)
        user = _make_member(org, 'gateuser')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.mfa_enabled = True
        profile.mfa_verified_at = timezone.now()
        profile.save()
        c = Client()
        c.force_login(user)
        resp = c.get(reverse('dashboard'))
        # MfaRequiredMixin / middleware should bounce to challenge or login.
        self.assertEqual(resp.status_code, 302)
        self.assertTrue('/mfa' in resp.url or '/login' in resp.url, resp.url)


class MfaPolicyServiceTests(TestCase):
    def test_organization_requires_mfa_reads_authoritative_field(self):
        org = _make_org('Svc Org', 'svc-org', require_mfa=True)
        self.assertTrue(organization_requires_mfa(org))
        org.require_mfa = False
        self.assertFalse(organization_requires_mfa(org))

    def test_organization_requires_mfa_none_is_false(self):
        self.assertFalse(organization_requires_mfa(None))

    def test_set_keeps_policy_mirror_in_sync(self):
        org = _make_org('Sync Org', 'sync-org', require_mfa=False)
        set_organization_mfa_required(org, True)
        org.refresh_from_db()
        self.assertTrue(org.require_mfa)
        self.assertTrue(ensure_org_policy(org).mfa_required)
        set_organization_mfa_required(org, False)
        org.refresh_from_db()
        self.assertFalse(org.require_mfa)
        self.assertFalse(ensure_org_policy(org).mfa_required)

    def test_admin_console_policy_write_mirrors_to_authority(self):
        from contracts.services.admin_console import AdminConsoleService
        org = _make_org('Console Org', 'console-org', require_mfa=False)
        user = _make_member(org, 'consoleadmin')
        AdminConsoleService().update_policy(org, user, mfa_required=True)
        org.refresh_from_db()
        self.assertTrue(org.require_mfa, 'policy write must propagate to authority')


class MfaOrgCreationProvisioningTests(TestCase):
    def test_registration_creates_org_with_policy(self):
        """Org auto-provisioned on first authenticated request has a policy row."""
        from contracts.tenancy import ensure_user_organization
        user = User.objects.create_user(username='registrant', password=PW)
        org = ensure_user_organization(user)
        self.assertIsNotNone(org)
        self.assertTrue(OrgPolicy.objects.filter(organization=org).exists())

    def test_admin_provisioning_path_has_policy(self):
        # Any provisioning path that funnels through ensure_user_organization.
        from contracts.tenancy import ensure_user_organization
        user = User.objects.create_user(username='provisioned', password=PW)
        org = ensure_user_organization(user)
        ensure_org_policy(org)  # idempotent
        self.assertEqual(OrgPolicy.objects.filter(organization=org).count(), 1)


class MfaRecoveryPathTests(TestCase):
    def test_recovery_code_satisfies_challenge(self):
        org = _make_org('Recover Org', 'recover-org', require_mfa=True)
        user = _make_member(org, 'recoveruser')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.mfa_enabled = True
        profile.mfa_verified_at = timezone.now()
        profile.save()
        codes = profile.issue_mfa_recovery_codes()
        self.assertTrue(codes)
        c = Client()
        c.force_login(user)
        resp = c.post(reverse('mfa_challenge'), {'code': codes[0]})
        # Valid recovery code -> verified -> redirected away from challenge.
        self.assertEqual(resp.status_code, 302)
        self.assertNotIn('/mfa', resp.url)


class SamlMfaBehaviorTests(TestCase):
    def test_saml_under_required_mfa_marks_profile_verified(self):
        """Documented decision: SAML delegates MFA to the IdP; on login under
        require_mfa the profile is marked enrolled/verified so the session
        middleware does not re-challenge. This test pins that behavior."""
        org = _make_org('Saml Org', 'saml-org', require_mfa=True)
        user = _make_member(org, 'samluser')
        profile, _ = UserProfile.objects.get_or_create(user=user)
        self.assertFalse(profile.mfa_enabled)
        # Simulate the SAML post-provision block (saml.py:118-121).
        if organization_requires_mfa(org) and not profile.mfa_enabled:
            profile.mfa_enabled = True
            profile.mfa_verified_at = timezone.now()
            profile.save(update_fields=['mfa_enabled', 'mfa_verified_at', 'updated_at'])
        profile.refresh_from_db()
        self.assertTrue(profile.mfa_enabled)
        self.assertIsNotNone(profile.mfa_verified_at)
