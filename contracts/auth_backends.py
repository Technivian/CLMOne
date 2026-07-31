from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import SuspiciousOperation
from django.utils.text import slugify

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from contracts.models import Organization


class CLMOneOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """Authenticate users via OIDC and map identities by email."""

    def _is_microsoft_entra(self) -> bool:
        return bool(getattr(settings, 'MICROSOFT_ENTRA_SSO_ENABLED', False))

    def _email_from_claims(self, claims):
        return (
            claims.get('email')
            or claims.get('upn')
            or claims.get('preferred_username')
            or ''
        ).strip().lower()

    def _is_allowed_email_domain(self, email: str) -> bool:
        allowed_domains = getattr(settings, 'SSO_ALLOWED_EMAIL_DOMAINS', [])
        if not allowed_domains:
            return True
        if '@' not in email:
            return False
        domain = email.split('@', 1)[1].lower()
        return domain in allowed_domains

    def verify_claims(self, claims):
        email = self._email_from_claims(claims)
        if self._is_microsoft_entra():
            return bool(email) and self._is_allowed_email_domain(email)
        return (
            super().verify_claims(claims)
            and bool(email)
            and self._is_allowed_email_domain(email)
        )

    def _entra_token_claims_are_valid(self, claims) -> bool:
        expected_tenant = str(
            getattr(settings, 'MICROSOFT_ENTRA_TENANT_ID', '') or ''
        ).strip().casefold()
        tenant = str(claims.get('tid') or '').strip().casefold()
        issuer = str(claims.get('iss') or '').strip().rstrip('/').casefold()
        expected_issuer = (
            f'https://login.microsoftonline.com/{expected_tenant}/v2.0'
        ).casefold()
        return bool(expected_tenant and tenant == expected_tenant and issuer == expected_issuer)

    def get_or_create_user(self, access_token, id_token, payload):
        if self._is_microsoft_entra() and not self._entra_token_claims_are_valid(payload):
            raise SuspiciousOperation('Microsoft Entra token policy failed.')
        user = super().get_or_create_user(access_token, id_token, payload)
        if user is not None and self._is_microsoft_entra():
            self.request.clmone_auth_provider = 'microsoft_entra'
        return user

    def filter_users_by_claims(self, claims):
        email = self._email_from_claims(claims)
        if not email:
            return self.UserModel.objects.none()
        users = self.UserModel.objects.filter(email__iexact=email)
        if self._is_microsoft_entra():
            allowlisted_orgs = getattr(
                settings,
                'MICROSOFT_ENTRA_ORG_ALLOWLIST',
                [],
            )
            users = users.filter(
                is_active=True,
                organization_memberships__is_active=True,
                organization_memberships__organization__is_active=True,
                organization_memberships__organization__slug__in=allowlisted_orgs,
                organization_memberships__organization__identity_provider=(
                    Organization.IdentityProvider.OIDC
                ),
            ).distinct()
        return users

    def create_user(self, claims):
        if self._is_microsoft_entra():
            raise SuspiciousOperation(
                'Microsoft Entra account is not pre-provisioned.'
            )
        email = self._email_from_claims(claims)
        preferred = claims.get('preferred_username') or email.split('@')[0] or 'sso-user'
        username_base = slugify(preferred)[:30] or 'sso-user'
        username = username_base

        user_model = get_user_model()
        suffix = 1
        while user_model.objects.filter(username=username).exists():
            suffix += 1
            username = f"{username_base[:24]}-{suffix}"

        user = user_model.objects.create_user(
            username=username,
            email=email,
            first_name=(claims.get('given_name') or '').strip(),
            last_name=(claims.get('family_name') or '').strip(),
        )
        user.is_active = True
        user.save(update_fields=['is_active'])
        return user

    def update_user(self, user, claims):
        email = self._email_from_claims(claims)
        if not self._is_microsoft_entra() and email and user.email != email:
            user.email = email

        given_name = (claims.get('given_name') or '').strip()
        family_name = (claims.get('family_name') or '').strip()

        if given_name:
            user.first_name = given_name
        if family_name:
            user.last_name = family_name

        update_fields = ['first_name', 'last_name']
        if not self._is_microsoft_entra():
            update_fields.insert(0, 'email')
        user.save(update_fields=update_fields)
        return user
