import logging
import secrets
import time
import traceback
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse

from .logging_context import (
    request_id_var,
    request_org_id_var,
    request_path_var,
    request_user_id_var,
)
from .models import UserProfile
from .session_security import current_session_timestamp
from .models import AuditLog
from .observability import record_request_metric
from .tenancy import get_user_organization

logger = logging.getLogger(__name__)


class PreviewExceptionMiddleware:
    """Surface verbose errors **only in DEBUG/preview**; never leak in production.

    Audit finding B4: this middleware previously returned a full Python
    traceback to any client on any unhandled 500, defeating ``DEBUG=False``.
    It now emits the verbose body only when ``settings.DEBUG`` is on (local
    dev / preview). In production it logs server-side and re-raises so Django's
    standard handler500 renders the branded, information-free 500 page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as exc:
            logger.exception('request_failed', extra={'path': request.path, 'method': request.method})
            if settings.DEBUG:
                return HttpResponse(
                    'Preview request failed:\n\n'
                    f'{exc.__class__.__name__}: {exc}\n\n'
                    f'{traceback.format_exc()}',
                    status=500,
                    content_type='text/plain',
                )
            # Production: do not disclose internals. Let Django render handler500.
            raise


class SecurityHeadersMiddleware:
    """Apply baseline security headers consistently across responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Per-request CSP nonce. Set before get_response so templates can stamp
        # inline <script>/<style> via the csp_nonce context processor.
        request.csp_nonce = secrets.token_urlsafe(16)
        response = self.get_response(request)
        if not getattr(settings, 'SECURITY_HEADERS_ENABLED', True):
            return response

        response.setdefault('X-Content-Type-Options', 'nosniff')
        response.setdefault('Referrer-Policy', getattr(settings, 'SECURE_REFERRER_POLICY', 'same-origin'))
        response.setdefault('Permissions-Policy', getattr(settings, 'PERMISSIONS_POLICY', 'geolocation=(), microphone=(), camera=()'))
        policy = getattr(settings, 'CONTENT_SECURITY_POLICY', "default-src 'self'")
        response.setdefault('Content-Security-Policy', policy.replace('{nonce}', request.csp_nonce))
        return response


