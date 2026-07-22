"""PAR-ID-001 — organization-scoped process-role assignment adapter (migration 0113).

Dual-read / diagnostics / parity only. Must NOT be used for:
- authorization
- approval gating
- signer resolution
- workflow routing
- contract access
- runtime assignment decisions
"""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from contracts.services.role_definition import LEGACY_LABEL_MAP, ensure_canonical_role_definitions

EVENT_ASSIGNMENT_CREATED = 'role.assignment.created'
EVENT_ASSIGNMENT_DEACTIVATED = 'role.assignment.deactivated'
EVENT_ASSIGNMENT_REPAIRED = 'role.assignment.repaired'
EVENT_ASSIGNMENT_LEGACY_MAPPED = 'role.assignment.legacy_mapped'
EVENT_ASSIGNMENT_DRIFT_DETECTED = 'role.assignment.drift_detected'

IMMUTABLE_PROCESS_ROLE_ASSIGNMENT_FIELDS = frozenset({
    'organization_id',
    'user_id',
    'role_definition_id',
    'assignment_source',
})

# Process-role legacy sources eligible for org-scoped backfill (not workspace membership).
PROCESS_LEGACY_SOURCES = frozenset({'profile_role'})

# Mapping confidence for known profile_role values.
PROFILE_ROLE_CONFIDENCE: dict[str, str] = {
    'PARTNER': 'CERTAIN',
    'SENIOR_ASSOCIATE': 'CERTAIN',
    'ASSOCIATE': 'CERTAIN',
    'PARALEGAL': 'CERTAIN',
    'LEGAL_ASSISTANT': 'CERTAIN',
    'CLIENT': 'CERTAIN',
    'ADMIN': 'AMBIGUOUS',  # → legacy_process_admin; NOT workspace_admin
}


class ProcessRoleAssignmentError(ValidationError):
    """Raised when process-role assignment rules are violated."""


def assert_process_role_assignment_immutable(instance, *, previous: dict) -> None:
    for field in ('organization_id', 'user_id', 'role_definition_id'):
        if previous.get(field) != getattr(instance, field, None):
            raise ProcessRoleAssignmentError(
                f'ProcessRoleAssignment.{field} is immutable after creation.'
            )
    if previous.get('assignment_source') != getattr(instance, 'assignment_source', None):
        raise ProcessRoleAssignmentError(
            'ProcessRoleAssignment.assignment_source is immutable after creation.'
        )


def _assert_manager(*, actor, organization) -> None:
    from contracts.permissions import can_manage_organization

    if actor is None or not getattr(actor, 'is_authenticated', False):
        raise PermissionDenied('Authentication required for process-role assignment management.')
    if organization is None:
        raise PermissionDenied('Organization is required.')
    if not can_manage_organization(actor, organization):
        raise PermissionDenied('Only organization OWNER or ADMIN may manage process-role assignments.')


def _assert_tenant(*, actor, organization) -> None:
    if actor is None or not getattr(actor, 'is_authenticated', False):
        return
    from contracts.tenancy import get_user_organization

    actor_org = get_user_organization(actor)
    if actor_org is None or organization is None or actor_org.pk != organization.pk:
        raise PermissionDenied('Cross-tenant process-role assignment operations are forbidden.')


def _validate_membership_consistency(*, organization, user, membership) -> None:
    from contracts.models import OrganizationMembership

    if membership is None:
        # Require an active membership in the organization for the user.
        if not OrganizationMembership.objects.filter(
            organization=organization, user=user, is_active=True,
        ).exists():
            raise ProcessRoleAssignmentError(
                'User must have an active membership in the organization.'
            )
        return
    if membership.organization_id != organization.pk:
        raise ProcessRoleAssignmentError('Membership organization must match assignment organization.')
    if membership.user_id != user.pk:
        raise ProcessRoleAssignmentError('Membership user must match assignment user.')
    if not membership.is_active:
        raise ProcessRoleAssignmentError('Membership must be active.')


