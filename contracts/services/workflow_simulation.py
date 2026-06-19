from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Optional

from contracts.models import WorkflowTemplate, WorkflowTemplateStep
from contracts.services.workflow_execution import (
    _CONDITION_PATTERN,
    _FIELD_ALIASES,
    evaluate_condition_expression,
)


@dataclass(frozen=True)
class WorkflowTemplateStepPreview:
    step_id: int
    order: int
    name: str
    description: str
    step_kind: str
    condition_expression: str
    would_apply: bool
    reason: str
    assignee_role: str
    resolved_assignee: str
    sla_hours: Optional[int]
    escalation_after_hours: Optional[int]
    preview_status: str


@dataclass(frozen=True)
class WorkflowTemplateSimulationResult:
    template_id: int
    template_name: str
    organization_id: Optional[int]
    preview_steps: list[WorkflowTemplateStepPreview]
    active_step_count: int
    skipped_step_count: int


class _ContractLikeAdapter:
    def __init__(self, data: dict[str, Any], organization=None):
        self.organization = organization
        self._data = data
        self.contract_type = data.get('contract_type') or ''
        self.value = data.get('value')
        self.jurisdiction = data.get('jurisdiction') or ''
        self.governing_law = data.get('governing_law') or ''
        self.data_transfer_flag = bool(data.get('data_transfer_flag', False))
        self.risk_level = data.get('risk_level') or ''
        self.counterparty = data.get('counterparty_name') or data.get('counterparty') or ''
        self.status = data.get('status') or ''


def _resolve_assignee_display(step: WorkflowTemplateStep, contract_like) -> str:
    assignee = step.resolve_assignee(contract_like)
    if assignee is not None:
        full_name = (assignee.get_full_name() or '').strip()
        return full_name or getattr(assignee, 'username', '') or ''
    if step.assignee_role:
        return step.assignee_role
    return ''


def _condition_reason(step: WorkflowTemplateStep, contract_like) -> tuple[bool, str]:
    expression = (step.condition_expression or '').strip()
    if not expression:
        return True, 'No condition specified.'

    match = _CONDITION_PATTERN.match(expression)
    if not match:
        return False, 'Invalid condition expression.'

    field_name = match.group('field').strip().lower()
    if field_name not in _FIELD_ALIASES:
        return False, f"Unknown condition field '{field_name}'."

    try:
        would_apply = evaluate_condition_expression(contract_like, expression)
    except Exception:
        return False, f"Invalid condition expression '{expression}'."

    if would_apply:
        return True, f"Condition '{expression}' matched."
    return False, f"Condition '{expression}' did not match."


def simulate_workflow_template(template: WorkflowTemplate, contract_data: dict[str, Any], organization=None, user=None):
    """
    Build a dry-run preview of how a template would materialize for contract-like data.

    This function does not create or mutate Workflow / WorkflowStep records.
    """
    if template is None:
        return WorkflowTemplateSimulationResult(
            template_id=0,
            template_name='',
            organization_id=getattr(organization, 'id', None),
            preview_steps=[],
            active_step_count=0,
            skipped_step_count=0,
        )

    contract_like = _ContractLikeAdapter(contract_data or {}, organization=organization)
    preview_steps: list[WorkflowTemplateStepPreview] = []
    first_actionable = True

    for step in template.steps.order_by('order', 'pk'):
        would_apply, reason = _condition_reason(step, contract_like)
        preview_status = 'WOULD_SKIP'
        if would_apply:
            if step.step_kind == WorkflowTemplateStep.StepKind.AUTOMATIC:
                preview_status = 'WOULD_COMPLETE_AUTOMATICALLY'
                reason = reason or 'Automatic step would complete immediately.'
            elif first_actionable:
                preview_status = 'WOULD_START'
                first_actionable = False
                reason = reason or 'First applicable actionable step.'
            else:
                preview_status = 'WOULD_WAIT'
                reason = reason or 'Applicable but waiting for an earlier actionable step.'
        else:
            preview_status = 'WOULD_SKIP'

        preview_steps.append(
            WorkflowTemplateStepPreview(
                step_id=step.pk,
                order=step.order,
                name=step.name,
                description=step.description,
                step_kind=step.step_kind,
                condition_expression=step.condition_expression,
                would_apply=would_apply,
                reason=reason,
                assignee_role=step.assignee_role,
                resolved_assignee=_resolve_assignee_display(step, contract_like),
                sla_hours=step.sla_hours,
                escalation_after_hours=step.escalation_after_hours,
                preview_status=preview_status,
            )
        )

    active_step_count = sum(1 for preview in preview_steps if preview.preview_status != 'WOULD_SKIP')
    skipped_step_count = len(preview_steps) - active_step_count
    return WorkflowTemplateSimulationResult(
        template_id=template.pk,
        template_name=template.name,
        organization_id=getattr(template, 'organization_id', None),
        preview_steps=preview_steps,
        active_step_count=active_step_count,
        skipped_step_count=skipped_step_count,
    )
