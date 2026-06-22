"""Authentication audit signals.

Centralizes login-success / login-failure / logout auditing for ALL auth paths
(password login, Django admin login, programmatic login) via Django's auth
signals, so no individual view needs to remember to log. SAML login keeps its
own explicit event in views_domains/saml.py.
"""
from __future__ import annotations

import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def _org_for(user):
    try:
        from contracts.tenancy import get_user_organization
        return get_user_organization(user)
    except Exception:
        return None


def _request_meta(request):
    if request is None:
        return None, '', ''
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')) or None
    if ip and ',' in ip:
        ip = ip.split(',')[0].strip()
    return ip, request.META.get('HTTP_USER_AGENT', ''), getattr(request, 'request_id', '') or ''


@receiver(user_logged_in)
def _audit_login_success(sender, request, user, **kwargs):
    from contracts.services.audit import append_audit
    ip, ua, rid = _request_meta(request)
    try:
        append_audit(
            action='LOGIN', model_name='User', organization=_org_for(user), user=user,
            object_id=getattr(user, 'id', None), object_repr=getattr(user, 'username', ''),
            event_type='auth.login_succeeded', actor_type='human', outcome='success',
            request_id=rid, ip_address=ip, user_agent=ua, changes={'event': 'auth.login_succeeded'},
        )
    except Exception:
        logger.exception('audit login_succeeded failed')


@receiver(user_logged_out)
def _audit_logout(sender, request, user, **kwargs):
    from contracts.services.audit import append_audit
    if user is None:
        return
    ip, ua, rid = _request_meta(request)
    try:
        append_audit(
            action='LOGOUT', model_name='User', organization=_org_for(user), user=user,
            object_id=getattr(user, 'id', None), object_repr=getattr(user, 'username', ''),
            event_type='auth.logout', actor_type='human', outcome='success',
            request_id=rid, ip_address=ip, user_agent=ua, changes={'event': 'auth.logout'},
        )
    except Exception:
        logger.exception('audit logout failed')


@receiver(user_login_failed)
def _audit_login_failure(sender, credentials, request=None, **kwargs):
    from contracts.services.audit import append_audit
    ip, ua, rid = _request_meta(request)
    # Never store the attempted password; record only the username attempted.
    username = ''
    if isinstance(credentials, dict):
        username = credentials.get('username') or credentials.get('email') or ''
    try:
        append_audit(
            action='LOGIN', model_name='User', organization=None, user=None,
            object_repr=str(username)[:300],
            event_type='auth.login_failed', actor_type='human', outcome='failure',
            request_id=rid, ip_address=ip, user_agent=ua,
            changes={'event': 'auth.login_failed', 'username': str(username)[:150]},
        )
    except Exception:
        logger.exception('audit login_failed failed')
