"""DPA Privacy Review Workflow — the first flagship "workflow-first" flow.

Orchestrates the New Contract → DPA path: a data-driven intake form
(FieldDefinition/FieldValue, not a hardcoded ModelForm), a live draft
preview, rule-based (not AI) risk-signal detection, and creation of a real
Workflow instance (the model that already plays "WorkflowInstance") with
its WorkflowSteps materialized from the DPA WorkflowTemplate.

Kept separate from contracts/services/draft_cockpit.py, which is scoped to
network-free, read-only helpers for the generic (any contract type)
create page — this module does multi-table transactional writes and calls
the workflow execution engine, a different concern.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from contracts.middleware import log_action
from contracts.models import (
    ApprovalRoute,
    ClauseTemplate,
    CommandCenterWorkItem,
    Contract,
    ContractTemplate,
    DraftDocument,
    FieldDefinition,
    FieldValue,
    RiskSignal,
    Workflow,
    WorkflowTemplate,
)
from contracts.services.contract_templates import MERGE_FIELDS, _format_value
from contracts.services.workflow_execution import materialize_workflow_from_template
from contracts.tenancy import set_organization_on_instance

SECTION_ORDER = [
    FieldDefinition.Section.BASIC_DETAILS,
    FieldDefinition.Section.PRIVACY_DETAILS,
    FieldDefinition.Section.LEGAL_POSITION,
    FieldDefinition.Section.PRIVACY_QUESTIONS,
]

_TOKEN_RE = re.compile(r'\{\{\s*(\w+)\s*\}\}')


def get_dpa_workflow_template() -> Optional[WorkflowTemplate]:
    return (
        WorkflowTemplate.objects
        .filter(contract_type__code='DPA', is_active=True)
        .order_by('-version')
        .first()
    )


def get_dpa_contract_template() -> Optional[ContractTemplate]:
    return (
        ContractTemplate.objects
        .filter(contract_type=Contract.ContractType.DPA, is_active=True)
        .order_by('name')
        .first()
    )


def get_field_definitions_by_section(workflow_template: WorkflowTemplate) -> Dict[str, List[FieldDefinition]]:
    """Grouped, in fixed display order, for left-column rendering."""
    if workflow_template is None:
        return {section: [] for section in SECTION_ORDER}
    definitions = list(
        FieldDefinition.objects.filter(workflow_template=workflow_template).order_by('section', 'order')
    )
    grouped = {section: [] for section in SECTION_ORDER}
    for field in definitions:
        grouped.setdefault(field.section, []).append(field)
    return grouped


def get_dpa_approval_route(workflow_template: WorkflowTemplate) -> List[ApprovalRoute]:
    if workflow_template is None:
        return []
    return list(ApprovalRoute.objects.filter(workflow_template=workflow_template).order_by('order'))


def get_clause_library_count(organization, contract_type: str) -> int:
    """Local copy of draft_cockpit's applicable-clause counter — kept here
    too so this module has no import dependency on draft_cockpit.py."""
    from django.db.models import Q
    if not contract_type:
        return 0
    qs = ClauseTemplate.objects.filter(is_approved=True)
    qs = qs.filter(Q(organization=organization) | Q(organization__isnull=True)) if organization else qs.filter(organization__isnull=True)
    matching = 0
    for clause in qs.only('applicable_contract_types'):
        allowed = [t.strip() for t in (clause.applicable_contract_types or '').split(',') if t.strip()]
        if not allowed or contract_type in allowed:
            matching += 1
    return matching


def render_dpa_live_preview(template_body: Optional[str], field_values_by_key: dict) -> str:
    """Merge-field substitution extended with FieldDefinition-only tokens.

    Checks the basic contract MERGE_FIELDS map first (title/counterparty/
    value/...), then falls back to a submitted FieldDefinition value (e.g.
    {{dpo_contact}}). Unrecognized tokens are left as-is, mirroring
    render_merge_fields's contract.
    """
    if not template_body:
        return ''

    values = dict(field_values_by_key or {})
    values.setdefault(
        'data_transfer_position',
        'Data leaves the EEA; SCCs or an approved transfer mechanism must be included'
        if values.get('cross_border_transfer')
        else 'No transfer outside the EEA is currently selected'
    )
    values.setdefault(
        'subprocessor_position',
        'Subprocessors are involved; approved flow-down obligations apply'
        if values.get('subprocessors_used')
        else 'No subprocessors are currently selected'
    )

    def _replace(match):
        token = match.group(1)
        if token in values:
            return _format_value(values.get(token))
        if token in MERGE_FIELDS:
            # No Contract instance yet on the builder page — MERGE_FIELDS
            # tokens resolve from field_values_by_key too, since basic
            # details (counterparty, start_date, ...) are also collected
            # as FieldDefinitions with matching keys.
            alias = MERGE_FIELDS[token]
            if alias in values:
                return _format_value(values.get(alias))
            return match.group(0)
        return match.group(0)

    return _TOKEN_RE.sub(_replace, template_body)


@dataclass
class RiskSignalRule:
    code: str
    description: str
    severity: str
    predicate: str  # documentation only; logic lives in detect_dpa_risk_signals


def detect_dpa_risk_signals(workflow: Workflow, field_values_by_key: dict) -> List[RiskSignal]:
    """Rule-based (no AI/LLM call) risk-signal detection from submitted
    field values. Persists RiskSignal rows scoped to the Workflow."""
    signals = []

    personal_data = bool(field_values_by_key.get('personal_data_involved', True))
    if personal_data:
        signals.append(('dpa_review_required', 'Personal data processing selected; DPA review and Legal review are required.', RiskSignal.Severity.MEDIUM))

    cross_border = bool(field_values_by_key.get('cross_border_transfer'))
    mechanism = field_values_by_key.get('transfer_mechanism')
    if cross_border:
        signals.append(('scc_transfer_review', 'Data may leave the EEA; SCC transfer position and DPO approval are required.', RiskSignal.Severity.HIGH))
        if not mechanism or mechanism == 'None':
            signals.append(('cross_border_no_mechanism', 'Cross-border transfer flagged but no transfer mechanism selected.', RiskSignal.Severity.HIGH))

    if not field_values_by_key.get('dpo_contact'):
        signals.append(('missing_dpo_contact', 'No Data Protection Officer contact provided.', RiskSignal.Severity.MEDIUM))

    if field_values_by_key.get('subprocessors_used'):
        signals.append(('subprocessor_review', 'Subprocessors are involved; approved subprocessor flow-down language must be reviewed.', RiskSignal.Severity.MEDIUM))
        if not field_values_by_key.get('liability_position'):
            signals.append(('subprocessors_undisclosed', 'Subprocessors are involved but no fallback/liability position was captured.', RiskSignal.Severity.MEDIUM))

    breach_hours = field_values_by_key.get('breach_notification_hours')
    try:
        breach_hours_val = float(breach_hours) if breach_hours not in (None, '') else None
    except (TypeError, ValueError):
        breach_hours_val = None
    if breach_hours_val is None or breach_hours_val > 72:
        signals.append(('breach_window_too_long', 'Breach notification window is missing or exceeds 72 hours.', RiskSignal.Severity.MEDIUM))

    created = []
    for code, description, severity in signals:
        created.append(RiskSignal.objects.create(workflow=workflow, code=code, description=description, severity=severity))
    return created


def sync_command_center_work_item_for_workflow(workflow: Workflow) -> CommandCenterWorkItem:
    """The single, isolated Command Center integration point — deliberately
    kept out of contracts/services/command_center.py (uncommitted,
    in-progress work from a separate session) to avoid touching its batch
    projection logic. _work_item_href() in that module already checks
    action_path first, so this item resolves correctly without any change
    there; dashboard.html's Kanban "Draft" column already matches
    stage == 'Drafting', so no template change is needed either."""
    contract = workflow.contract
    item, _ = CommandCenterWorkItem.objects.update_or_create(
        organization=workflow.organization,
        source_type=CommandCenterWorkItem.SourceType.WORKFLOW,
        source_model='Workflow',
        source_object_id=workflow.pk,
        defaults={
            'title': workflow.title,
            'subtitle': contract.counterparty if contract else '',
            'item_type': 'DPA workflow',
            'stage': 'Drafting',
            'status': CommandCenterWorkItem.Status.OPEN,
            'risk_level': contract.risk_level if contract else Contract.RiskLevel.LOW,
            'priority': CommandCenterWorkItem.Priority.MEDIUM,
            'contract': contract,
            'workflow': workflow,
            'action_label': 'Continue draft',
            'action_path': reverse('contracts:workflow_detail', kwargs={'pk': workflow.pk}),
            'last_source_synced_at': timezone.now(),
        },
    )
    return item


@transaction.atomic
def create_dpa_workflow_instance(*, organization, user, cleaned_values: dict, request=None) -> Workflow:
    """The single orchestration entry point: creates the Contract, the
    Workflow instance, materializes its WorkflowSteps, stores FieldValues,
    renders and saves the DraftDocument, detects RiskSignals, and syncs the
    Command Center Priority Queue row — all in one transaction."""
    workflow_template = get_dpa_workflow_template()
    if workflow_template is None:
        raise ValueError('DPA Privacy Review Workflow template is not seeded.')

    field_defs = list(FieldDefinition.objects.filter(workflow_template=workflow_template))

    contract = Contract(
        title=f"DPA — {cleaned_values.get('counterparty') or 'Untitled counterparty'}",
        contract_type=Contract.ContractType.DPA,
        status=Contract.Status.DRAFT,
        created_by=user,
    )
    set_organization_on_instance(contract, organization)
    for field in field_defs:
        if field.maps_to_contract_field and field.key in cleaned_values:
            setattr(contract, field.maps_to_contract_field, cleaned_values[field.key])
    contract.save()

    workflow = Workflow.objects.create(
        title='DPA Privacy Review Workflow',
        description=f"Privacy review for the DPA with {cleaned_values.get('counterparty') or 'this counterparty'}.",
        organization=organization,
        template=workflow_template,
        contract=contract,
        status=Workflow.Status.ACTIVE,
        created_by=user,
    )
    materialize_workflow_from_template(workflow)

    FieldValue.objects.bulk_create([
        FieldValue(workflow=workflow, field_definition=field, value=cleaned_values.get(field.key))
        for field in field_defs
    ])

    contract_template = get_dpa_contract_template()
    preview_content = render_dpa_live_preview(contract_template.body if contract_template else None, cleaned_values)
    DraftDocument.objects.create(
        workflow=workflow, contract=contract, content=preview_content, version=1, is_current=True, created_by=user,
    )

    detect_dpa_risk_signals(workflow, cleaned_values)
    sync_command_center_work_item_for_workflow(workflow)

    log_action(
        user, 'CREATE', 'Workflow', workflow.id, str(workflow),
        changes={'event': 'dpa_workflow_created', 'contract_id': contract.id},
        request=request, organization=organization,
    )
    return workflow
