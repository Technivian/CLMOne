"""Reusable object-read policy boundary for PAR-SEC-002 contract surfaces."""

from __future__ import annotations

import logging
from enum import Enum

from django.conf import settings
from django.db.models import Q, QuerySet
from django.utils import timezone

from contracts.models import (
    Client,
    Contract,
    Document,
    DocumentVersion,
    EthicalWall,
    LegalTask,
    Matter,
    OrganizationMembership,
    Workflow,
    WorkflowInstance,
)


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


def _contract_enforcement_state(
    organization,
    *,
    enabled_setting: str,
    abort_setting: str,
    environments_setting: str,
    org_allowlist_setting: str,
) -> SearchEnforcementState:
    """Resolve a reversible, environment/workspace-bounded enforcement gate."""
    enforcement_enabled = getattr(
        settings,
        enabled_setting,
        False,
    )
    abort_fail_closed = getattr(
        settings,
        abort_setting,
        False,
    )
    if not enforcement_enabled and not abort_fail_closed:
        return SearchEnforcementState.LEGACY
    if organization is None:
        return SearchEnforcementState.FAIL_CLOSED

    allowlisted_orgs = _configured_values(org_allowlist_setting)
    if str(organization.slug).casefold() not in allowlisted_orgs:
        return SearchEnforcementState.LEGACY
    if abort_fail_closed:
        return SearchEnforcementState.ABORT_FAIL_CLOSED
    if not enforcement_enabled:
        return SearchEnforcementState.LEGACY

    environment = str(getattr(settings, 'DJANGO_ENV', '') or '').strip().casefold()
    allowlisted_environments = _configured_values(environments_setting)
    if environment == 'production' or environment not in allowlisted_environments:
        return SearchEnforcementState.FAIL_CLOSED
    return SearchEnforcementState.ENFORCE


def contract_search_enforcement_state(organization) -> SearchEnforcementState:
    """Resolve the existing search/facet gate without broadening its scope."""
    return _contract_enforcement_state(
        organization,
        enabled_setting='PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED',
        abort_setting='PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED',
        environments_setting='PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS',
        org_allowlist_setting='PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST',
    )


def contract_repository_enforcement_state(organization) -> SearchEnforcementState:
    """Resolve the separate repository/read-path enforcement gate."""
    return _contract_enforcement_state(
        organization,
        enabled_setting='PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED',
        abort_setting='PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED',
        environments_setting='PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS',
        org_allowlist_setting='PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST',
    )


def _restricted_scope_ids(*, organization, user) -> tuple[set[int], set[int]]:
    """Validate the requester and return client/matter scopes denied by active walls."""
    if organization is None:
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

    return restricted_client_ids, restricted_matter_ids


def is_workspace_privileged_editor(*, organization, user) -> bool:
    """Return whether a member has the existing all-record EDIT authority.

    PDR-0008 preserves OWNER/ADMIN edit authority.  It does *not* approve an
    OWNER/ADMIN supervisory read, comment, AI, or export override, so callers
    must never use this predicate for object discovery.
    """
    return OrganizationMembership.objects.filter(
        organization=organization,
        user=user,
        is_active=True,
        organization__is_active=True,
        role__in=[
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
        ],
    ).exists()


def _apply_private_contract_read_access(queryset: QuerySet, *, user) -> QuerySet:
    """Apply the approved owner/creator read boundary at queryset level.

    This is the one canonical private-by-default rule.  OWNER/ADMIN are not
    included here because supervisory read/export requires a separate Product
    and Security approval that PDR-0008 does not supply.
    """
    return queryset.filter(Q(owner=user) | Q(created_by=user))


def filter_contract_security_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'contract_search',
) -> QuerySet:
    """Apply membership, tenant, relation, and Ethical-Wall security checks.

    This helper intentionally does not apply owner/creator visibility. It is
    used only for the separately approved OWNER/ADMIN all-record EDIT action;
    it is never a discovery queryset.
    """
    if queryset.model is not Contract:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    restricted_client_ids, restricted_matter_ids = _restricted_scope_ids(
        organization=organization,
        user=user,
    )

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
        logger.info('object_read_policy outcome=deny surface=%s', surface)
    else:
        logger.info('object_read_policy outcome=allow surface=%s', surface)
    return eligible.distinct()


