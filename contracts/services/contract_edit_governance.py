"""Edit-page governance helpers for Contract update flows."""

from __future__ import annotations

from dataclasses import dataclass

from contracts.models import Contract, ContractVersion
from contracts.services.intake_risk import assess_intake_risk
from contracts.services.contract_launch_setup import get_launch_setup_for_type


# Fields that must not silently overwrite an approved / executed record.
GOVERNED_EDIT_FIELDS = frozenset({
    'contract_type',
    'counterparty',
    'value',
    'currency',
    'governing_law',
    'jurisdiction',
    'start_date',
    'end_date',
    'renewal_date',
    'auto_renew',
    'notice_period_days',
    'termination_notice_date',
    'paper_source',
    'personal_data_processing',
    'sensitive_data_flag',
    'counterparty_privacy_review_required',
    'data_transfer_flag',
    'dpa_attached',
    'scc_attached',
    'content',
})

# Safe to save without creating a version / amendment.
METADATA_EDIT_FIELDS = frozenset({
    'title',
    'owner',
    'client',
    'matter',
    'language',
})

_LOCKED_STATUSES = frozenset({
    Contract.Status.ACTIVE,
    Contract.Status.EXPIRED,
    Contract.Status.TERMINATED,
    Contract.Status.ARCHIVED,
    Contract.Status.CANCELLED,
})

_LOCKED_STAGES = frozenset({
    Contract.LifecycleStage.EXECUTED,
    Contract.LifecycleStage.OBLIGATION_TRACKING,
    Contract.LifecycleStage.RENEWAL,
    Contract.LifecycleStage.SIGNATURE,
    Contract.LifecycleStage.APPROVAL,
})

GOVERNED_CHANGE_WARNING = (
    'These changes will recalculate risk and may alter the approval route.'
)


def contract_is_governance_locked(contract: Contract | None) -> bool:
    """True when the approved record must not be overwritten in-place."""
    if not contract or not getattr(contract, 'pk', None):
        return False
    status = getattr(contract, 'status', '') or ''
    stage = getattr(contract, 'lifecycle_stage', '') or ''
    return status in _LOCKED_STATUSES or stage in _LOCKED_STAGES


def revision_session_key(contract_id: int) -> str:
    return f'contract_revision_unlocked_{contract_id}'


def risk_state_for_contract(contract: Contract, *, reassessment=None) -> dict:
    """Accurate risk label for the edit rail (never 'Risk not assessed')."""
    if reassessment is not None:
        return risk_state_from_assessment(reassessment)

    stored = (contract.risk_level or '').strip()
    if contract_is_governance_locked(contract) and not stored:
        return {
            'key': 'reassessment_required',
            'label': 'Risk reassessment required',
            'detail': 'Governed terms changed or risk was never recorded for this approved record.',
            'tone': 'attention',
        }
    if stored:
        return {
            'key': 'calculated',
            'label': f'{contract.get_risk_level_display()} risk',
            'detail': 'Stored risk level for this contract.',
            'tone': 'success' if stored == Contract.RiskLevel.LOW else 'attention',
        }
    return {
        'key': 'incomplete',
        'label': 'Risk assessment incomplete',
        'detail': 'Risk has not been calculated for this contract yet.',
        'tone': 'attention',
    }


def current_version_label(contract: Contract) -> str:
    latest = (
        ContractVersion.objects.filter(contract=contract)
        .order_by('-version_number')
        .values_list('version_number', flat=True)
        .first()
    )
    if latest:
        return f'v{latest}'
    return 'v1 (current record)'


def validation_issues_for_contract(contract: Contract) -> list[str]:
    issues = []
    if not contract.owner_id:
        issues.append('Contract owner is missing.')
    if not (contract.counterparty or '').strip():
        issues.append('Counterparty is missing.')
    if not contract.start_date:
        issues.append('Effective date is missing.')
    if not contract.end_date:
        issues.append('Expiry date is missing.')
    if contract_is_governance_locked(contract) and not (contract.risk_level or '').strip():
        issues.append('Risk reassessment is required.')
    return issues


@dataclass
class EditGovernanceContext:
    locked: bool
    revision_unlocked: bool
    governed_fields_readonly: bool
    current_version: str
    risk_state: dict
    validation_issues: list[str]
    change_impact: str
    approval_impact: str
    setup_readonly: dict
    warning: str


def build_edit_governance_context(contract: Contract, *, revision_unlocked: bool = False) -> EditGovernanceContext:
    locked = contract_is_governance_locked(contract)
    governed_readonly = locked and not revision_unlocked
    setup = get_launch_setup_for_type(contract.contract_type)
    risk_state = risk_state_for_contract(contract)
    issues = validation_issues_for_contract(contract)
    if governed_readonly:
        change_impact = 'Metadata edits only. Governed terms require a new version or amendment.'
        approval_impact = 'Saving metadata does not change the approval route.'
    elif locked and revision_unlocked:
        change_impact = 'Revision unlocked. Changing governed terms will recalculate risk and may alter approvals.'
        approval_impact = GOVERNED_CHANGE_WARNING
    else:
        change_impact = 'Draft record — changes save in place.'
        approval_impact = 'Risk and routing update when governed inputs change.'
    return EditGovernanceContext(
        locked=locked,
        revision_unlocked=revision_unlocked,
        governed_fields_readonly=governed_readonly,
        current_version=current_version_label(contract),
        risk_state=risk_state,
        validation_issues=issues,
        change_impact=change_impact,
        approval_impact=approval_impact,
        setup_readonly={
            'template_name': setup.template.name if setup and setup.template else 'Not recorded',
            'playbook': setup.playbook if setup else '—',
            'contract_type': contract.get_contract_type_display(),
            'paper_source': contract.get_paper_source_display() or 'Not set',
        },
        warning=GOVERNED_CHANGE_WARNING,
    )


def restore_governed_fields(instance: Contract, original: Contract) -> None:
    """Prevent in-place overwrite of governed fields on a locked record."""
    for field_name in GOVERNED_EDIT_FIELDS:
        setattr(instance, field_name, getattr(original, field_name))


def governed_fields_changed(cleaned_data: dict, original: Contract) -> list[str]:
    changed = []
    for field_name in GOVERNED_EDIT_FIELDS:
        if field_name not in cleaned_data:
            continue
        new_value = cleaned_data.get(field_name)
        old_value = getattr(original, field_name, None)
        if new_value != old_value:
            changed.append(field_name)
    return changed


def assess_edit_risk(cleaned_data: dict, *, template_applied: bool = False):
    return assess_intake_risk(cleaned_data, template_applied=template_applied)


def risk_state_from_assessment(assessment) -> dict:
    """Map intake assessment onto edit-page risk vocabulary."""
    if assessment.state != 'PRELIMINARY' or not assessment.level:
        return {
            'key': 'incomplete',
            'label': 'Risk assessment incomplete',
            'detail': 'Fill the remaining risk inputs to calculate a level.',
            'tone': 'attention',
        }
    return {
        'key': 'reassessed',
        'label': f'{assessment.level.title()} risk',
        'detail': GOVERNED_CHANGE_WARNING,
        'tone': 'attention' if assessment.level in {'MEDIUM', 'HIGH', 'CRITICAL'} else 'success',
    }