class AuthRateLimitMiddleware:
    """
    Simple per-IP request throttling for auth-sensitive endpoints.

    This is intentionally lightweight and works without external dependencies.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if not getattr(settings, 'RATELIMIT_ENABLED', True):
                return self.get_response(request)

            path = request.path
            client_ip = self._client_ip(request)
            trusted = client_ip in getattr(settings, 'RATELIMIT_TRUSTED_IPS', ())

            # Token-authenticated API/SCIM surfaces: throttle repeated auth
            # FAILURES per IP, leaving legitimate authenticated traffic alone.
            api_prefix = self._matched_api_prefix(path)
            if api_prefix and not trusted:
                return self._handle_api_request(request, api_prefix, client_ip)

            if path not in getattr(settings, 'RATELIMIT_PATHS', ('/login/', '/register/')):
                return self.get_response(request)

            if request.method not in {'POST'}:
                return self.get_response(request)

            if trusted:
                return self.get_response(request)

            limit, window = self._policy_for_path(path)
            key = f'auth-rl:{path}:{client_ip}'
            now = int(time.time())
            bucket = cache.get(key)

            if not bucket or not isinstance(bucket, dict) or now >= bucket.get('reset_at', 0):
                bucket = {'count': 0, 'reset_at': now + window}

            if bucket['count'] >= limit:
                retry_after = max(bucket['reset_at'] - now, 1)
                response = HttpResponse('Too many requests. Please try again later.', status=429)
                response['Retry-After'] = str(retry_after)
                return response

            bucket['count'] += 1
            cache.set(key, bucket, timeout=window)
            return self.get_response(request)
        except Exception as exc:
            logger.exception('auth_rate_limit_cache_failure', extra={'path': request.path, 'client_ip': self._client_ip(request)})
            if settings.DEBUG:
                return HttpResponse(
                    f'Auth rate limit error: {exc.__class__.__name__}: {exc}',
                    status=503,
                    content_type='text/plain',
                )
            # Production: cache backend is unavailable. Fail closed on auth
            # endpoints rather than disclose internals or silently stop
            # throttling (audit C10). Generic, information-free response.
            return HttpResponse('Service temporarily unavailable.', status=503, content_type='text/plain')

    @staticmethod
    def _client_ip(request):
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '') or 'unknown'

    @staticmethod
    def _policy_for_path(path):
        if path == '/register/':
            return (
                int(getattr(settings, 'REGISTER_RATE_LIMIT_REQUESTS', 10)),
                int(getattr(settings, 'REGISTER_RATE_LIMIT_WINDOW_SECONDS', 300)),
            )
        return (
            int(getattr(settings, 'LOGIN_RATE_LIMIT_REQUESTS', 10)),
            int(getattr(settings, 'LOGIN_RATE_LIMIT_WINDOW_SECONDS', 300)),
        )

    @staticmethod
    def _matched_api_prefix(path):
        for prefix in getattr(settings, 'API_RATELIMIT_PREFIXES', ()):
            if path.startswith(prefix):
                return prefix
        return None

    def _handle_api_request(self, request, prefix, client_ip):
        limit = int(getattr(settings, 'API_AUTH_FAIL_LIMIT', 20))
        window = int(getattr(settings, 'API_AUTH_FAIL_WINDOW_SECONDS', 300))
        key = f'api-authfail-rl:{prefix}:{client_ip}'
        now = int(time.time())
        bucket = cache.get(key)
        if not bucket or not isinstance(bucket, dict) or now >= bucket.get('reset_at', 0):
            bucket = {'count': 0, 'reset_at': now + window}

        # Block once too many recent auth failures have accumulated.
        if bucket['count'] >= limit:
            retry_after = max(bucket['reset_at'] - now, 1)
            response = HttpResponse('Too many failed authentication attempts.', status=429)
            response['Retry-After'] = str(retry_after)
            return response

        response = self.get_response(request)

        # Count only auth failures, so authenticated clients are never throttled.
        if response.status_code in (401, 403):
            bucket['count'] += 1
            cache.set(key, bucket, timeout=max(bucket['reset_at'] - now, 1))
        return response


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and getattr(user, 'is_authenticated', False):
            preferred_org_id = request.session.get('active_organization_id')
            if preferred_org_id:
                user._active_organization_id = preferred_org_id
            organization = get_user_organization(user)
            request.organization = organization
            if organization and request.session.get('active_organization_id') != organization.id:
                request.session['active_organization_id'] = organization.id
        else:
            request.organization = None
        return self.get_response(request)


class SessionSecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return self.get_response(request)

        mfa_redirect = self._mfa_gate_redirect(request)
        if mfa_redirect is not None:
            return mfa_redirect

        session = request.session
        profile, _ = UserProfile.objects.get_or_create(user=user)

        current_revocation_counter = profile.session_revocation_counter
        session_revocation_counter = session.get('session_revocation_counter')
        if session_revocation_counter is None:
            session['session_revocation_counter'] = current_revocation_counter
            session_revocation_counter = current_revocation_counter
        elif session_revocation_counter != current_revocation_counter:
            session.flush()
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")

        organization = getattr(request, 'organization', None) or get_user_organization(user)
        idle_timeout_minutes = int(
            getattr(organization, 'session_idle_timeout_minutes', None)
            or getattr(settings, 'SESSION_IDLE_TIMEOUT_MINUTES', 120)
        )
        now_ts = current_session_timestamp()
        last_activity = session.get('session_last_activity_at')
        if last_activity is not None:
            try:
                last_activity = int(last_activity)
            except (TypeError, ValueError):
                last_activity = None
        if last_activity is not None and now_ts - last_activity > idle_timeout_minutes * 60:
            session.flush()
            return redirect(f"{settings.LOGIN_URL}?next={request.get_full_path()}")

        session['session_last_activity_at'] = now_ts

        return self.get_response(request)

    # Paths that must stay reachable so a user can complete (or escape) the MFA
    # flow without a redirect loop: auth pages, the MFA pages themselves, and
    # account/admin management. Static/media are served outside this middleware.
    _MFA_EXEMPT_PREFIXES = (
        '/login/', '/logout/', '/register/', '/mfa/',
        '/profile/', '/settings/', '/admin/',
    )

    @classmethod
    def _is_exempt_path(cls, path):
        return any(path.startswith(prefix) for prefix in cls._MFA_EXEMPT_PREFIXES)

    def _mfa_gate_redirect(self, request):
        """Fail-closed MFA gate applied to EVERY non-exempt authenticated view.

        Enforcement lives here (not only in MfaRequiredMixin) so a view that
        forgets the mixin cannot become an MFA bypass. Returns a redirect
        response when the user must satisfy MFA first, else None.
        """
        if self._is_exempt_path(request.path):
            return None
        from contracts.services.mfa_policy import organization_requires_mfa
        organization = getattr(request, 'organization', None) or get_user_organization(request.user)
        if not organization_requires_mfa(organization):
            return None
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        if not profile.mfa_enabled or profile.mfa_verified_at is None:
            return redirect('mfa_enroll')
        if not request.session.get('mfa_verified'):
            return redirect(f"{reverse('mfa_challenge')}?next={request.get_full_path()}")
        return None
class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        request_id = request.META.get('HTTP_X_REQUEST_ID') or str(uuid4())
        request.request_id = request_id
        user = getattr(request, 'user', None)
        organization = getattr(request, 'organization', None)

        request_id_token = request_id_var.set(request_id)
        request_path_token = request_path_var.set(getattr(request, 'path', '-'))
        user_token = request_user_id_var.set(str(user.id) if getattr(user, 'is_authenticated', False) else '-')
        org_token = request_org_id_var.set(str(organization.id) if organization else '-')

        try:
            response = self.get_response(request)
            latency_ms = (time.perf_counter() - started) * 1000
            record_request_metric(request.path, response.status_code, latency_ms)

            response['X-Request-ID'] = request_id
            logger.info(
                'request_completed',
                extra={
                    'method': request.method,
                    'path': request.path,
                    'status_code': response.status_code,
                    'latency_ms': round(latency_ms, 2),
                },
            )
            return response
        finally:
            request_id_var.reset(request_id_token)
            request_path_var.reset(request_path_token)
            request_user_id_var.reset(user_token)
            request_org_id_var.reset(org_token)


def log_action(
    user, action, model_name, object_id=None, object_repr='', changes=None, request=None,
    *, organization=None, organization_id=None, event_type=None, actor_type=None,
    outcome=None, job_run_id=None,
):
    """Canonical audit entry point — appends to the per-org tamper-evident chain.

    Backward compatible: existing callers pass (user, action, model_name, ...).
    Organization is resolved from the explicit arg, then request.organization,
    then a legacy ``changes['organization_id']``. Audit failures are logged and
    swallowed so a logging fault never breaks the business action; the append
    itself runs in its own savepoint so it cannot poison the caller's
    transaction.
    """
    from contracts.services.audit import append_audit

    ip_address = None
    user_agent = ''
    request_id = ''
    if request:
        ip_address = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        request_id = getattr(request, 'request_id', '') or ''
        if organization is None and organization_id is None:
            organization = getattr(request, 'organization', None)

    if organization is None and organization_id is None and isinstance(changes, dict):
        organization_id = changes.get('organization_id')

    try:
        return append_audit(
            action=action,
            model_name=model_name,
            organization=organization,
            organization_id=organization_id,
            user=user,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes,
            event_type=event_type,
            actor_type=actor_type,
            outcome=outcome or AuditLog.Outcome.SUCCESS,
            request_id=request_id,
            job_run_id=job_run_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except Exception:
        logger.exception('audit append failed action=%s model=%s', action, model_name)
        return None
