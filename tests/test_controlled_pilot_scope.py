from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import Organization, OrganizationMembership
from django.contrib.auth import get_user_model


class ControlledPilotScopeTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='scope_user', password='pass12345')
        self.org = Organization.objects.create(name='Scope Org', slug='scope-org')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.client.force_login(self.user)

    @override_settings(
        CONTROLLED_PILOT_ENABLED=True,
        BILLING_SELF_SERVE_ENABLED=False,
        TRUST_ACCOUNTING_ENABLED=False,
        GEMINI_AI_ENABLED=False,
    )
    def test_pilot_blocks_excluded_direct_routes(self):
        blocked = (
            '/contracts/billing/',
            '/contracts/clients/',
            '/contracts/matters/',
            '/contracts/invoices/',
            '/contracts/trust-accounts/',
            '/contracts/signatures/',
            '/contracts/new/',
            '/contracts/new/upload/',
            '/contracts/dpa-reviews/',
            '/contracts/workflows/templates/',
            '/contracts/approval-rules/',
        )
        for path in blocked:
            response = self.client.get(path, follow=False)
            self.assertIn(response.status_code, (302, 403), msg=path)
            if response.status_code == 302:
                self.assertNotIn(path.rstrip('/'), response.url.rstrip('/'), msg=path)

    @override_settings(
        CONTROLLED_PILOT_ENABLED=True,
        BILLING_SELF_SERVE_ENABLED=False,
        TRUST_ACCOUNTING_ENABLED=False,
        GEMINI_AI_ENABLED=False,
    )
    def test_pilot_allows_obligations_dates_and_reminders(self):
        """PILOT_SCOPE.md lists dates/expiry/renewal/notice reminders as an
        approved in-scope capability; the route allowlist must match."""
        response = self.client.get('/contracts/obligations/', follow=False)
        self.assertEqual(response.status_code, 200)
        # The legacy /contracts/deadlines/ list redirects here unconditionally
        # (deadlines.py: "Phase 4 retires it in favor of Obligations") and
        # must reach the same now-allowed surface, not bounce to dashboard.
        legacy = self.client.get('/contracts/deadlines/', follow=True)
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.redirect_chain[-1][0], '/contracts/obligations/')

    @override_settings(CONTROLLED_PILOT_ENABLED=True, GEMINI_AI_ENABLED=False)
    def test_pilot_allows_governed_builders(self):
        for name in (
            'contracts:contract_template_picker',
            'contracts:msa_workflow_builder',
            'contracts:nda_workflow_builder',
            'contracts:dpa_workflow_builder',
            'contracts:repository',
        ):
            response = self.client.get(reverse(name))
            self.assertNotEqual(response.status_code, 404, msg=name)
            # Must not bounce to dashboard solely due to pilot denylist.
            if response.status_code == 302:
                self.assertNotEqual(response.url, reverse('dashboard'), msg=name)

    @override_settings(CONTROLLED_PILOT_ENABLED=False, BILLING_SELF_SERVE_ENABLED=False)
    def test_billing_flag_blocks_without_full_pilot_mode(self):
        response = self.client.get('/contracts/billing/', follow=False)
        self.assertEqual(response.status_code, 302)