def _audit(*, actor, organization, event_type, assignment, changes: dict | None = None) -> None:
    from contracts.middleware import log_action
    from contracts.models import AuditLog

    log_action(
        actor if getattr(actor, 'is_authenticated', False) else None,
        AuditLog.Action.UPDATE,
        'ProcessRoleAssignment',
        object_id=getattr(assignment, 'pk', None),
        object_repr=f'ProcessRoleAssignment {getattr(assignment, "pk", "")}',
        organization=organization,
        event_type=event_type,
        changes=changes or {},
    )


@transaction.atomic
def create_process_role_assignment(
    *,
    organization,
    user,
    role_definition,
    assignment_source: str,
    actor=None,
    membership=None,
    legacy_source_field: str = '',
    legacy_source_value: str = '',
    mapping_confidence: str = 'CERTAIN',
    is_system_managed: bool = False,
    effective_start=None,
    effective_end=None,
    assignment_reason: str = '',
    correlation_id=None,
    skip_authz: bool = False,
    emit_legacy_mapped: bool = False,
):
    from contracts.models import ProcessRoleAssignment

    if not skip_authz:
        _assert_tenant(actor=actor, organization=organization)
        _assert_manager(actor=actor, organization=organization)

    if role_definition.organization_id != organization.pk:
        raise ProcessRoleAssignmentError('RoleDefinition must belong to the same organization.')
    _validate_membership_consistency(organization=organization, user=user, membership=membership)

    if assignment_source not in ProcessRoleAssignment.AssignmentSource.values:
        raise ProcessRoleAssignmentError(f'Invalid assignment_source: {assignment_source}')
    if mapping_confidence not in ProcessRoleAssignment.MappingConfidence.values:
        raise ProcessRoleAssignmentError(f'Invalid mapping_confidence: {mapping_confidence}')

    if ProcessRoleAssignment.objects.filter(
        organization=organization, user=user, role_definition=role_definition, is_active=True,
    ).exists():
        raise ProcessRoleAssignmentError(
            'An active assignment already exists for this user and role definition.'
        )

    assignment = ProcessRoleAssignment(
        organization=organization,
        user=user,
        membership=membership,
        role_definition=role_definition,
        assignment_source=assignment_source,
        legacy_source_field=legacy_source_field or '',
        legacy_source_value=legacy_source_value or '',
        mapping_confidence=mapping_confidence,
        is_active=True,
        is_system_managed=is_system_managed,
        effective_start=effective_start or timezone.now(),
        effective_end=effective_end,
        assigned_by=actor if getattr(actor, 'is_authenticated', False) else None,
        assignment_reason=assignment_reason or '',
        correlation_id=correlation_id or uuid.uuid4(),
    )
    assignment.save(skip_process_role_immutability=True)
    event = EVENT_ASSIGNMENT_LEGACY_MAPPED if emit_legacy_mapped else EVENT_ASSIGNMENT_CREATED
    _audit(
        actor=actor,
        organization=organization,
        event_type=event,
        assignment=assignment,
        changes={
            'role_definition_code': role_definition.code,
            'assignment_source': assignment_source,
            'mapping_confidence': mapping_confidence,
            'legacy_source_field': legacy_source_field,
            'legacy_source_value': legacy_source_value,
        },
    )
    return assignment


@transaction.atomic
def deactivate_process_role_assignment(assignment, *, actor, reason: str = '', skip_authz: bool = False):
    if not skip_authz:
        _assert_tenant(actor=actor, organization=assignment.organization)
        _assert_manager(actor=actor, organization=assignment.organization)
    if assignment.is_system_managed and not skip_authz:
        raise ProcessRoleAssignmentError(
            'System-managed assignments require governed repair to deactivate.'
        )
    if not assignment.is_active:
        return assignment
    assignment.is_active = False
    assignment.effective_end = assignment.effective_end or timezone.now()
    if reason:
        assignment.assignment_reason = (
            f'{assignment.assignment_reason}\nDeactivated: {reason}'.strip()
            if assignment.assignment_reason else f'Deactivated: {reason}'
        )
    assignment.save()
    _audit(
        actor=actor,
        organization=assignment.organization,
        event_type=EVENT_ASSIGNMENT_DEACTIVATED,
        assignment=assignment,
        changes={'is_active': False, 'reason': reason},
    )
    return assignment


