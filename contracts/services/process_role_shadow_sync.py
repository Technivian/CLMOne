"""PAR-ID-001 Slice 3 — feature-flagged shadow sync of UserProfile.role → ProcessRoleAssignment.

Legacy UserProfile.role remains authoritative. ProcessRoleAssignment is never used
for permissions, approval, signer, or workflow routing in this slice.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from contracts.services.process_role_assignment import (
    EVENT_ASSIGNMENT_CREATED,
    EVENT_ASSIGNMENT_DEACTIVATED,
    EVENT_ASSIGNMENT_LEGACY_MAPPED,
    create_process_role_assignment,
    resolve_legacy_process_role_code,
)
from contracts.services.role_definition import ensure_canonical_role_definitions

logger = logging.getLogger(__name__)

EVENT_ASSIGNMENT_SHADOW_SYNC_FAILED = 'role.assignment.shadow_sync_failed'
SHADOW_REASON = 'process_role_shadow_sync'
LEGACY_FIELD = 'profile_role'


def shadow_write_enabled() -> bool:
    return bool(getattr(settings, 'PROCESS_ROLE_SHADOW_WRITE_ENABLED', False))


def parity_reporting_enabled() -> bool:
    return bool(getattr(settings, 'PROCESS_ROLE_PARITY_REPORTING_ENABLED', False))


def _audit_shadow_failure(*, organization, user, legacy_value, error, correlation_id, actor=None) -> None:
    try:
        from contracts.middleware import log_action
        from contracts.models import AuditLog

        log_action(
            actor if getattr(actor, 'is_authenticated', False) else None,
            AuditLog.Action.UPDATE,
            'ProcessRoleAssignment',
            object_id=None,
            object_repr=f'shadow_sync_failed user={getattr(user, "pk", None)}',
            organization=organization,
            event_type=EVENT_ASSIGNMENT_SHADOW_SYNC_FAILED,
            changes={
                'legacy_source_field': LEGACY_FIELD,
                'legacy_source_value': legacy_value,
                'user_id': getattr(user, 'pk', None),
                'error': str(error)[:500],
                'correlation_id': str(correlation_id),
                'reason': SHADOW_REASON,
            },
        )
    except Exception:
        logger.exception('failed to audit shadow sync failure')


def shadow_sync_profile_role_for_organization(
    *,
    organization,
    user,
    profile_role: str,
    actor=None,
    correlation_id=None,
) -> dict[str, Any]:
    """Idempotently mirror a profile process-role into one org's ProcessRoleAssignment rows.

    Does not modify UserProfile.role. Does not touch OrganizationMembership.role.
    """
    from contracts.models import OrganizationMembership, ProcessRoleAssignment, RoleDefinition

    correlation_id = correlation_id or uuid.uuid4()
    membership = OrganizationMembership.objects.filter(
        organization=organization, user=user, is_active=True,
    ).first()
    if membership is None:
        raise PermissionError('No active membership for organization; shadow sync fail-closed.')

    ensure_canonical_role_definitions(organization)
    code, confidence = resolve_legacy_process_role_code(LEGACY_FIELD, profile_role)
    role_def = RoleDefinition.objects.filter(organization=organization, code=code).first()
    if role_def is None:
        raise RuntimeError(f'RoleDefinition {code} missing for organization {organization.pk}')

    # Never treat workspace membership roles as process assignments (defense in depth).
    if membership.role in ('OWNER', 'ADMIN', 'MEMBER') and code in (
        'workspace_owner', 'workspace_admin', 'workspace_member',
    ):
        raise RuntimeError('Refusing to shadow-write workspace roles as process assignments.')

    result = {'created': False, 'deactivated': 0, 'noop': False, 'code': code, 'confidence': confidence}

    with transaction.atomic():
        # Deactivate prior profile_role-sourced active assignments that no longer match.
        stale = ProcessRoleAssignment.objects.filter(
            organization=organization,
            user=user,
            is_active=True,
            legacy_source_field=LEGACY_FIELD,
        ).exclude(role_definition=role_def)
        for assignment in stale:
            assignment.is_active = False
            assignment.effective_end = timezone.now()
            assignment.assignment_reason = (
                f'{assignment.assignment_reason}\nDeactivated by {SHADOW_REASON}'.strip()
                if assignment.assignment_reason else f'Deactivated by {SHADOW_REASON}'
            )
            assignment.save()
            result['deactivated'] += 1
            try:
                from contracts.middleware import log_action
                from contracts.models import AuditLog

                log_action(
                    actor if getattr(actor, 'is_authenticated', False) else None,
                    AuditLog.Action.UPDATE,
                    'ProcessRoleAssignment',
                    object_id=assignment.pk,
                    object_repr=f'ProcessRoleAssignment {assignment.pk}',
                    organization=organization,
                    event_type=EVENT_ASSIGNMENT_DEACTIVATED,
                    changes={
                        'reason': SHADOW_REASON,
                        'legacy_source_field': LEGACY_FIELD,
                        'legacy_source_value': profile_role,
                        'correlation_id': str(correlation_id),
                        'user_id': user.pk,
                    },
                )
            except Exception:
                logger.exception('shadow deactivate audit failed')

        existing = ProcessRoleAssignment.objects.filter(
            organization=organization,
            user=user,
            role_definition=role_def,
            is_active=True,
        ).first()
        if existing:
            # Refresh legacy metadata if needed (idempotent).
            update_fields = []
            if existing.legacy_source_field != LEGACY_FIELD:
                existing.legacy_source_field = LEGACY_FIELD
                update_fields.append('legacy_source_field')
            if existing.legacy_source_value != (profile_role or ''):
                existing.legacy_source_value = profile_role or ''
                update_fields.append('legacy_source_value')
            if existing.mapping_confidence != confidence:
                existing.mapping_confidence = confidence
                update_fields.append('mapping_confidence')
            if update_fields:
                existing.updated_at = timezone.now()
                update_fields.append('updated_at')
                existing.save(update_fields=update_fields)
            result['noop'] = True
            return result

        create_process_role_assignment(
            organization=organization,
            user=user,
            membership=membership,
            role_definition=role_def,
            assignment_source='SYSTEM',
            legacy_source_field=LEGACY_FIELD,
            legacy_source_value=profile_role or '',
            mapping_confidence=confidence,
            is_system_managed=True,
            assignment_reason=SHADOW_REASON,
            correlation_id=correlation_id,
            actor=actor,
            skip_authz=True,
            emit_legacy_mapped=True,
        )
        result['created'] = True
    return result


def maybe_shadow_sync_profile_role(profile, *, previous_role=None, actor=None) -> None:
    """Hook after UserProfile.save. Never raises to the caller (legacy write already committed)."""
    if not shadow_write_enabled():
        return
    user = getattr(profile, 'user', None)
    if user is None:
        return
    new_role = getattr(profile, 'role', None) or ''
    if previous_role is not None and previous_role == new_role:
        return

    from contracts.models import OrganizationMembership

    correlation_id = uuid.uuid4()
    memberships = OrganizationMembership.objects.filter(user=user, is_active=True).select_related('organization')
    for membership in memberships:
        org = membership.organization
        try:
            shadow_sync_profile_role_for_organization(
                organization=org,
                user=user,
                profile_role=new_role,
                actor=actor,
                correlation_id=correlation_id,
            )
        except Exception as exc:
            logger.exception(
                'process role shadow sync failed org=%s user=%s', getattr(org, 'pk', None), getattr(user, 'pk', None),
            )
            _audit_shadow_failure(
                organization=org,
                user=user,
                legacy_value=new_role,
                error=exc,
                correlation_id=correlation_id,
                actor=actor,
            )


def maybe_shadow_sync_after_queryset_role_update(user_ids, previous_by_user: dict, new_role: str) -> None:
    if not shadow_write_enabled() or not user_ids:
        return
    from django.contrib.auth import get_user_model
    from contracts.models import UserProfile

    User = get_user_model()
    for user_id in user_ids:
        prev = previous_by_user.get(user_id)
        if prev == new_role:
            continue
        user = User.objects.filter(pk=user_id).first()
        profile = UserProfile.objects.filter(user_id=user_id).first()
        if not user or not profile:
            continue
        maybe_shadow_sync_profile_role(profile, previous_role=prev)
