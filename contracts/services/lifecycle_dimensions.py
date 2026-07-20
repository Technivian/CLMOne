"""Canonical three-dimension contract lifecycle vocabulary.

Record status, workflow stage, and document state are separate. Pairing rules
live here so models, services, migrations, and tests share one authority.
"""

from __future__ import annotations

from typing import Iterable


# --- Record status -----------------------------------------------------------

RECORD_STATUS_IN_PROGRESS = 'IN_PROGRESS'
RECORD_STATUS_ACTIVE = 'ACTIVE'
RECORD_STATUS_EXPIRED = 'EXPIRED'
RECORD_STATUS_TERMINATED = 'TERMINATED'
RECORD_STATUS_CANCELLED = 'CANCELLED'
RECORD_STATUS_ARCHIVED = 'ARCHIVED'

RECORD_STATUSES = frozenset({
    RECORD_STATUS_IN_PROGRESS,
    RECORD_STATUS_ACTIVE,
    RECORD_STATUS_EXPIRED,
    RECORD_STATUS_TERMINATED,
    RECORD_STATUS_CANCELLED,
    RECORD_STATUS_ARCHIVED,
})

RECORD_TERMINAL_STATUSES = frozenset({
    RECORD_STATUS_EXPIRED,
    RECORD_STATUS_TERMINATED,
    RECORD_STATUS_CANCELLED,
    RECORD_STATUS_ARCHIVED,
})

# Historical Contract.status → record status (data migration / reads).
LEGACY_STATUS_TO_RECORD = {
    'NEEDS_INPUT': RECORD_STATUS_IN_PROGRESS,
    'UPLOADED': RECORD_STATUS_IN_PROGRESS,
    'PROCESSING': RECORD_STATUS_IN_PROGRESS,
    'CLASSIFICATION_REQUIRED': RECORD_STATUS_IN_PROGRESS,
    'AI_REVIEW_IN_PROGRESS': RECORD_STATUS_IN_PROGRESS,
    'AI_REVIEW_READY': RECORD_STATUS_IN_PROGRESS,
    'HUMAN_REVIEW_IN_PROGRESS': RECORD_STATUS_IN_PROGRESS,
    'INFORMATION_REQUIRED': RECORD_STATUS_IN_PROGRESS,
    'INTERNAL_APPROVAL_REQUIRED': RECORD_STATUS_IN_PROGRESS,
    'NEGOTIATION_IN_PROGRESS': RECORD_STATUS_IN_PROGRESS,
    'READY_FOR_SIGNATURE': RECORD_STATUS_IN_PROGRESS,
    'SIGNATURE_IN_PROGRESS': RECORD_STATUS_IN_PROGRESS,
    'EXECUTED': RECORD_STATUS_IN_PROGRESS,  # executed-as-status → still pre-activation record unless stage says otherwise
    'OBLIGATIONS_ACTIVE': RECORD_STATUS_ACTIVE,
    'DRAFT': RECORD_STATUS_IN_PROGRESS,
    'PENDING': RECORD_STATUS_IN_PROGRESS,
    'IN_REVIEW': RECORD_STATUS_IN_PROGRESS,
    'APPROVED': RECORD_STATUS_IN_PROGRESS,
    'ACTIVE': RECORD_STATUS_ACTIVE,
    'EXPIRED': RECORD_STATUS_EXPIRED,
    'TERMINATED': RECORD_STATUS_TERMINATED,
    'COMPLETED': RECORD_STATUS_ACTIVE,
    'CANCELLED': RECORD_STATUS_CANCELLED,
    'ARCHIVED': RECORD_STATUS_ARCHIVED,
    'IN_PROGRESS': RECORD_STATUS_IN_PROGRESS,
}


def map_legacy_status_to_record(status: str | None, *, lifecycle_stage: str | None = None) -> str:
    if lifecycle_stage == 'ARCHIVED':
        return RECORD_STATUS_ARCHIVED
    if not status:
        return RECORD_STATUS_IN_PROGRESS
    if status in RECORD_STATUSES:
        return status
    return LEGACY_STATUS_TO_RECORD.get(status, RECORD_STATUS_IN_PROGRESS)


# --- Workflow stage ----------------------------------------------------------

STAGE_INTAKE = 'INTAKE'
STAGE_DRAFTING = 'DRAFTING'
STAGE_INTERNAL_REVIEW = 'INTERNAL_REVIEW'
STAGE_NEGOTIATION = 'NEGOTIATION'
STAGE_APPROVAL = 'APPROVAL'
STAGE_SIGNATURE = 'SIGNATURE'
STAGE_EXECUTED = 'EXECUTED'
STAGE_OBLIGATION_TRACKING = 'OBLIGATION_TRACKING'
STAGE_RENEWAL = 'RENEWAL'

WORKFLOW_STAGES = frozenset({
    STAGE_INTAKE,
    STAGE_DRAFTING,
    STAGE_INTERNAL_REVIEW,
    STAGE_NEGOTIATION,
    STAGE_APPROVAL,
    STAGE_SIGNATURE,
    STAGE_EXECUTED,
    STAGE_OBLIGATION_TRACKING,
    STAGE_RENEWAL,
})

PRE_ACTIVATION_STAGES = frozenset({
    STAGE_INTAKE,
    STAGE_DRAFTING,
    STAGE_INTERNAL_REVIEW,
    STAGE_NEGOTIATION,
    STAGE_APPROVAL,
    STAGE_SIGNATURE,
    STAGE_EXECUTED,
})