@transaction.atomic
def repair_process_role_assignment(
    assignment,
    *,
    actor,
    reason: str,
    is_active: bool | None = None,
    effective_end=None,
    membership=None,
    skip_authz: bool = False,
):
    if not skip_authz:
        _assert_tenant(actor=actor, organization=assignment.organization)
        _assert_manager(actor=actor, organization=assignment.organization)
    if not reason or not reason.strip():
        raise ProcessRoleAssignmentError('Repair requires a reason.')
    changes: dict[str, Any] = {'reason': reason.strip()}
    if is_active is not None and is_active != assignment.is_active:
        changes['is_active'] = {'from': assignment.is_active, 'to': is_active}
        assignment.is_active = is_active
        if not is_active and assignment.effective_end is None:
            assignment.effective_end = timezone.now()
    if effective_end is not None:
        changes['effective_end'] = str(effective_end)
        assignment.effective_end = effective_end
    if membership is not None:
        _validate_membership_consistency(
            organization=assignment.organization, user=assignment.user, membership=membership,
        )
        changes['membership_id'] = membership.pk
        assignment.membership = membership
    assignment.assignment_reason = (
        f'{assignment.assignment_reason}\nRepair: {reason.strip()}'.strip()
        if assignment.assignment_reason else f'Repair: {reason.strip()}'
    )
    assignment.save()
    _audit(
        actor=actor,
        organization=assignment.organization,
        event_type=EVENT_ASSIGNMENT_REPAIRED,
        assignment=assignment,
        changes=changes,
    )
    return assignment


def resolve_legacy_process_role_code(source_field: str, source_value: str) -> tuple[str, str]:
    """Return (role_definition_code, mapping_confidence) for a legacy process-role label."""
    value = (source_value or '').strip().upper()
    field = (source_field or '').strip()
    code = LEGACY_LABEL_MAP.get((field, value))
    if code is None:
        return 'legacy_unknown', 'UNKNOWN'
    if field == 'profile_role':
        confidence = PROFILE_ROLE_CONFIDENCE.get(value, 'UNKNOWN')
        return code, confidence
    # Non-profile process sources (e.g. approval_step) are catalogue mappings only —
    # not backfilled as user assignments in this slice.
    return code, 'CERTAIN'


