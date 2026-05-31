from datetime import date
from decimal import Decimal

from django.utils import timezone


CONTRACT_LIFECYCLE_TRANSITIONS = {
    'DRAFTING': {'INTERNAL_REVIEW', 'ARCHIVED'},
    'INTERNAL_REVIEW': {'NEGOTIATION', 'ARCHIVED'},
    'NEGOTIATION': {'APPROVAL', 'ARCHIVED'},
    'APPROVAL': {'SIGNATURE', 'ARCHIVED'},
    'SIGNATURE': {'EXECUTED', 'ARCHIVED'},
    'EXECUTED': {'OBLIGATION_TRACKING', 'RENEWAL', 'ARCHIVED'},
    'OBLIGATION_TRACKING': {'RENEWAL', 'ARCHIVED'},
    'RENEWAL': {'DRAFTING', 'ARCHIVED'},
    'ARCHIVED': set(),
}

TRACKED_CONTRACT_FIELDS = (
    'status',
    'lifecycle_stage',
    'contract_type',
    'counterparty',
    'value',
    'currency',
    'governing_law',
    'jurisdiction',
    'risk_level',
    'data_transfer_flag',
    'dpa_attached',
    'scc_attached',
    'start_date',
    'end_date',
    'renewal_date',
    'auto_renew',
    'notice_period_days',
    'termination_notice_date',
    'client_id',
    'matter_id',
)


def get_allowed_lifecycle_stages(current_stage):
    return CONTRACT_LIFECYCLE_TRANSITIONS.get(current_stage, set())


def can_transition_lifecycle_stage(contract, new_stage):
    if contract is None or not new_stage:
        return False

    current_stage = getattr(contract, 'lifecycle_stage', None)
    if new_stage == current_stage:
        return True
    return new_stage in get_allowed_lifecycle_stages(current_stage)


def _normalize_audit_value(value):
    if isinstance(value, (date,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if hasattr(value, 'pk'):
        return value.pk
    return value


def build_contract_audit_changes(before_contract, after_contract, tracked_fields=TRACKED_CONTRACT_FIELDS):
    if before_contract is None or after_contract is None:
        return {}

    changes = {}
    for field_name in tracked_fields:
        before_value = _normalize_audit_value(getattr(before_contract, field_name, None))
        after_value = _normalize_audit_value(getattr(after_contract, field_name, None))
        if before_value != after_value:
            changes[field_name] = {
                'before': before_value,
                'after': after_value,
            }
    return changes


def build_contract_lifecycle_guidance(contract, today=None):
    today = today or timezone.localdate()

    guidance = {
        'state': 'Active',
        'severity': 'low',
        'action': 'No immediate lifecycle action required.',
        'next_stage': getattr(contract, 'lifecycle_stage', None),
        'detail': '',
        'signals': [],
    }

    if contract is None:
        return guidance

    if contract.lifecycle_stage == 'ARCHIVED':
        guidance.update({
            'state': 'Archived',
            'severity': 'low',
            'action': 'No operational action required.',
            'next_stage': 'ARCHIVED',
            'detail': 'Archived contracts are retained for evidence and reference only.',
        })
        return guidance

    if contract.end_date:
        days_until_end = (contract.end_date - today).days
        guidance['signals'].append(
            f'End date is in {days_until_end} day(s) on {contract.end_date.isoformat()}.'
        )
        if days_until_end < 0:
            guidance.update({
                'state': 'Expired',
                'severity': 'high',
                'action': 'Review immediately for renewal, termination, or archive eligibility.',
                'next_stage': 'RENEWAL',
            })
        elif days_until_end <= 30:
            guidance.update({
                'state': 'Renewal Window',
                'severity': 'medium',
                'action': 'Prepare renewal or termination decision now.',
                'next_stage': 'RENEWAL',
            })

    if contract.renewal_date:
        days_until_renewal = (contract.renewal_date - today).days
        guidance['signals'].append(
            f'Renewal date is in {days_until_renewal} day(s) on {contract.renewal_date.isoformat()}.'
        )
        if days_until_renewal <= 14 and guidance['severity'] != 'high':
            guidance.update({
                'state': 'Renewal Due',
                'severity': 'medium',
                'action': 'Finalize renewal language and stakeholder approvals.',
                'next_stage': 'RENEWAL',
            })

    if contract.auto_renew:
        guidance['signals'].append('Auto-renew is enabled.')
        if guidance['severity'] == 'low':
            guidance.update({
                'state': 'Auto-Renew Enabled',
                'severity': 'medium',
                'action': 'Set a cancellation checkpoint before the notice deadline.',
                'next_stage': 'RENEWAL',
            })
        else:
            guidance['action'] = f"{guidance['action']} Auto-renew is enabled."

    if contract.termination_notice_date:
        days_until_notice = (contract.termination_notice_date - today).days
        guidance['signals'].append(
            f'Termination notice date is in {days_until_notice} day(s) on {contract.termination_notice_date.isoformat()}.'
        )
        if days_until_notice <= 0:
            guidance.update({
                'state': 'Termination Notice Due',
                'severity': 'high',
                'action': 'Send termination notice or move to archive review immediately.',
                'next_stage': 'RENEWAL',
            })

    if guidance['severity'] == 'low' and contract.lifecycle_stage == 'EXECUTED' and not contract.end_date:
        guidance.update({
            'state': 'Execution Complete',
            'action': 'Capture renewal date and notice period to prepare for lifecycle management.',
            'next_stage': 'OBLIGATION_TRACKING',
        })

    return guidance