POST_ACTIVATION_STAGES = frozenset({
    STAGE_EXECUTED,
    STAGE_OBLIGATION_TRACKING,
    STAGE_RENEWAL,
})

LEGACY_STAGE_FALLBACK = {
    'ARCHIVED': STAGE_OBLIGATION_TRACKING,
}


def map_legacy_stage(stage: str | None) -> str:
    if not stage:
        return STAGE_DRAFTING
    if stage in WORKFLOW_STAGES:
        return stage
    return LEGACY_STAGE_FALLBACK.get(stage, STAGE_DRAFTING)


# --- Document state ----------------------------------------------------------

DOC_STATE_DRAFT = 'DRAFT'
DOC_STATE_FINAL = 'FINAL'
DOC_STATE_EXECUTED = 'EXECUTED'
DOC_STATE_SUPERSEDED = 'SUPERSEDED'

DOCUMENT_STATES = frozenset({
    DOC_STATE_DRAFT,
    DOC_STATE_FINAL,
    DOC_STATE_EXECUTED,
    DOC_STATE_SUPERSEDED,
})

LEGACY_DOCUMENT_STATUS = {
    'DRAFT': DOC_STATE_DRAFT,
    'REVIEW': DOC_STATE_DRAFT,
    'APPROVED': DOC_STATE_FINAL,
    'FINAL': DOC_STATE_FINAL,
    'ARCHIVED': DOC_STATE_SUPERSEDED,
    'EXECUTED': DOC_STATE_EXECUTED,
    'SUPERSEDED': DOC_STATE_SUPERSEDED,
}


def map_legacy_document_status(status: str | None) -> str:
    if not status:
        return DOC_STATE_DRAFT
    if status in DOCUMENT_STATES:
        return status
    return LEGACY_DOCUMENT_STATUS.get(status, DOC_STATE_DRAFT)


# --- Pairing matrix ----------------------------------------------------------

def allowed_stages_for_status(status: str) -> frozenset[str]:
    if status == RECORD_STATUS_IN_PROGRESS:
        return PRE_ACTIVATION_STAGES
    if status == RECORD_STATUS_ACTIVE:
        return POST_ACTIVATION_STAGES
    if status in RECORD_TERMINAL_STATUSES:
        # Terminal records freeze stage; any known stage is acceptable for storage,
        # but transitions must not advance further without system repair.
        return WORKFLOW_STAGES
    return frozenset()


def is_valid_status_stage_pair(status: str, stage: str) -> bool:
    if status not in RECORD_STATUSES or stage not in WORKFLOW_STAGES:
        return False
    return stage in allowed_stages_for_status(status)


def validate_status_stage_pair(status: str, stage: str) -> None:
    from django.core.exceptions import ValidationError

    if not is_valid_status_stage_pair(status, stage):
        raise ValidationError(
            f'Invalid combination: record status {status} cannot pair with workflow stage {stage}.'
        )


def is_valid_document_state_for_contract(
    document_state: str,
    *,
    contract_status: str | None,
    contract_stage: str | None,
) -> bool:
    if document_state not in DOCUMENT_STATES:
        return False
    if document_state != DOC_STATE_EXECUTED:
        return True
    status = contract_status or ''
    stage = contract_stage or ''
    if status in {
        RECORD_STATUS_ACTIVE,
        RECORD_STATUS_EXPIRED,
        RECORD_STATUS_TERMINATED,
        RECORD_STATUS_ARCHIVED,
    }:
        return True
    return stage in {STAGE_EXECUTED, STAGE_OBLIGATION_TRACKING, STAGE_RENEWAL}


def validate_document_state_for_contract(
    document_state: str,
    *,
    contract_status: str | None,
    contract_stage: str | None,
) -> None:
    from django.core.exceptions import ValidationError

    if not is_valid_document_state_for_contract(
        document_state,
        contract_status=contract_status,
        contract_stage=contract_stage,
    ):
        raise ValidationError(
            'Document state Executed is only allowed after the contract is active '
            'or at/after the Executed workflow stage.'
        )


def normalize_contract_dimensions(status: str | None, stage: str | None) -> tuple[str, str]:
    """Return (record_status, workflow_stage) after legacy mapping + archive rule."""
    mapped_stage = map_legacy_stage(stage)
    if stage == 'ARCHIVED':
        return RECORD_STATUS_ARCHIVED, mapped_stage
    mapped_status = map_legacy_status_to_record(status, lifecycle_stage=stage)
    # If legacy EXECUTED status + EXECUTED/OBLIGATION stage, prefer ACTIVE.
    if status in {'EXECUTED', 'OBLIGATIONS_ACTIVE'} and mapped_stage in POST_ACTIVATION_STAGES:
        if mapped_stage != STAGE_EXECUTED or status == 'OBLIGATIONS_ACTIVE':
            mapped_status = RECORD_STATUS_ACTIVE
        elif mapped_stage == STAGE_EXECUTED and status == 'EXECUTED':
            # Resting at executed stage still pre-obligation → IN_PROGRESS unless already active ops.
            mapped_status = RECORD_STATUS_IN_PROGRESS
    if mapped_status == RECORD_STATUS_ACTIVE and mapped_stage in PRE_ACTIVATION_STAGES - {STAGE_EXECUTED}:
        mapped_stage = STAGE_OBLIGATION_TRACKING
    if mapped_status == RECORD_STATUS_IN_PROGRESS and mapped_stage in {STAGE_OBLIGATION_TRACKING, STAGE_RENEWAL}:
        mapped_status = RECORD_STATUS_ACTIVE
    return mapped_status, mapped_stage
