import json
import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from contracts.models import Organization, OrganizationMembership


PRODUCTION_ENVIRONMENT_NAMES = {'prod', 'production', 'live'}


class Command(BaseCommand):
    help = (
        'Perform a read-only, secret-safe Microsoft Entra activation preflight '
        'for one named non-production workspace.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--environment', required=True)
        parser.add_argument('--workspace', required=True)
        parser.add_argument('--redirect-uri', required=True)

    @staticmethod
    def _normalized_tenant_id():
        try:
            return str(uuid.UUID(str(settings.MICROSOFT_ENTRA_TENANT_ID)))
        except (ValueError, TypeError, AttributeError):
            return ''

    def handle(self, *args, **options):
        environment = options['environment'].strip().casefold()
        workspace_slug = options['workspace'].strip()
        redirect_uri = options['redirect_uri'].strip()
        app_base_url = str(getattr(settings, 'APP_BASE_URL', '')).rstrip('/')
        parsed_app_base_url = urlparse(app_base_url)
        tenant_id = self._normalized_tenant_id()
        expected_discovery = (
            f'https://login.microsoftonline.com/{tenant_id}/v2.0/'
            '.well-known/openid-configuration'
            if tenant_id
            else ''
        )
        expected_redirect = f'{app_base_url}/oidc/callback/'

        workspace = Organization.objects.filter(slug=workspace_slug).first()
        candidate_memberships = []
        if workspace is not None:
            candidate_memberships = list(
                OrganizationMembership.objects.filter(
                    organization=workspace,
                    is_active=True,
                    user__is_active=True,
                ).select_related('user')
            )

        allowed_domains = {
            str(domain).strip().casefold()
            for domain in getattr(settings, 'SSO_ALLOWED_EMAIL_DOMAINS', [])
            if str(domain).strip()
        }
        candidate_emails = [
            membership.user.email.strip().casefold()
            for membership in candidate_memberships
        ]
        candidate_domains_allowed = bool(candidate_emails) and all(
            '@' in email and email.rsplit('@', 1)[1] in allowed_domains
            for email in candidate_emails
        )
        candidate_emails_unique = (
            bool(candidate_emails)
            and len(candidate_emails) == len(set(candidate_emails))
        )

        checks = {
            'app_base_url_is_https_origin': (
                parsed_app_base_url.scheme == 'https'
                and bool(parsed_app_base_url.netloc)
                and not parsed_app_base_url.username
                and not parsed_app_base_url.password
                and not parsed_app_base_url.path
                and not parsed_app_base_url.query
                and not parsed_app_base_url.fragment
            ),
            'client_id_configured': bool(
                str(getattr(settings, 'OIDC_RP_CLIENT_ID', '')).strip()
            ),
            'client_secret_configured': bool(
                str(getattr(settings, 'OIDC_RP_CLIENT_SECRET', '')).strip()
            ),
            'discovery_endpoint_exact': bool(tenant_id) and (
                str(getattr(settings, 'OIDC_OP_DISCOVERY_ENDPOINT', '')).rstrip('/')
                == expected_discovery
            ),
            'email_domains_allowlisted': bool(allowed_domains),
            'environment_non_production': bool(environment) and (
                environment not in PRODUCTION_ENVIRONMENT_NAMES
            ),
            'jit_creation_disabled': not bool(
                getattr(settings, 'OIDC_CREATE_USER', True)
            ),
            'microsoft_entra_enabled': bool(
                getattr(settings, 'MICROSOFT_ENTRA_SSO_ENABLED', False)
            ),
            'oidc_ssl_verification_enabled': bool(
                getattr(settings, 'OIDC_VERIFY_SSL', False)
            ),
            'oidc_access_token_storage_disabled': not bool(
                getattr(settings, 'OIDC_STORE_ACCESS_TOKEN', True)
            ),
            'oidc_nonce_enabled': bool(getattr(settings, 'OIDC_USE_NONCE', False)),
            'oidc_signing_algorithm_rs256': (
                getattr(settings, 'OIDC_RP_SIGN_ALGO', '') == 'RS256'
            ),
            'oidc_scopes_minimized': set(
                str(getattr(settings, 'OIDC_RP_SCOPES', '')).split()
            ) == {'openid', 'email', 'profile'},
            'preprovisioned_identity_domains_allowed': candidate_domains_allowed,
            'preprovisioned_identities_present': bool(candidate_memberships),
            'preprovisioned_identities_unique': candidate_emails_unique,
            'redirect_uri_exact': bool(expected_redirect) and (
                redirect_uri == expected_redirect
            ),
            'sso_enabled': bool(getattr(settings, 'SSO_ENABLED', False)),
            'tenant_id_is_uuid': bool(tenant_id),
            'workspace_active': bool(workspace and workspace.is_active),
            'workspace_allowlisted': workspace_slug in set(
                getattr(settings, 'MICROSOFT_ENTRA_ORG_ALLOWLIST', [])
            ),
            'workspace_uses_oidc': bool(
                workspace
                and workspace.identity_provider == Organization.IdentityProvider.OIDC
            ),
        }
        report = {
            'checks': checks,
            'ready': all(checks.values()),
        }
        self.stdout.write(json.dumps(report, sort_keys=True))

        if not report['ready']:
            raise CommandError('Microsoft Entra activation preflight failed.')

        self.stdout.write(
            self.style.SUCCESS('Microsoft Entra activation preflight passed.')
        )
