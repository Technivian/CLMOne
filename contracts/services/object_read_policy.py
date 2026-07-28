"""Reusable object-read policy boundary for the PAR-SEC-002 search slice."""

from __future__ import annotations

import logging
from enum import Enum

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone

from contracts.models import Contract, EthicalWall, OrganizationMembership


logger = logging.getLogger(__name__)


class SearchEnforcementState(str, Enum):
    LEGACY = 'legacy'
    ENFORCE = 'enforce'
    FAIL_CLOSED = 'fail_closed'
    ABORT_FAIL_CLOSED = 'abort_fail_closed'


class ObjectReadPolicyUnavailable(RuntimeError):
    """Raised when eligibility cannot be evaluated safely."""


def _configured_values(setting_name: str) -> set[str]:
    raw = getattr(settings, setting_name, '') or ''
    if isinstance(raw, str):
        values = raw.split(',')
    else:
        values = raw
    return {str(value).strip().casefold() for value in values if str(value).strip()}


def contract_search_enforcement_state(organization) -> SearchEnforcementState:
    """Resolve the reversible gate without broadening its configured scope."""
    enforcement_enabled = getattr(
        settings,
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED',
        False,
    )
    abort_fail_closed = getattr(
        settings,
        'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED',
        False,
    )
    if not enforcement_enabled and not abort_fail_closed:
        return SearchEnforcementState.LEGACY
    if organization is None:
        return SearchEnforcementState.FAIL_CLOSED

    allowlisted_orgs = _configured_values(
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST'
    )
    if str(organization.slug).casefold() not in allowlisted_orgs:
        return SearchEnforcementState.LEGACY
    if abort_fail_closed:
        return SearchEnforcementState.ABORT_FAIL_CLOSED
    if not enforcement_enabled:
        return SearchEnforcementState.LEGACY

    environment = str(getattr(settings, 'DJANGO_ENV', '') or '').strip().casefold()
    allowlisted_environments = _configured_values(
        'PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS'
    )
    if environment == 'production' or environment not in allowlisted_environments:
        return SearchEnforcementState.FAIL_CLOSED
    return SearchEnforcementState.ENFORCE


def filter_contract_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
) -> QuerySet:
    """Return only contracts eligible for this requester under Ethical Walls."""
    if queryset.model is not Contract or organization is None:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    if not user or not getattr(user, 'is_authenticated', False) or not user.is_active:
        raise ObjectReadPolicyUnavailable('Requester membership cannot be established.')
    if not OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
        organization__is_active=True,
    ).exists():
        raise ObjectReadPolicyUnavailable('Requester membership cannot be established.')

    now = timezone.now()
    active_walls = EthicalWall.objects.filter(
        organization=organization,
        is_active=True,
    ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))

    wall_rows = list(
        active_walls.values(
            'id',
            'client_id',
            'client__organization_id',
            'matter_id',
            'matter__organization_id',
            'matter__client__organization_id',
        )
    )
    restricted_wall_ids = set(
        active_walls.filter(restricted_users=user).values_list('id', flat=True)
    )
    restricted_client_ids: set[int] = set()
    restricted_matter_ids: set[int] = set()
    for wall in wall_rows:
        if wall['client_id'] is None and wall['matter_id'] is None:
            raise ObjectReadPolicyUnavailable('Ethical Wall configuration is not evaluable.')
        if (
            wall['client_id'] is not None
            and wall['client__organization_id'] != organization.pk
        ):
            raise ObjectReadPolicyUnavailable('Ethical Wall configuration is not evaluable.')
        if wall['matter_id'] is not None and (
            wall['matter__organization_id'] != organization.pk
            or wall['matter__client__organization_id'] != organization.pk
        ):
            raise ObjectReadPolicyUnavailable('Ethical Wall configuration is not evaluable.')
        if wall['id'] not in restricted_wall_ids:
            continue
        if wall['client_id'] is not None:
            restricted_client_ids.add(wall['client_id'])
        if wall['matter_id'] is not None:
            restricted_matter_ids.add(wall['matter_id'])

    eligible = queryset.filter(organization=organization)
    eligible = eligible.filter(
        Q(client__isnull=True) | Q(client__organization=organization),
        Q(matter__isnull=True)
        | Q(
            matter__organization=organization,
            matter__client__organization=organization,
        ),
    )
    if restricted_client_ids or restricted_matter_ids:
        eligible = eligible.exclude(
            Q(client_id__in=restricted_client_ids)
            | Q(matter_id__in=restricted_matter_ids)
            | Q(matter__client_id__in=restricted_client_ids)
        )
        logger.info('object_read_policy outcome=deny surface=contract_search')
    else:
        logger.info('object_read_policy outcome=allow surface=contract_search')
    return eligible.distinct()
