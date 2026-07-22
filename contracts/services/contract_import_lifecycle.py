"""PDR-0002 helpers for import / bulk-ingestion lifecycle ownership."""

from __future__ import annotations

from django.core.exceptions import ValidationError

from contracts.services.lifecycle_dimensions import (
    RECORD_STATUS_ACTIVE,
    RECORD_STATUS_IN_PROGRESS,
    RECORD_TERMINAL_STATUSES,
    STAGE_DRAFTING,
    STAGE_OBLIGATION_TRACKING,
    is_valid_status_stage_pair,
    map_legacy_stage,
    map_legacy_status_to_record,
    validate_status_stage_pair,
)


class ImportLifecycleError(ValidationError):
    """Raised when an import attempts an illegal status/stage pair."""


def default_stage_for_status(status: str) -> str:
    """Canonical resting stage when an import supplies status only."""
    if status == RECORD_STATUS_ACTIVE:
        return STAGE_OBLIGATION_TRACKING
    if status in RECORD_TERMINAL_STATUSES:
        return STAGE_OBLIGATION_TRACKING
    return STAGE_DRAFTING


# Keep validate_status_stage_pair import available to callers/tests.
_ = validate_status_stage_pair


def resolve_import_status_stage(*, status, lifecycle_stage=None) -> tuple[str, str]:
    """Map legacy aliases and require a valid PDR-0002 pair.

    When ``lifecycle_stage`` is omitted, choose the default resting stage for
    the resolved status. When both are provided, reject illegal combinations
    instead of silently coercing.
    """
    resolved_status = map_legacy_status_to_record(status)
    if lifecycle_stage in {None, ''}:
        return resolved_status, default_stage_for_status(resolved_status)

    resolved_stage = map_legacy_stage(lifecycle_stage)
    if not is_valid_status_stage_pair(resolved_status, resolved_stage):
        raise ImportLifecycleError(
            f'Invalid import combination: status {resolved_status} cannot pair '
            f'with lifecycle_stage {resolved_stage}.'
        )
    return resolved_status, resolved_stage


def persist_contract_with_imported_lifecycle(
    contract,
    *,
    desired_status,
    desired_lifecycle_stage=None,
    actor=None,
    reason: str = '',
    source: str = 'import',
    request=None,
    non_lifecycle_update_fields: list[str] | None = None,
):
    """Save contract fields, then apply status/stage via the lifecycle service.

    Creates always start at ``IN_PROGRESS`` / ``DRAFTING``, then move to the
    desired pair through ``apply_operational_position(..., system=True)`` so
    audit/provenance remain intact for bulk ingestion.
    """
    from contracts.models import Contract
    from contracts.services.contract_lifecycle import get_contract_lifecycle_service

    status, stage = resolve_import_status_stage(
        status=desired_status,
        lifecycle_stage=desired_lifecycle_stage,
    )
    created = contract.pk is None
    reason_text = (reason or f'{source} lifecycle sync')[:300]
    actor_type = 'system'

    if created:
        contract.status = Contract.Status.IN_PROGRESS
        contract.lifecycle_stage = Contract.LifecycleStage.DRAFTING
        contract.save()
    else:
        # Persist non-lifecycle field changes without rewriting status/stage here.
        if non_lifecycle_update_fields:
            fields = [f for f in non_lifecycle_update_fields if f not in {'status', 'lifecycle_stage'}]
            if fields:
                if 'updated_at' not in fields:
                    fields = list(fields) + ['updated_at']
                contract.save(update_fields=fields)
        else:
            # Full save excluding lifecycle ownership: temporarily restore DB pair.
            current = Contract.objects.filter(pk=contract.pk).values('status', 'lifecycle_stage').first()
            if current:
                contract.status = current['status']
                contract.lifecycle_stage = current['lifecycle_stage']
            contract.save()

    needs_lifecycle = (
        created
        or contract.status != status
        or contract.lifecycle_stage != stage
    )
    # Reload after save for service lock path.
    contract.refresh_from_db()
    if needs_lifecycle and (contract.status != status or contract.lifecycle_stage != stage):
        contract = get_contract_lifecycle_service().apply_operational_position(
            contract,
            status=status,
            lifecycle_stage=stage,
            actor=actor,
            system=True,
            reason=reason_text,
            request=request,
            actor_type=actor_type,
        )
    return contract, created
