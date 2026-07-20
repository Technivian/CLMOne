from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from contracts.models import WorkflowTemplate, WorkflowTemplateStep
from contracts.services.workflow_execution import (
    _CONDITION_PATTERN,
    _FIELD_ALIASES,
    describe_condition_expression,
    describe_condition_rules,
    evaluate_condition_expression,
    evaluate_step_condition,
    is_automation_kind,
    normalize_condition_rules,
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
    assignment_resolved: bool
    sla_hours: Optional[int]
    escalation_after_hours: Optional[int]
    preview_status: str
    has_condition: bool = False
    projected_deadline_label: str = ''
    sla_missing: bool = False


@dataclass(frozen=True)
class WorkflowSimulationBlockingIssue:
    step_id: Optional[int]
    step_name: str
    issue: str
    impact: str
    recommended_action: str
    design_url: str = ''
    focus_field: str = ''


@dataclass(frozen=True)
class WorkflowTemplateSimulationResult:
    template_id: int
    template_name: str
    organization_id: Optional[int]
    preview_steps: list[WorkflowTemplateStepPreview]
    active_step_count: int
    skipped_step_count: int
    matched_conditions: tuple[str, ...] = ()
    resulting_route: tuple[str, ...] = ()
    validation_messages: tuple[str, ...] = ()
    blocking_issues: tuple[WorkflowSimulationBlockingIssue, ...] = ()
    condition_evaluations: tuple[str, ...] = ()
    unresolved_assignment_count: int = 0
    simulation_completed: bool = True
    execution_blocked: bool = False
    execution_outcome_label: str = 'Ready to launch'
    result_tone: str = 'pass'  # pass | warning | blocked | fail
    final_outcome_label: str = 'would complete'
    banner_title: str = 'Simulation completed successfully'
    assignments_summary_label: str = 'all resolved'
    blocking_summary_label: str = 'No blocking issues'


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
        self.finance_threshold = data.get('finance_threshold')


def _condition_label(step: WorkflowTemplateStep) -> str:
    rules = normalize_condition_rules(getattr(step, 'condition_rules', None))
    if rules:
        return describe_condition_rules(rules) or ''
    return describe_condition_expression(step.condition_expression or '') or ''


def _expression_field(expression: str) -> str:
    match = _CONDITION_PATTERN.match((expression or '').strip())
    if not match:
        return ''
    return _FIELD_ALIASES.get(match.group('field').strip().lower(), match.group('field').strip().lower())


def _clause_expected_value(step: WorkflowTemplateStep, field: str) -> str:
    rules = normalize_condition_rules(getattr(step, 'condition_rules', None))
    if rules:
        for clause in rules.get('clauses') or []:
            if str(clause.get('field') or '').strip().lower() == field:
                return str(clause.get('value') or '').strip()
    expression = (step.condition_expression or '').strip()
    match = _CONDITION_PATTERN.match(expression)
    if match and _FIELD_ALIASES.get(match.group('field').strip().lower(), match.group('field').strip().lower()) == field:
        return str(match.group('value') or '').strip().strip("'\"")
    return ''


def _title_value(raw: str) -> str:
    value = (raw or '').strip().replace('_', ' ')
    if value.upper() == value and value.isalpha():
        return value.title()
    return value


def _humanize_condition_reason(step: WorkflowTemplateStep, would_apply: bool, *, invalid: bool = False, detail: str = '') -> str:
    """Enterprise-facing condition copy — never expose raw expressions like risk=HIGH."""
    name = (step.name or 'This step').strip() or 'This step'
    label = _condition_label(step)
    field = ''
    rules = normalize_condition_rules(getattr(step, 'condition_rules', None))
    if rules and rules.get('clauses'):
        field = str(rules['clauses'][0].get('field') or '')
    if not field:
        field = _expression_field(step.condition_expression or '')

    if invalid:
        if detail:
            return f'{name} could not be evaluated: {detail}'
        return f'{name} could not be evaluated because its condition is invalid.'

    if field == 'finance_threshold':
        if would_apply:
            return f'{name} was triggered because the contract met the finance approval threshold.'
        return f'{name} was skipped because the contract did not meet the finance approval threshold.'

    if field == 'data_transfer_flag':
        if would_apply:
            return f'{name} was triggered because cross-border data transfer is required.'
        return f'{name} was skipped because cross-border data transfer is not required.'

    if field == 'risk_level':
        expected = _title_value(_clause_expected_value(step, 'risk_level'))
        if would_apply:
            if expected:
                return f'{name} was triggered because the risk level was {expected}.'
            return f'{name} was triggered because the risk level matched the condition.'
        if expected:
            return f'{name} was skipped because the risk level was not {expected}.'
        return f'{name} was skipped because the risk level did not match.'

    if not label:
        if would_apply:
            return 'No condition specified.'
        return f'{name} was skipped.'

    label = label.replace(' equals ', ' is ')
    if would_apply:
        return f'{name} was triggered because {label}.'
    if field and ' is ' in label:
        expected = label.split(' is ', 1)[-1].strip()
        field_label = field.replace('_', ' ')
        return f'{name} was skipped because the {field_label} was not {expected}.'
    return f'{name} was skipped because {label} did not match.'


def _resolve_assignment(step: WorkflowTemplateStep, contract_like) -> tuple[bool, str]:
    """Return (resolved?, display). Role-only fallback is treated as unresolved."""
    assignee = step.resolve_assignee(contract_like)
    if assignee is not None:
        full_name = (assignee.get_full_name() or '').strip()
        return True, full_name or getattr(assignee, 'username', '') or 'Assigned user'
    role = (step.assignee_role or '').strip()
    if role:
        return False, f'{role} (unresolved)'
    return False, 'Unresolved'


def _projected_deadline_label(sla_hours: Optional[int]) -> str:
    if sla_hours is None:
        return 'Not configured'
    if sla_hours == 1:
        return 'Within 1 hour of step start'
    return f'Within {sla_hours} hours of step start'


def _condition_reason(step: WorkflowTemplateStep, contract_like) -> tuple[bool, str, bool]:
    """Return (would_apply, reason, is_invalid)."""
    rules = normalize_condition_rules(getattr(step, 'condition_rules', None))
    if rules:
        try:
            would_apply = evaluate_step_condition(contract_like, step)
        except Exception:
            return False, _humanize_condition_reason(step, False, invalid=True), True
        return would_apply, _humanize_condition_reason(step, would_apply), False

    expression = (step.condition_expression or '').strip()
    if not expression:
        return True, _humanize_condition_reason(step, True), False

    match = _CONDITION_PATTERN.match(expression)
    compound_ok = ' and ' in expression.lower() or ' or ' in expression.lower()
    if not match and not compound_ok:
        return False, _humanize_condition_reason(step, False, invalid=True, detail='Invalid condition expression.'), True

    if match:
        field_name = match.group('field').strip().lower()
        if field_name not in _FIELD_ALIASES:
            return (
                False,
                _humanize_condition_reason(
                    step,
                    False,
                    invalid=True,
                    detail=f'Unknown condition field “{field_name}”.',
                ),
                True,
            )

    try:
        would_apply = evaluate_condition_expression(contract_like, expression)
    except Exception:
        return False, _humanize_condition_reason(step, False, invalid=True), True

    return would_apply, _humanize_condition_reason(step, would_apply), False


def _execution_labels(
    *,
    blocked: bool,
    unresolved: int,
    has_route: bool,
    has_invalid: bool,
    has_warnings: bool,
) -> tuple[str, str, str, str]:
    """Return (result_tone, execution_outcome_label, final_outcome_label, banner_title)."""
    if has_invalid:
        return (
            'fail',
            'Execution blocked',
            'execution blocked',
            'Simulation could not be completed',
        )
    if not has_route:
        return (
            'blocked',
            'Execution blocked',
            'execution blocked',
            'Simulation completed with blocking issues',
        )
    if unresolved:
        return (
            'blocked',
            'Execution blocked',
            'execution blocked',
            'Simulation completed with blocking issues',
        )
    if blocked:
        return (
            'blocked',
            'Execution blocked',
            'execution blocked',
            'Simulation completed with blocking issues',
        )
    if has_warnings:
        return (
            'warning',
            'Ready to launch',
            'would complete with warnings',
            'Simulation completed with warnings',
        )
    return (
        'pass',
        'Ready to launch',
        'would complete',
        'Simulation completed successfully',
    )


def simulate_workflow_template(template: WorkflowTemplate, contract_data: dict[str, Any], organization=None, user=None):
    """
    Build a dry-run preview of how a template would materialize for contract-like data.

    This function does not create or mutate Workflow / WorkflowStep records.
    Simulation success (the dry-run completed) is separate from executability
    (whether the workflow could safely launch for these inputs).
    """
    if template is None:
        return WorkflowTemplateSimulationResult(
            template_id=0,
            template_name='',
            organization_id=getattr(organization, 'id', None),
            preview_steps=[],
            active_step_count=0,
            skipped_step_count=0,
            simulation_completed=True,
            execution_blocked=True,
            execution_outcome_label='Execution blocked',
            result_tone='fail',
            final_outcome_label='execution blocked',
            banner_title='Simulation could not be completed',
            assignments_summary_label='0 unresolved',
            blocking_summary_label='Invalid template',
        )

    contract_like = _ContractLikeAdapter(contract_data or {}, organization=organization)
    preview_steps: list[WorkflowTemplateStepPreview] = []
    first_actionable = True
    matched_conditions: list[str] = []
    condition_evaluations: list[str] = []
    resulting_route: list[str] = []
    validation_messages: list[str] = []
    blocking_issues: list[WorkflowSimulationBlockingIssue] = []
    unresolved_assignment_count = 0
    has_invalid = False
    has_warnings = False

    for step in template.steps.order_by('order', 'pk'):
        would_apply, reason, is_invalid = _condition_reason(step, contract_like)
        preview_status = 'WOULD_SKIP'
        assignment_resolved = True
        resolved_assignee = ''
        has_condition = bool(step.condition_expression or step.condition_rules)
        sla_missing = False

        if is_invalid:
            has_invalid = True
            validation_messages.append(reason)
            blocking_issues.append(
                WorkflowSimulationBlockingIssue(
                    step_id=step.pk,
                    step_name=step.name,
                    issue=reason,
                    impact='This step cannot be evaluated, so the route is unsafe to launch.',
                    recommended_action='Open Design and correct the step condition.',
                    design_url=f'?tab=design&step={step.pk}',
                    focus_field='conditions',
                )
            )
            preview_status = 'WOULD_SKIP'
            would_apply = False
        elif would_apply:
            if is_automation_kind(step.step_kind):
                preview_status = 'WOULD_COMPLETE_AUTOMATICALLY'
                reason = reason if reason and reason != 'No condition specified.' else 'Automation step would complete immediately.'
            elif first_actionable:
                preview_status = 'WOULD_START'
                first_actionable = False
                if reason == 'No condition specified.':
                    reason = 'First applicable actionable step.'
            else:
                preview_status = 'WOULD_WAIT'
                if reason == 'No condition specified.':
                    reason = 'Applicable but waiting for an earlier actionable step.'
            if has_condition:
                matched_conditions.append(reason)
            resulting_route.append(step.name)

            if not is_automation_kind(step.step_kind):
                assignment_resolved, resolved_assignee = _resolve_assignment(step, contract_like)
                if not assignment_resolved:
                    unresolved_assignment_count += 1
                    role_hint = f' ({step.assignee_role})' if step.assignee_role else ''
                    message = (
                        f'{step.name}: Assignment unresolved{role_hint}. '
                        'No matching workspace member could be resolved for this scenario.'
                    )
                    validation_messages.append(message)
                    blocking_issues.append(
                        WorkflowSimulationBlockingIssue(
                            step_id=step.pk,
                            step_name=step.name,
                            issue=f'Required assignment unresolved{role_hint}',
                            impact='Workflow cannot launch until this step has an assignee.',
                            recommended_action='Open Design and assign an owner or role mapping for this step.',
                            design_url=f'?tab=design&step={step.pk}',
                            focus_field='assignment',
                        )
                    )

            if step.sla_hours is None or step.escalation_after_hours is None:
                sla_missing = True
                has_warnings = True
        else:
            preview_status = 'WOULD_SKIP'

        if has_condition or is_invalid:
            condition_evaluations.append(reason)

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
                resolved_assignee=resolved_assignee,
                assignment_resolved=assignment_resolved,
                sla_hours=step.sla_hours,
                escalation_after_hours=step.escalation_after_hours,
                preview_status=preview_status,
                has_condition=has_condition,
                projected_deadline_label=_projected_deadline_label(step.sla_hours),
                sla_missing=sla_missing,
            )
        )

    active_step_count = sum(1 for preview in preview_steps if preview.preview_status != 'WOULD_SKIP')
    skipped_step_count = len(preview_steps) - active_step_count
    if not resulting_route:
        validation_messages.append('No steps would run for these inputs.')
        blocking_issues.append(
            WorkflowSimulationBlockingIssue(
                step_id=None,
                step_name='',
                issue='No steps would run for these inputs',
                impact='There is no actionable route for this scenario.',
                recommended_action='Adjust scenario inputs or open Design to review step conditions.',
                design_url='?tab=design',
            )
        )

    execution_blocked = bool(validation_messages) or unresolved_assignment_count > 0 or not resulting_route or has_invalid
    if execution_blocked:
        has_warnings = False

    result_tone, execution_outcome_label, final_outcome_label, banner_title = _execution_labels(
        blocked=execution_blocked,
        unresolved=unresolved_assignment_count,
        has_route=bool(resulting_route),
        has_invalid=has_invalid,
        has_warnings=has_warnings,
    )

    if unresolved_assignment_count:
        assignments_summary_label = f'{unresolved_assignment_count} unresolved'
        blocking_summary_label = (
            f'{unresolved_assignment_count} required assignment'
            f'{"s" if unresolved_assignment_count != 1 else ""} unresolved'
        )
    elif execution_blocked:
        assignments_summary_label = 'all resolved' if resulting_route else '0 unresolved'
        blocking_summary_label = f'{len(blocking_issues)} blocking issue{"s" if len(blocking_issues) != 1 else ""}'
    else:
        assignments_summary_label = 'all resolved'
        blocking_summary_label = 'No blocking issues'

    return WorkflowTemplateSimulationResult(
        template_id=template.pk,
        template_name=template.name,
        organization_id=getattr(template, 'organization_id', None),
        preview_steps=preview_steps,
        active_step_count=active_step_count,
        skipped_step_count=skipped_step_count,
        matched_conditions=tuple(matched_conditions),
        resulting_route=tuple(resulting_route),
        validation_messages=tuple(validation_messages),
        blocking_issues=tuple(blocking_issues),
        condition_evaluations=tuple(condition_evaluations),
        unresolved_assignment_count=unresolved_assignment_count,
        simulation_completed=True,
        execution_blocked=execution_blocked,
        execution_outcome_label=execution_outcome_label,
        result_tone=result_tone,
        final_outcome_label=final_outcome_label,
        banner_title=banner_title,
        assignments_summary_label=assignments_summary_label,
        blocking_summary_label=blocking_summary_label,
    )
