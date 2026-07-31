"""Default-off Microsoft Entra OIDC security and presentation coverage."""

import json
import os
import subprocess
import sys
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import SuspiciousOperation
from django.core.management import call_command
from django.core.management.base import CommandError
from django.template import engines
from django.test import RequestFactory, TestCase, override_settings

from contracts.auth_backends import CLMOneOIDCAuthenticationBackend
from contracts.models import (
    AuditLog,
    Organization,
    OrganizationMembership,
)


User = get_user_model()
TENANT_ID = '4f6f6627-bcac-4e9b-8af9-b499d197cd86'
ENTRA_SETTINGS = {
    'SSO_ENABLED': True,
    'MICROSOFT_ENTRA_SSO_ENABLED': True,
    'MICROSOFT_ENTRA_TENANT_ID': TENANT_ID,
    'MICROSOFT_ENTRA_ORG_ALLOWLIST': ['synthetic-payroll-workspace'],
    'OIDC_CREATE_USER': False,
    'OIDC_RP_CLIENT_ID': 'synthetic-client-id',
    'OIDC_RP_CLIENT_SECRET': 'synthetic-secret',
    'OIDC_RP_SCOPES': 'openid email profile',
    'OIDC_OP_TOKEN_ENDPOINT': (
        f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'
    ),
    'OIDC_OP_USER_ENDPOINT': 'https://graph.microsoft.com/oidc/userinfo',
    'OIDC_OP_JWKS_ENDPOINT': (
        f'https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys'
    ),
    'OIDC_VERIFY_SSL': True,
    'SSO_ALLOWED_EMAIL_DOMAINS': ['payrollminds.example'],
    'OIDC_OP_DISCOVERY_ENDPOINT': (
        'https://login.microsoftonline.com/'
        f'{TENANT_ID}/v2.0/.well-known/openid-configuration'
    ),
    'APP_BASE_URL': 'https://synthetic-nonprod.example',
}


