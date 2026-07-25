"""Default-off, content-free observation for PAR-SEC-002 characterization.

This module deliberately does not decide access, filter a queryset, persist an
event, or expose a counter.  When enabled in a controlled observation setting,
it records only an aggregate route and actor-class counter in process memory
and emits the same two fields to the application logger.  It is not an audit
log, policy engine, or authorization control.
"""

from __future__ import annotations

from collections import Counter
import logging

from django.conf import settings

from contracts.permissions import can_manage_organization

logger = logging.getLogger(__name__)

_counters: Counter[tuple[str, str]] = Counter()


def observe_request(surface: str, user, organization) -> None:
    """Record a content-free route counter only when the committed flag is on."""
    if not getattr(settings, 'PAR_SEC_002_OBSERVATION_ENABLED', False):
        return

    if organization is None:
        actor_class = 'no_workspace'
    elif can_manage_organization(user, organization):
        actor_class = 'manager'
    else:
        actor_class = 'member'

    _counters[(surface, actor_class)] += 1
    logger.info('par_sec_002_observation surface=%s actor_class=%s', surface, actor_class)


def observation_counters() -> dict[tuple[str, str], int]:
    """Return a test/operator-process snapshot without exposing it over HTTP."""
    return dict(_counters)


def reset_observation_counters() -> None:
    """Reset process-local counters for deterministic tests and controlled drills."""
    _counters.clear()