def filter_contract_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'contract_search',
) -> QuerySet:
    """Return only contracts eligible for canonical private-by-default read."""
    eligible = filter_contract_security_queryset(
        queryset,
        organization=organization,
        user=user,
        surface=surface,
    )
    return _apply_private_contract_read_access(eligible, user=user).distinct()


def filter_contract_edit_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'contract_edit',
) -> QuerySet:
    """Return records the actor may resolve for a mutation endpoint.

    Discovery stays private-by-default.  This narrowly preserves the approved
    existing OWNER/ADMIN all-record *edit* authority after tenant and
    Ethical-Wall checks; it must never be used by list, search, count, export,
    or detail-read paths.
    """
    eligible = filter_contract_security_queryset(
        queryset,
        organization=organization,
        user=user,
        surface=surface,
    )
    if is_workspace_privileged_editor(organization=organization, user=user):
        return eligible
    return _apply_private_contract_read_access(eligible, user=user).distinct()


def filter_document_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'document_repository',
) -> QuerySet:
    """Return documents the requester may discover or open.

    Document visibility inherits active Ethical Walls from every canonical
    relationship that can carry a client or matter.  Relationally inconsistent
    cross-workspace references are excluded even when the document row itself
    carries the requester's organization.
    """
    if queryset.model is not Document:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    restricted_client_ids, restricted_matter_ids = _restricted_scope_ids(
        organization=organization,
        user=user,
    )
    eligible_contracts = Contract.objects.filter(organization=organization).filter(
        Q(client__isnull=True) | Q(client__organization=organization),
        Q(matter__isnull=True)
        | Q(
            matter__organization=organization,
            matter__client__organization=organization,
        ),
    )
    if restricted_client_ids or restricted_matter_ids:
        eligible_contracts = eligible_contracts.exclude(
            Q(client_id__in=restricted_client_ids)
            | Q(matter_id__in=restricted_matter_ids)
            | Q(matter__client_id__in=restricted_client_ids)
        )
    eligible_contracts = _apply_private_contract_read_access(
        eligible_contracts,
        user=user,
    )
    eligible_contract_ids = eligible_contracts.values('pk')

    eligible = queryset.filter(
        organization=organization,
        is_deleted=False,
    ).filter(
        Q(client__isnull=True) | Q(client__organization=organization),
        Q(matter__isnull=True)
        | Q(
            matter__organization=organization,
            matter__client__organization=organization,
        ),
        Q(contract__isnull=True) | Q(contract_id__in=eligible_contract_ids),
    )
    if restricted_client_ids or restricted_matter_ids:
        eligible = eligible.exclude(
            Q(client_id__in=restricted_client_ids)
            | Q(matter_id__in=restricted_matter_ids)
            | Q(matter__client_id__in=restricted_client_ids)
        )
        logger.info('object_read_policy outcome=deny surface=%s', surface)
    else:
        logger.info('object_read_policy outcome=allow surface=%s', surface)
    return eligible.filter(
        Q(contract_id__in=eligible_contract_ids) | Q(contract__isnull=True, uploaded_by=user)
    ).distinct()


def filter_client_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'document_client_options',
) -> QuerySet:
    """Filter client choices used by secured document repository forms."""
    if queryset.model is not Client:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    restricted_client_ids, _ = _restricted_scope_ids(
        organization=organization,
        user=user,
    )
    eligible = queryset.filter(organization=organization)
    if restricted_client_ids:
        eligible = eligible.exclude(pk__in=restricted_client_ids)
        logger.info('object_read_policy outcome=deny surface=%s', surface)
    else:
        logger.info('object_read_policy outcome=allow surface=%s', surface)
    eligible_contracts = _apply_private_contract_read_access(
        Contract.objects.filter(organization=organization),
        user=user,
    )
    # A Client is a relation-derived metadata surface. Do not disclose it
    # merely because a private contract points at it; standalone documents
    # remain visible only to their uploader.
    eligible = eligible.filter(
        Q(contracts__isnull=True)
        | Q(contracts__in=eligible_contracts)
        | Q(documents__uploaded_by=user)
    )
    return eligible.distinct()