def dual_read_process_roles(*, organization, user) -> dict[str, Any]:
    """Non-authoritative dual-read of canonical assignments vs legacy profile roles.

    Must not be used for authorization or runtime routing.
    """
    from contracts.models import OrganizationMembership, ProcessRoleAssignment, UserProfile

    ensure_canonical_role_definitions(organization)

    membership = OrganizationMembership.objects.filter(
        organization=organization, user=user, is_active=True,
    ).first()

    canonical = list(
        ProcessRoleAssignment.objects.filter(
            organization=organization, user=user, is_active=True,
        ).select_related('role_definition')
    )
    canonical_payload = [
        {
            'role_definition_id': a.role_definition_id,
            'code': a.role_definition.code,
            'category': a.role_definition.category,
            'assignment_source': a.assignment_source,
            'mapping_confidence': a.mapping_confidence,
            'legacy_source_field': a.legacy_source_field,
            'legacy_source_value': a.legacy_source_value,
        }
        for a in canonical
    ]

    profile = UserProfile.objects.filter(user=user).first()
    legacy_payload = []
    if profile and profile.role:
        code, confidence = resolve_legacy_process_role_code('profile_role', profile.role)
        legacy_payload.append({
            'source_field': 'profile_role',
            'source_value': profile.role,
            'mapped_code': code,
            'mapping_confidence': confidence,
            'organization_scope': 'user_global_legacy',
        })

    # Workspace membership role is recorded for drift awareness but is NOT a process role.
    workspace_payload = None
    if membership:
        ws_code = LEGACY_LABEL_MAP.get(('membership_role', membership.role))
        workspace_payload = {
            'source_field': 'membership_role',
            'source_value': membership.role,
            'mapped_workspace_code': ws_code,
            'note': 'Workspace Role — not a process-role assignment; never merged with process ADMIN.',
        }

    canonical_codes = {row['code'] for row in canonical_payload}
    legacy_codes = {row['mapped_code'] for row in legacy_payload}
    conflicts = []
    unresolved = []
    drift = []

    for row in legacy_payload:
        if row['mapping_confidence'] == 'UNKNOWN':
            unresolved.append(row)
        elif row['mapping_confidence'] == 'AMBIGUOUS':
            conflicts.append({
                'type': 'ambiguous_legacy',
                'legacy': row,
                'detail': 'Ambiguous ADMIN / uncertain process meaning; LEGACY_UNKNOWN target.',
            })
        if row['mapped_code'] not in canonical_codes:
            drift.append({
                'classification': 'legacy_without_canonical',
                'legacy': row,
            })

    for code in canonical_codes - legacy_codes:
        # Canonical-only is expected after manual adds; classify as informational drift.
        drift.append({
            'classification': 'canonical_without_legacy',
            'code': code,
        })

    # Detect forbidden ADMIN merge signal for reporting
    if (
        membership
        and membership.role == 'ADMIN'
        and profile
        and profile.role == 'ADMIN'
    ):
        conflicts.append({
            'type': 'admin_name_collision',
            'detail': (
                'OrganizationMembership.ADMIN and UserProfile.ADMIN coexist; '
                'meanings must remain separate (workspace vs legacy_process_admin).'
            ),
        })

    report = {
        'organization_id': organization.pk,
        'user_id': user.pk,
        'membership_id': membership.pk if membership else None,
        'canonical_assignments': canonical_payload,
        'legacy_assignments': legacy_payload,
        'workspace_role': workspace_payload,
        'mapping_confidence_summary': {
            row['mapped_code']: row['mapping_confidence'] for row in legacy_payload
        },
        'conflicts': conflicts,
        'unresolved_values': unresolved,
        'drift_classification': drift,
        'authoritative_for_runtime': False,
        'consumer_policy': 'diagnostics_parity_planning_display_only',
    }

    if drift or conflicts or unresolved:
        # Audit drift detection without elevating to runtime authority.
        try:
            from contracts.middleware import log_action
            from contracts.models import AuditLog

            log_action(
                None,
                AuditLog.Action.UPDATE,
                'ProcessRoleAssignment',
                object_id=None,
                object_repr=f'dual_read user={user.pk} org={organization.pk}',
                organization=organization,
                event_type=EVENT_ASSIGNMENT_DRIFT_DETECTED,
                changes={
                    'conflicts': len(conflicts),
                    'unresolved': len(unresolved),
                    'drift': len(drift),
                    'user_id': user.pk,
                },
            )
        except Exception:
            pass

    return report


@transaction.atomic
def backfill_process_role_assignments_for_organization(organization, *, actor=None) -> dict[str, int]:
    """Truthful backfill of org-scoped process-role assignments from UserProfile.role.

    Does not modify UserProfile.role or OrganizationMembership.role.
    """
    from contracts.models import OrganizationMembership, ProcessRoleAssignment, RoleDefinition, UserProfile

    ensure_canonical_role_definitions(organization)
    created = 0
    skipped = 0
    ambiguous = 0

    memberships = (
        OrganizationMembership.objects.filter(organization=organization, is_active=True)
        .select_related('user')
    )
    for membership in memberships:
        profile = UserProfile.objects.filter(user=membership.user).first()
        if not profile or not profile.role:
            skipped += 1
            continue
        code, confidence = resolve_legacy_process_role_code('profile_role', profile.role)
        role_def = RoleDefinition.objects.filter(organization=organization, code=code).first()
        if role_def is None:
            skipped += 1
            continue
        if ProcessRoleAssignment.objects.filter(
            organization=organization,
            user=membership.user,
            role_definition=role_def,
            is_active=True,
        ).exists():
            skipped += 1
            continue
        create_process_role_assignment(
            organization=organization,
            user=membership.user,
            membership=membership,
            role_definition=role_def,
            assignment_source='LEGACY_BACKFILL',
            legacy_source_field='profile_role',
            legacy_source_value=profile.role,
            mapping_confidence=confidence,
            is_system_managed=True,
            assignment_reason='0113 truthful legacy backfill from UserProfile.role',
            actor=actor,
            skip_authz=True,
            emit_legacy_mapped=True,
        )
        created += 1
        if confidence == 'AMBIGUOUS':
            ambiguous += 1
    return {'created': created, 'skipped': skipped, 'ambiguous': ambiguous}
