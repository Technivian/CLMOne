"""PAR-ID-001 R1 — CERTAIN non-ADMIN ProcessRoleAssignment remediation.

Creates missing CERTAIN assignments for the authorized 12-row scope only.
Does not enable flags, change resolver authority, or remediate AMBIGUOUS ADMIN.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from typing import Any

from django.db import transaction
from django.utils import timezone

from contracts.services.process_role_assignment import (
    create_process_role_assignment,
    deactivate_process_role_assignment,
    resolve_legacy_process_role_code,
)
from contracts.services.role_definition import ensure_canonical_role_definitions

# Authorized mapping rules (R1-MAP-05/06 intentionally omitted).
R1_CERTAIN_MAPS: dict[str, str] = {
    'PARTNER': 'partner_reviewer',
    'SENIOR_ASSOCIATE': 'senior_reviewer',
    'ASSOCIATE': 'legal_reviewer',
    'PARALEGAL': 'paralegal_reviewer',
}

R1_RULE_BY_LEGACY: dict[str, str] = {
    'PARTNER': 'R1-MAP-01',
    'SENIOR_ASSOCIATE': 'R1-MAP-02',
    'ASSOCIATE': 'R1-MAP-03',
    'PARALEGAL': 'R1-MAP-04',
}

# Exact authorized scope keys: (org_slug, username, profile_role, mapped_code, rule_id)
R1_AUTHORIZED_KEYS: frozenset[tuple[str, str, str, str, str]] = frozenset({
    ('demo-firm', 'jsmith', 'PARTNER', 'partner_reviewer', 'R1-MAP-01'),
    ('demo-firm', 'sjones', 'SENIOR_ASSOCIATE', 'senior_reviewer', 'R1-MAP-02'),
    ('demo-firm', 'mwilson', 'PARALEGAL', 'paralegal_reviewer', 'R1-MAP-04'),
    ('clmone-demo', 'demo_partner', 'PARTNER', 'partner_reviewer', 'R1-MAP-01'),
    ('clmone-demo', 'demo_associate', 'SENIOR_ASSOCIATE', 'senior_reviewer', 'R1-MAP-02'),
    ('clmone-demo', 'demo_paralegal', 'PARALEGAL', 'paralegal_reviewer', 'R1-MAP-04'),
    ('clmone-mvp', 'mvp_owner', 'ASSOCIATE', 'legal_reviewer', 'R1-MAP-03'),
    ('clmone-mvp', 'mvp_reviewer', 'SENIOR_ASSOCIATE', 'senior_reviewer', 'R1-MAP-02'),
    ('controlled-pilot-org', 'pilot_requester', 'PARALEGAL', 'paralegal_reviewer', 'R1-MAP-04'),
    ('controlled-pilot-org', 'pilot_legal', 'ASSOCIATE', 'legal_reviewer', 'R1-MAP-03'),
    ('payrollminds-demo', 'payrollminds_legal', 'SENIOR_ASSOCIATE', 'senior_reviewer', 'R1-MAP-02'),
    ('payrollminds-demo', 'payrollminds_procurement', 'ASSOCIATE', 'legal_reviewer', 'R1-MAP-03'),
})

RUN_ID_PREFIX = 'r1_remediation_run_id='


class R1ScopeError(ValueError):
    """Actual discovered CERTAIN missing scope does not match the authorized 12 rows."""


@dataclass(frozen=True)
class R1PlannedRow:
    organization_id: int
    organization_slug: str
    user_id: int
    username: str
    profile_role: str
    mapped_code: str
    rule_id: str
    membership_id: int | None
    already_active: bool

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.organization_slug,
            self.username,
            self.profile_role,
            self.mapped_code,
            self.rule_id,
        )


def _reason_for_run(*, run_id: str, rule_id: str) -> str:
    return (
        f'PAR-ID-001 R1 CERTAIN non-ADMIN remediation; '
        f'{RUN_ID_PREFIX}{run_id}; mapping_rule={rule_id}'
    )


def discover_r1_candidates(*, include_already_active: bool = True) -> list[R1PlannedRow]:
    """Discover CERTAIN R1-MAP-01..04 candidates (missing or already active)."""
    from contracts.models import Organization, OrganizationMembership, ProcessRoleAssignment, UserProfile

    planned: list[R1PlannedRow] = []
    for org in Organization.objects.order_by('id'):
        ensure_canonical_role_definitions(org)
        memberships = (
            OrganizationMembership.objects.filter(organization=org, is_active=True)
            .select_related('user')
            .order_by('user_id')
        )
        for membership in memberships:
            profile = UserProfile.objects.filter(user=membership.user).first()
            if not profile or not profile.role:
                continue
            legacy = (profile.role or '').strip().upper()
            if legacy not in R1_CERTAIN_MAPS:
                continue
            code, confidence = resolve_legacy_process_role_code('profile_role', legacy)
            if confidence != 'CERTAIN':
                continue
            expected = R1_CERTAIN_MAPS[legacy]
            if code != expected:
                continue
            rule_id = R1_RULE_BY_LEGACY[legacy]
            already = ProcessRoleAssignment.objects.filter(
                organization=org,
                user=membership.user,
                role_definition__code=code,
                is_active=True,
            ).exists()
            if already and not include_already_active:
                continue
            planned.append(
                R1PlannedRow(
                    organization_id=org.pk,
                    organization_slug=org.slug,
                    user_id=membership.user_id,
                    username=membership.user.username,
                    profile_role=legacy,
                    mapped_code=code,
                    rule_id=rule_id,
                    membership_id=membership.pk,
                    already_active=already,
                )
            )
    return planned


def validate_r1_scope(planned: list[R1PlannedRow]) -> None:
    """Fail closed unless discovered keys exactly match the authorized 12-row scope."""
    keys = {row.key for row in planned}
    if keys != R1_AUTHORIZED_KEYS:
        missing = sorted(R1_AUTHORIZED_KEYS - keys)
        extra = sorted(keys - R1_AUTHORIZED_KEYS)
        raise R1ScopeError(
            f'R1 scope mismatch: expected {len(R1_AUTHORIZED_KEYS)} keys, got {len(keys)}; '
            f'missing={missing!r}; extra={extra!r}'
        )


def plan_r1_remediation() -> dict[str, Any]:
    planned = discover_r1_candidates(include_already_active=True)
    validate_r1_scope(planned)
    to_create = [r for r in planned if not r.already_active]
    already = [r for r in planned if r.already_active]
    return {
        'mode': 'dry-run',
        'authorized_count': len(R1_AUTHORIZED_KEYS),
        'discovered_count': len(planned),
        'to_create_count': len(to_create),
        'already_active_count': len(already),
        'to_create': [asdict(r) for r in to_create],
        'already_active': [asdict(r) for r in already],
        'scope_valid': True,
        'flags_must_remain_false': True,
    }


@transaction.atomic
def apply_r1_remediation(*, actor=None, run_id: str | None = None) -> dict[str, Any]:
    from contracts.models import OrganizationMembership, ProcessRoleAssignment, RoleDefinition, User

    planned = discover_r1_candidates(include_already_active=True)
    validate_r1_scope(planned)
    run_id = run_id or str(uuid.uuid4())
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    now = timezone.now().isoformat()

    for row in planned:
        if row.already_active:
            skipped.append({**asdict(row), 'reason': 'already_active'})
            continue
        from contracts.models import Organization

        org = Organization.objects.get(pk=row.organization_id)
        user = User.objects.get(pk=row.user_id)
        membership = (
            OrganizationMembership.objects.filter(pk=row.membership_id).first()
            if row.membership_id
            else None
        )
        role_def = RoleDefinition.objects.get(organization=org, code=row.mapped_code)
        # Preserve existing: re-check active inside transaction
        if ProcessRoleAssignment.objects.filter(
            organization=org, user=user, role_definition=role_def, is_active=True,
        ).exists():
            skipped.append({**asdict(row), 'reason': 'already_active_race'})
            continue
        assignment = create_process_role_assignment(
            organization=org,
            user=user,
            membership=membership,
            role_definition=role_def,
            assignment_source='LEGACY_BACKFILL',
            legacy_source_field='profile_role',
            legacy_source_value=row.profile_role,
            mapping_confidence='CERTAIN',
            is_system_managed=True,
            assignment_reason=_reason_for_run(run_id=run_id, rule_id=row.rule_id),
            actor=actor,
            skip_authz=True,
            emit_legacy_mapped=True,
        )
        created.append({
            **asdict(row),
            'assignment_id': assignment.pk,
            'remediation_run_id': run_id,
            'actor_id': getattr(actor, 'pk', None),
            'timestamp': now,
            'provenance': {
                'assignment_source': 'LEGACY_BACKFILL',
                'mapping_confidence': 'CERTAIN',
                'mapping_rule': row.rule_id,
                'legacy_source_field': 'profile_role',
                'legacy_source_value': row.profile_role,
            },
        })

    if len(created) + len(skipped) != len(R1_AUTHORIZED_KEYS):
        raise R1ScopeError('R1 apply did not cover the full authorized key set')

    return {
        'mode': 'apply',
        'remediation_run_id': run_id,
        'created_count': len(created),
        'skipped_count': len(skipped),
        'created': created,
        'skipped': skipped,
        'timestamp': now,
    }


@transaction.atomic
def rollback_r1_remediation(*, run_id: str, actor=None) -> dict[str, Any]:
    from contracts.models import ProcessRoleAssignment

    if not run_id or RUN_ID_PREFIX not in f'{RUN_ID_PREFIX}{run_id}':
        # always form marker for filter
        pass
    marker = f'{RUN_ID_PREFIX}{run_id}'
    qs = ProcessRoleAssignment.objects.filter(
        assignment_reason__contains=marker,
        is_active=True,
    ).select_related('organization', 'user', 'role_definition')
    deactivated = []
    for assignment in qs:
        # Hard exclusion: never touch AMBIGUOUS / legacy_process_admin
        if assignment.mapping_confidence != 'CERTAIN':
            continue
        if assignment.role_definition.code == 'legacy_process_admin':
            continue
        deactivate_process_role_assignment(
            assignment,
            actor=actor,
            reason=f'R1 rollback for {marker}',
            skip_authz=True,
        )
        deactivated.append({
            'assignment_id': assignment.pk,
            'organization_id': assignment.organization_id,
            'organization_slug': assignment.organization.slug,
            'user_id': assignment.user_id,
            'username': assignment.user.username,
            'mapped_code': assignment.role_definition.code,
        })
    return {
        'mode': 'rollback',
        'remediation_run_id': run_id,
        'deactivated_count': len(deactivated),
        'deactivated': deactivated,
        'timestamp': timezone.now().isoformat(),
    }