def filter_matter_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'document_matter_options',
) -> QuerySet:
    """Filter matter choices used by secured document repository forms."""
    if queryset.model is not Matter:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    restricted_client_ids, restricted_matter_ids = _restricted_scope_ids(
        organization=organization,
        user=user,
    )
    eligible = queryset.filter(
        organization=organization,
        client__organization=organization,
    )
    if restricted_client_ids or restricted_matter_ids:
        eligible = eligible.exclude(
            Q(pk__in=restricted_matter_ids)
            | Q(client_id__in=restricted_client_ids)
        )
        logger.info('object_read_policy outcome=deny surface=%s', surface)
    else:
        logger.info('object_read_policy outcome=allow surface=%s', surface)
    eligible_contracts = _apply_private_contract_read_access(
        Contract.objects.filter(organization=organization),
        user=user,
    )
    eligible = eligible.filter(
        Q(contracts__isnull=True) | Q(contracts__in=eligible_contracts)
    )
    return eligible.distinct()


def filter_document_version_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'document_version',
) -> QuerySet:
    """Return immutable document versions only when their document is visible."""
    if queryset.model is not DocumentVersion:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    documents = filter_document_queryset(
        Document.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(
        organization=organization,
        document_row_id__in=documents.values('pk'),
    ).distinct()


def filter_workflow_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'workflow',
) -> QuerySet:
    """Filter workflow rows through the linked Contract read boundary.

    An unlinked workflow has no contract metadata to inherit, so only its
    creator may discover it. This is conservative and keeps it from becoming
    a side channel for a future linked contract.
    """
    if queryset.model is not Workflow:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    contracts = filter_contract_queryset(
        Contract.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(organization=organization).filter(
        Q(contract_id__in=contracts.values('pk'))
        | Q(contract__isnull=True, created_by=user)
    ).distinct()


def filter_workflow_edit_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'workflow_edit',
) -> QuerySet:
    """Resolve workflows for a permitted mutation, never for discovery."""
    if queryset.model is not Workflow:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    contracts = filter_contract_edit_queryset(
        Contract.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(organization=organization).filter(
        Q(contract_id__in=contracts.values('pk'))
        | Q(contract__isnull=True, created_by=user)
    ).distinct()


def filter_workflow_instance_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'workflow_instance',
) -> QuerySet:
    """Filter canonical workflow instances through their one contract."""
    if queryset.model is not WorkflowInstance:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    contracts = filter_contract_queryset(
        Contract.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(
        organization=organization,
        contract_id__in=contracts.values('pk'),
    ).distinct()


def filter_legal_task_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'work_item',
) -> QuerySet:
    """Filter contract-linked work items through the canonical contract rule."""
    if queryset.model is not LegalTask:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    contracts = filter_contract_queryset(
        Contract.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(
        Q(contract_id__in=contracts.values('pk'))
        # Matter-only tasks have no Contract to inherit. Retain their
        # established tenant/matter boundary; they are not a contract-record
        # discovery path.
        | Q(contract__isnull=True, matter__organization=organization)
        | Q(contract__isnull=True, matter__isnull=True, assigned_to=user)
    ).distinct()


def filter_legal_task_edit_queryset(
    queryset: QuerySet,
    *,
    organization,
    user,
    surface: str = 'work_item_edit',
) -> QuerySet:
    """Resolve task rows for a permitted mutation, never for a queue/list."""
    if queryset.model is not LegalTask:
        raise ObjectReadPolicyUnavailable('Unsupported object policy input.')
    contracts = filter_contract_edit_queryset(
        Contract.objects.filter(organization=organization),
        organization=organization,
        user=user,
        surface=surface,
    )
    return queryset.filter(
        Q(contract_id__in=contracts.values('pk'))
        | Q(contract__isnull=True, matter__organization=organization)
        | Q(contract__isnull=True, matter__isnull=True, assigned_to=user)
    ).distinct()
