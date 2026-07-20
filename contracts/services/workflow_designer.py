"""Workflow Designer list helpers: cards, publish validation, duplication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db.models import Count, Q
from django.urls import reverse

from contracts.models import AuditLog, Workflow, WorkflowTemplate, WorkflowTemplateStep
from contracts.services.workflow_templates import clone_template_version, list_template_versions


OPEN_WORKFLOW_STATUSES = frozenset({
    Workflow.Status.ACTIVE,
})


@dataclass(frozen=True)
class PublishValidationResult:
    ok: bool
    errors: tuple[str, ...]

    @property
    def message(self) -> str:
        if self.ok:
            return ''
        return ' '.join(self.errors)


def workflow_designer_tabs(*, active: str) -> list[dict]:
    """Tab strip for the Workflow Designer authoring hub."""
    items = (
        ('templates', 'Templates', 'contracts:workflow_template_list'),
        ('routing', 'Routing rules', 'contracts:approval_rule_list'),
        ('approval_rules', 'Approval rules', 'contracts:workflow_approval_route_list'),
        ('history', 'Change history', 'contracts:workflow_designer_history'),
    )
    return [
        {
            'key': key,
            'label': label,
            'url': reverse(url_name),
            'active': key == active,
        }
        for key, label, url_name in items
    ]


def template_stage_count(template: WorkflowTemplate) -> int:
    cached = getattr(template, 'step_count', None)
    if cached is not None:
        return int(cached)
    return template.steps.count()


def is_incomplete_template(template: WorkflowTemplate) -> bool:
    """Zero-stage templates are never publishable — surface as Draft · Incomplete."""
    return template_stage_count(template) == 0


def is_standard_incomplete_template(template: WorkflowTemplate) -> bool:
    name = (template.name or '').strip().lower()
    return is_incomplete_template(template) and (
        name == 'standard' or name.startswith('standard ') or 'standard workflow' in name
    )


def ensure_stepless_templates_unpublished(queryset) -> int:
    """Force any published zero-stage templates back to draft (data integrity)."""
    stepless = list(
        queryset.annotate(step_count=Count('steps')).filter(is_active=True, step_count=0)
    )
    if not stepless:
        return 0
    WorkflowTemplate.objects.filter(pk__in=[t.pk for t in stepless]).update(is_active=False)
    for template in stepless:
        template.is_active = False
    return len(stepless)


def validate_template_for_publish(template: WorkflowTemplate) -> PublishValidationResult:
    """Gate publish on stages, routing, owners, and configuration integrity."""
    errors: list[str] = []
    steps = list(template.steps.order_by('order', 'pk'))
    if not steps:
        errors.append('Add at least one stage before publishing this template.')
        return PublishValidationResult(ok=False, errors=tuple(errors))

    orders = [step.order for step in steps]
    if len(orders) != len(set(orders)):
        errors.append('Stage order must be unique — resolve duplicate stage numbers.')

    unowned = [
        step for step in steps
        if step.step_kind == WorkflowTemplateStep.StepKind.APPROVAL
        and not (step.assignee_role or '').strip()
        and not step.specific_assignee_id
    ]
    if unowned:
        labels = ', '.join(step.name for step in unowned[:3])
        suffix = '…' if len(unowned) > 3 else ''
        errors.append(
            f'Assign an owner (role or user) to every approval stage ({labels}{suffix}).'
        )

    for step in steps:
        expression = (step.condition_expression or '').strip()
        if not expression:
            continue
        # Lightweight syntax check — full evaluation needs a contract context.
        if expression.count('(') != expression.count(')'):
            errors.append(f'Fix routing condition on stage “{step.name}” (unbalanced parentheses).')
        if any(token in expression for token in (';;', '===')):
            errors.append(f'Fix routing condition on stage “{step.name}” (invalid expression).')

    return PublishValidationResult(ok=not errors, errors=tuple(errors))


def _status_presentation(template: WorkflowTemplate) -> dict:
    if is_incomplete_template(template):
        return {
            'label': 'Draft · Incomplete',
            'tone': 'attention',
            'is_published': False,
            'is_incomplete': True,
        }
    if template.is_active:
        return {
            'label': 'Published',
            'tone': 'success',
            'is_published': True,
            'is_incomplete': False,
        }
    return {
        'label': 'Draft',
        'tone': 'neutral',
        'is_published': False,
        'is_incomplete': False,
    }


def _contract_type_label(template: WorkflowTemplate) -> str:
    if template.contract_type_id and getattr(template, 'contract_type', None):
        return template.contract_type.name
    return template.get_category_display()


def _stage_path(template: WorkflowTemplate, *, limit: int = 4) -> str:
    steps = list(template.steps.all()[: limit + 1]) if hasattr(template, '_prefetched_objects_cache') and 'steps' in getattr(template, '_prefetched_objects_cache', {}) else list(
        template.steps.order_by('order', 'pk')[: limit + 1]
    )
    if not steps:
        return 'No stages yet'
    visible = steps[:limit]
    path = ' → '.join(step.name for step in visible)
    if len(steps) > limit:
        path = f'{path} → +{len(steps) - limit}'
    return path


def _latest_audit(template: WorkflowTemplate) -> Optional[AuditLog]:
    return (
        AuditLog.objects.filter(
            Q(model_name='WorkflowTemplate', object_id=template.pk)
            | Q(changes__template_id=template.pk)
        )
        .select_related('user')
        .order_by('-timestamp', '-pk')
        .first()
    )


def _owner_label(template: WorkflowTemplate, latest_audit: Optional[AuditLog]) -> str:
    for step in template.steps.all()[:8]:
        if step.specific_assignee_id:
            user = step.specific_assignee
            return (user.get_full_name() or user.username).strip() or 'Assigned'
        if (step.assignee_role or '').strip():
            return step.get_assignee_role_display() if hasattr(step, 'get_assignee_role_display') else step.assignee_role
    if latest_audit and latest_audit.user_id:
        user = latest_audit.user
        return (user.get_full_name() or user.username).strip() or 'Workspace'
    if template.organization_id:
        return 'Workspace'
    return 'System'


def _has_unpublished_changes(template: WorkflowTemplate) -> bool:
    versions = list_template_versions(template)
    if len(versions) < 2:
        return is_incomplete_template(template) is False and not template.is_active and template_stage_count(template) > 0
    newest = versions[0]
    published = next((v for v in versions if v.is_active and not is_incomplete_template(v)), None)
    if published and newest.pk != published.pk and not newest.is_active:
        return True
    return (not template.is_active) and template_stage_count(template) > 0


def active_workflow_count_for_template(template: WorkflowTemplate) -> int:
    cached = getattr(template, 'active_workflow_count', None)
    if cached is not None:
        return int(cached)
    return Workflow.objects.filter(
        template=template,
        status=Workflow.Status.ACTIVE,
    ).count()


def build_template_card(template: WorkflowTemplate) -> dict:
    status = _status_presentation(template)
    latest_audit = _latest_audit(template)
    editor = '—'
    updated_at = template.created_at
    if latest_audit:
        updated_at = latest_audit.timestamp
        if latest_audit.user_id:
            editor = (latest_audit.user.get_full_name() or latest_audit.user.username).strip() or '—'
    return {
        'template': template,
        'name': template.name,
        'contract_type_label': _contract_type_label(template),
        'status_label': status['label'],
        'status_tone': status['tone'],
        'is_published': status['is_published'],
        'is_incomplete': status['is_incomplete'],
        'version_label': f'v{template.version}',
        'stage_path': _stage_path(template),
        'stage_count': template_stage_count(template),
        'owner_label': _owner_label(template, latest_audit),
        'updated_at': updated_at,
        'editor_label': editor,
        'active_workflow_count': active_workflow_count_for_template(template),
        'has_unpublished_changes': _has_unpublished_changes(template),
        'designer_url': reverse('contracts:workflow_template_detail', kwargs={'pk': template.pk}),
        'can_delete': bool(template.organization_id),
        'can_publish': validate_template_for_publish(template).ok and not template.is_active,
    }


def duplicate_workflow_template(template: WorkflowTemplate, *, name: Optional[str] = None) -> WorkflowTemplate:
    """Create an independent unpublished copy (not a version bump)."""
    copy_name = name or f'Copy of {template.name}'
    clone = WorkflowTemplate.objects.create(
        name=copy_name,
        description=template.description,
        organization=template.organization,
        category=template.category,
        contract_type=template.contract_type,
        version=1,
        parent_template=None,
        is_active=False,
    )
    for step in template.steps.order_by('order', 'pk'):
        WorkflowTemplateStep.objects.create(
            template=clone,
            name=step.name,
            description=step.description,
            order=step.order,
            estimated_duration=step.estimated_duration,
            step_kind=step.step_kind,
            condition_expression=step.condition_expression,
            assignee_role=step.assignee_role,
            specific_assignee=step.specific_assignee,
            sla_hours=step.sla_hours,
            escalation_after_hours=step.escalation_after_hours,
        )
    return clone


def filter_workflow_templates(queryset, *, q='', contract_type='', status='', owner='', sort='updated'):
    q = (q or '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(category__icontains=q)
            | Q(contract_type__name__icontains=q)
        )
    contract_type = (contract_type or '').strip()
    if contract_type:
        if contract_type.isdigit():
            queryset = queryset.filter(contract_type_id=int(contract_type))
        else:
            queryset = queryset.filter(category=contract_type)

    status = (status or '').strip().lower()
    queryset = queryset.annotate(step_count=Count('steps', distinct=True))
    if status == 'published':
        queryset = queryset.filter(is_active=True).exclude(step_count=0)
    elif status == 'draft':
        queryset = queryset.filter(Q(is_active=False) | Q(step_count=0))
    elif status == 'incomplete':
        queryset = queryset.filter(step_count=0)

    owner = (owner or '').strip()
    if owner == 'unassigned':
        queryset = queryset.exclude(
            steps__specific_assignee__isnull=False
        ).exclude(
            steps__assignee_role__gt=''
        ).distinct()
    elif owner == 'system':
        queryset = queryset.filter(organization__isnull=True)
    elif owner == 'workspace':
        queryset = queryset.filter(organization__isnull=False)

    sort = (sort or 'updated').strip().lower()
    if sort == 'name':
        queryset = queryset.order_by('name', '-version')
    elif sort == 'status':
        queryset = queryset.order_by('-is_active', 'name')
    elif sort == 'version':
        queryset = queryset.order_by('-version', 'name')
    else:
        queryset = queryset.order_by('-created_at', 'name')
    return queryset