@override_settings(**ENTRA_SETTINGS)
class MicrosoftEntraBackendTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Synthetic Payroll Workspace',
            slug='synthetic-payroll-workspace',
            identity_provider=Organization.IdentityProvider.OIDC,
        )
        self.user = User.objects.create_user(
            username='preprovisioned-user',
            email='legal@payrollminds.example',
            first_name='Stored',
            last_name='Name',
        )
        self.membership = OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        self.backend = CLMOneOIDCAuthenticationBackend()
        self.backend.request = SimpleNamespace()
        self.token_claims = {
            'tid': TENANT_ID,
            'iss': f'https://login.microsoftonline.com/{TENANT_ID}/v2.0',
            'aud': 'synthetic-client-id',
            'sub': 'synthetic-subject',
        }
        self.userinfo = {
            'preferred_username': 'legal@payrollminds.example',
            'given_name': 'Entra',
            'family_name': 'User',
        }

    def test_exact_tenant_and_issuer_are_required_before_user_lookup(self):
        self.assertTrue(
            self.backend._entra_token_claims_are_valid(self.token_claims)
        )
        for changed_claims in (
            {**self.token_claims, 'tid': '0aa0aa00-0000-4000-8000-000000000000'},
            {**self.token_claims, 'iss': 'https://login.microsoftonline.com/common/v2.0'},
            {key: value for key, value in self.token_claims.items() if key != 'tid'},
            {key: value for key, value in self.token_claims.items() if key != 'iss'},
        ):
            with self.assertRaisesMessage(
                SuspiciousOperation,
                'Microsoft Entra token policy failed.',
            ):
                self.backend.get_or_create_user(
                    'access-token',
                    'id-token',
                    changed_claims,
                )

    def test_preprovisioned_active_member_authenticates_without_email_mutation(self):
        with patch.object(
            self.backend,
            'get_userinfo',
            return_value=self.userinfo,
        ):
            authenticated = self.backend.get_or_create_user(
                'access-token',
                'id-token',
                self.token_claims,
            )

        self.assertEqual(authenticated, self.user)
        self.assertEqual(
            self.backend.request.clmone_auth_provider,
            'microsoft_entra',
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'legal@payrollminds.example')
        self.assertEqual(self.user.first_name, 'Entra')
        self.assertEqual(self.user.last_name, 'User')

    def test_unprovisioned_inactive_or_non_oidc_membership_is_denied(self):
        unknown_claims = {
            **self.userinfo,
            'preferred_username': 'unknown@payrollminds.example',
        }
        self.assertFalse(self.backend.filter_users_by_claims(unknown_claims).exists())

        self.membership.is_active = False
        self.membership.save(update_fields=['is_active'])
        self.assertFalse(self.backend.filter_users_by_claims(self.userinfo).exists())

        self.membership.is_active = True
        self.membership.save(update_fields=['is_active'])
        self.organization.identity_provider = Organization.IdentityProvider.SAML
        self.organization.save(update_fields=['identity_provider'])
        self.assertFalse(self.backend.filter_users_by_claims(self.userinfo).exists())

    def test_workspace_outside_explicit_allowlist_is_denied(self):
        with self.settings(
            MICROSOFT_ENTRA_ORG_ALLOWLIST=['another-workspace'],
        ):
            self.assertFalse(
                self.backend.filter_users_by_claims(self.userinfo).exists()
            )

    def test_domain_allowlist_and_duplicate_identity_fail_closed(self):
        self.assertFalse(self.backend.verify_claims({
            'preferred_username': 'legal@other.example',
        }))
        duplicate = User.objects.create_user(
            username='duplicate-user',
            email='LEGAL@payrollminds.example',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=duplicate,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        with patch.object(
            self.backend,
            'get_userinfo',
            return_value=self.userinfo,
        ):
            with self.assertRaisesMessage(
                SuspiciousOperation,
                'Multiple users returned',
            ):
                self.backend.get_or_create_user(
                    'access-token',
                    'id-token',
                    self.token_claims,
                )

    def test_just_in_time_account_creation_is_refused(self):
        with self.assertRaisesMessage(
            SuspiciousOperation,
            'Microsoft Entra account is not pre-provisioned.',
        ):
            self.backend.create_user(self.userinfo)

    def test_success_audit_records_provider_without_token_or_claims(self):
        request = RequestFactory().get('/oidc/callback/')
        request.clmone_auth_provider = 'microsoft_entra'
        request.request_id = 'synthetic-request-id'

        user_logged_in.send(
            sender=type(self.user),
            request=request,
            user=self.user,
        )

        event = AuditLog.objects.get(event_type='auth.login_succeeded')
        self.assertEqual(
            event.changes['authentication_method'],
            'microsoft_entra',
        )
        evidence = str(event.changes)
        self.assertNotIn('access-token', evidence)
        self.assertNotIn('id-token', evidence)
        self.assertNotIn('synthetic-subject', evidence)


class MicrosoftEntraConfigurationTests(TestCase):
    def _settings_import(self, **overrides):
        tenant = TENANT_ID
        environment = os.environ.copy()
        for key in (
            'SSO_ENABLED',
            'MICROSOFT_ENTRA_SSO_ENABLED',
            'MICROSOFT_ENTRA_TENANT_ID',
            'MICROSOFT_ENTRA_ORG_ALLOWLIST',
            'OIDC_CREATE_USER',
            'OIDC_RP_CLIENT_ID',
            'OIDC_RP_CLIENT_SECRET',
            'OIDC_OP_DISCOVERY_ENDPOINT',
            'SSO_ALLOWED_EMAIL_DOMAINS',
        ):
            environment.pop(key, None)
        environment.update({
            'DJANGO_SECRET_KEY': 'synthetic-settings-key',
            'SSO_ENABLED': 'true',
            'MICROSOFT_ENTRA_SSO_ENABLED': 'true',
            'MICROSOFT_ENTRA_TENANT_ID': tenant,
            'MICROSOFT_ENTRA_ORG_ALLOWLIST': 'synthetic-payroll-workspace',
            'OIDC_CREATE_USER': 'false',
            'OIDC_RP_CLIENT_ID': 'synthetic-client-id',
            'OIDC_RP_CLIENT_SECRET': 'synthetic-client-secret',
            'OIDC_OP_DISCOVERY_ENDPOINT': (
                'https://login.microsoftonline.com/'
                f'{tenant}/v2.0/.well-known/openid-configuration'
            ),
            'SSO_ALLOWED_EMAIL_DOMAINS': 'payrollminds.example',
            **overrides,
        })
        return subprocess.run(
            [sys.executable, '-c', 'import config.settings_base'],
            cwd=Path(__file__).resolve().parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_tenant_specific_default_off_configuration_loads(self):
        result = self._settings_import()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_common_tenant_jit_creation_and_empty_domain_are_rejected(self):
        invalid_cases = (
            {
                'OIDC_OP_DISCOVERY_ENDPOINT': (
                    'https://login.microsoftonline.com/common/'
                    'v2.0/.well-known/openid-configuration'
                ),
            },
            {'OIDC_CREATE_USER': 'true'},
            {'SSO_ALLOWED_EMAIL_DOMAINS': ''},
            {'MICROSOFT_ENTRA_ORG_ALLOWLIST': ''},
            {'SSO_ENABLED': 'false'},
        )
        for invalid in invalid_cases:
            with self.subTest(invalid=invalid):
                result = self._settings_import(**invalid)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    'ImproperlyConfigured',
                    result.stderr,
                )


@override_settings(**ENTRA_SETTINGS)
class MicrosoftEntraActivationPreflightTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Synthetic Payroll Workspace',
            slug='synthetic-payroll-workspace',
            identity_provider=Organization.IdentityProvider.OIDC,
        )
        self.user = User.objects.create_user(
            username='synthetic-entra-user',
            email='legal@payrollminds.example',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )

    def _run(self, **overrides):
        output = StringIO()
        arguments = {
            'environment': 'synthetic-non-production',
            'workspace': self.organization.slug,
            'redirect_uri': 'https://synthetic-nonprod.example/oidc/callback/',
            'stdout': output,
            **overrides,
        }
        call_command('verify_microsoft_entra_activation', **arguments)
        return output.getvalue()

    def test_valid_preflight_is_read_only_and_does_not_disclose_secrets(self):
        before = {
            'organizations': Organization.objects.count(),
            'memberships': OrganizationMembership.objects.count(),
            'users': User.objects.count(),
        }

        output = self._run()
        report = json.loads(output.splitlines()[0])

        self.assertTrue(report['ready'])
        self.assertTrue(all(report['checks'].values()))
        self.assertEqual(
            before,
            {
                'organizations': Organization.objects.count(),
                'memberships': OrganizationMembership.objects.count(),
                'users': User.objects.count(),
            },
        )
        for sensitive_value in (
            TENANT_ID,
            'synthetic-client-id',
            'synthetic-secret',
            self.user.email,
        ):
            self.assertNotIn(sensitive_value, output)

    def test_production_environment_and_redirect_mismatch_fail_closed(self):
        for overrides in (
            {'environment': 'production'},
            {'redirect_uri': 'https://wrong.example/oidc/callback/'},
        ):
            with self.subTest(overrides=overrides):
                output = StringIO()
                with self.assertRaisesMessage(
                    CommandError,
                    'Microsoft Entra activation preflight failed.',
                ):
                    self._run(stdout=output, **overrides)
                report = json.loads(output.getvalue().splitlines()[0])
                self.assertFalse(report['ready'])

    def test_disabled_feature_and_missing_workspace_fail_closed(self):
        cases = (
            ({'MICROSOFT_ENTRA_SSO_ENABLED': False}, {}),
            ({'SSO_ENABLED': False}, {}),
            ({}, {'workspace': 'missing-synthetic-workspace'}),
        )
        for settings_overrides, command_overrides in cases:
            with self.subTest(
                settings=settings_overrides,
                command=command_overrides,
            ):
                output = StringIO()
                with self.settings(**settings_overrides):
                    with self.assertRaises(CommandError):
                        self._run(stdout=output, **command_overrides)
                report = json.loads(output.getvalue().splitlines()[0])
                self.assertFalse(report['ready'])

    def test_workspace_and_preprovisioned_identity_failures_are_deterministic(self):
        cases = (
            ('inactive_workspace', lambda: Organization.objects.filter(
                pk=self.organization.pk,
            ).update(is_active=False)),
            ('non_oidc_workspace', lambda: Organization.objects.filter(
                pk=self.organization.pk,
            ).update(identity_provider=Organization.IdentityProvider.SAML)),
            ('inactive_membership', lambda: OrganizationMembership.objects.filter(
                organization=self.organization,
            ).update(is_active=False)),
            ('wrong_domain', lambda: User.objects.filter(pk=self.user.pk).update(
                email='legal@outside.example',
            )),
        )
        for _name, mutate in cases:
            with self.subTest(case=_name):
                self.organization.is_active = True
                self.organization.identity_provider = Organization.IdentityProvider.OIDC
                self.organization.save(update_fields=['is_active', 'identity_provider'])
                self.user.email = 'legal@payrollminds.example'
                self.user.save(update_fields=['email'])
                OrganizationMembership.objects.filter(
                    organization=self.organization,
                ).update(is_active=True)
                mutate()
                with self.assertRaises(CommandError):
                    self._run()

    def test_duplicate_case_insensitive_identity_fails_closed(self):
        duplicate = User.objects.create_user(
            username='duplicate-synthetic-entra-user',
            email='LEGAL@payrollminds.example',
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=duplicate,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )

        output = StringIO()
        with self.assertRaises(CommandError):
            self._run(stdout=output)
        report = json.loads(output.getvalue().splitlines()[0])
        self.assertFalse(report['checks']['preprovisioned_identities_unique'])


class MicrosoftEntraPresentationTests(TestCase):
    def test_provider_icon_and_login_copy_are_explicit(self):
        icon = engines['django'].from_string(
            '{% include "design_system/provider_icon.html" '
            'with provider="microsoft" %}'
        ).render({})
        login_source = (
            Path(__file__).resolve().parents[1]
            / 'theme'
            / 'templates'
            / 'registration'
            / 'login.html'
        ).read_text()

        self.assertIn('data-provider-icon="microsoft"', icon)
        self.assertIn('MICROSOFT_ENTRA_SSO_ENABLED', login_source)
        self.assertIn('Continue with Microsoft', login_source)
