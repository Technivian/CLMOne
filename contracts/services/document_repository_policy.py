"""Fail-closed document repository policy for the bounded PAR-SEC-002 gate."""

from __future__ import annotations

import logging

from contracts.models import Client, Matter
from contracts.services.object_read_policy import (
    SearchEnforcementState,
    contract_repository_enforcement_state,
    filter_client_queryset,
    filter_document_queryset,
    filter_matter_queryset,
)


logger = logging.getLogger(__name__)


def document_repository_enforcement_active(organization) -> bool:
    """Return whether the bounded private-repository policy is active."""
    return (
        contract_repository_enforcement_state(organization)
        is SearchEnforcementState.ENFORCE
    )


def apply_document_repository_policy(queryset, *, organization, user, surface):
    """Apply document visibility before rows, counts, metadata, or files escape."""
    state = contract_repository_enforcement_state(organization)
    if state is SearchEnforcementState.LEGACY:
        return queryset
    if state in {
        SearchEnforcementState.FAIL_CLOSED,
        SearchEnforcementState.ABORT_FAIL_CLOSED,
    }:
        outcome = (
            'rollback_fail_closed'
            if state is SearchEnforcementState.ABORT_FAIL_CLOSED
            else 'configuration_fail_closed'
        )
        logger.warning(
            'object_read_policy outcome=%s surface=%s',
            outcome,
            surface,
        )
        return queryset.none()
    try:
        return filter_document_queryset(
            queryset,
            organization=organization,
            user=user,
            surface=surface,
        )
    except Exception:
        # Never log object identifiers, policy inputs, or exception text.
        logger.error('object_read_policy outcome=policy_error surface=%s', surface)
        return queryset.none()


def apply_document_relation_policy(queryset, *, organization, user, surface):
    """Apply the same gate to client/matter choices on document forms."""
    state = contract_repository_enforcement_state(organization)
    if state is SearchEnforcementState.LEGACY:
        return queryset
    if state in {
        SearchEnforcementState.FAIL_CLOSED,
        SearchEnforcementState.ABORT_FAIL_CLOSED,
    }:
        return queryset.none()
    try:
        if queryset.model is Client:
            return filter_client_queryset(
                queryset,
                organization=organization,
                user=user,
                surface=surface,
            )
        if queryset.model is Matter:
            return filter_matter_queryset(
                queryset,
                organization=organization,
                user=user,
                surface=surface,
            )
    except Exception:
        logger.error('object_read_policy outcome=policy_error surface=%s', surface)
        return queryset.none()
    logger.error('object_read_policy outcome=policy_error surface=%s', surface)
    return queryset.none()


def apply_related_object_read_policy(queryset, *, organization, user, surface):
    """Apply the repository read boundary to canonical Client/Matter surfaces.

    Client and Matter are relationship metadata that can disclose a private
    Contract's existence.  They therefore use the same authoritative policy
    evaluator as document form relations, rather than a view-local check.
    """
    return apply_document_relation_policy(
        queryset,
        organization=organization,
        user=user,
        surface=surface,
    )
