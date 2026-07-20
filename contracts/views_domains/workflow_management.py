from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Count, Max, Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from contracts.forms import WorkflowForm, WorkflowStepForm, WorkflowTemplateForm, WorkflowTemplatePreviewForm, WorkflowTemplateStepForm
from contracts.middleware import log_action
from contracts.models import (
    ApprovalRequest,
    ApprovalRoute,
    ApprovalRule,
    AuditLog,
    Contract,
    DraftDocument,
    FieldDefinition,
    FieldValue,
    RiskSignal,
    Workflow,
    WorkflowStep,
    WorkflowTemplate,
    WorkflowTemplateStep,
)
from contracts.permissions import ContractAction, can_access_contract_action
from contracts.tenancy import get_user_organization, scope_queryset_for_organization, set_organization_on_instance
from contracts.services.workflow_routing import build_approval_request_plan_for_contract, suggest_workflow_template_for_contract
from contracts.services.workflow_execution import advance_workflow_after_completion, materialize_workflow_from_template
from contracts.services.workflow_audit import (
    build_field_changes,
    get_workflow_audit_feed,
    get_workflow_template_audit_feed,
    log_workflow_created,
    log_workflow_preview_run,
    log_workflow_step_added,
    log_workflow_step_completed,
    log_workflow_step_escalated,
    log_workflow_step_updated,
    log_workflow_template_cloned,
    log_workflow_template_created,
    log_workflow_template_publish_toggled,
    log_workflow_template_reordered,
    log_workflow_template_restored,
    log_workflow_template_step_added,
    log_workflow_template_step_deleted,
    log_workflow_template_updated,
)
from contracts.services.workflow_simulation import simulate_workflow_template
from contracts.services.workflow_templates import COMPARISON_PRESETS, compare_template_versions, clone_template_version, list_template_versions
from contracts.services.workflow_designer import (
    build_template_card,
    duplicate_workflow_template,
    ensure_stepless_templates_unpublished,
    filter_workflow_templates,
    validate_template_for_publish,
    workflow_designer_tabs,
)
from contracts.view_support import (
    TenantAssignCreateMixin,
    apply_form_queryset_scopes,
    TenantScopedFormMixin,
    TenantScopedQuerysetMixin,
    configure_workflow_form as _configure_workflow_form,
    get_scoped_queryset_for_request,
    scope_workflow_steps_for_organization as _scope_workflow_steps_for_organization,
    scope_workflows_for_organization as _scope_workflows_for_organization,
    organization_user_queryset,
)


def _workflow_template_queryset_for_organization(organization):
    if organization is None:
        return WorkflowTemplate.objects.none()
    return (
        WorkflowTemplate.objects.filter(Q(organization=organization) | Q(organization__isnull=True))
        .distinct()
        .prefetch_related('steps')
    )


class WorkflowTemplateListView(TenantScopedQuerysetMixin, LoginRequiredMixin, ListView):
    model = WorkflowTemplate
    template_name = 'contracts/workflow_template_list.html'
    context_object_name = 'workflow_templates'

    def get_queryset(self):
        org = self.get_organization()
        return _workflow_template_queryset_for_organization(org)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_workflow_template_list_context(self.request, context['workflow_templates']))
        return context


def _workflow_template_list_context(request, templates_qs):
    organization = get_user_organization(request.user)
    ensure_stepless_templates_unpublished(templates_qs)
    params = request.GET
    filtered = filter_workflow_templates(
        templates_qs.select_related('contract_type').prefetch_related('steps', 'steps__specific_assignee'),
        q=params.get('q', ''),
        contract_type=params.get('contract_type', ''),
        status=params.get('status', ''),
        owner=params.get('owner', ''),
        sort=params.get('sort', 'updated'),
    )
    filtered = filtered.annotate(
        active_workflow_count=Count(
            'workflow',
            filter=Q(workflow__status=Workflow.Status.ACTIVE),
            distinct=True,
        ),
    )
    templates = list(filtered)
    cards = [build_template_card(template) for template in templates]
    filter_q = (params.get('q') or '').strip()
    filter_contract_type = (params.get('contract_type') or '').strip()
    filter_status = (params.get('status') or '').strip()
    filter_owner = (params.get('owner') or '').strip()
    filter_sort = (params.get('sort') or 'updated').strip()
    more_filters_active = bool(
        filter_contract_type
        or filter_status
        or filter_owner
        or (filter_sort and filter_sort != 'updated')
    )
    return {
        'workflow_templates': templates,
        'template_cards': cards,
        'result_count': len(cards),
        'designer_tabs': workflow_designer_tabs(active='templates'),
        'filter_q': filter_q,
        'filter_contract_type': filter_contract_type,
        'filter_status': filter_status,
        'filter_owner': filter_owner,
        'filter_sort': filter_sort,
        'more_filters_active': more_filters_active,
        'category_choices': WorkflowTemplate.Category.choices,
        'hide_app_footer': True,
        'organization': organization,
    }


@login_required
def workflow_template_list(request):
    templates = _workflow_template_queryset_for_organization(get_user_organization(request.user))
    return render(request, 'contracts/workflow_template_list.html', _workflow_template_list_context(request, templates))


@login_required
def workflow_approval_route_list(request):
    organization = get_user_organization(request.user)
    template_qs = _workflow_template_queryset_for_organization(organization)
    routes = (
        ApprovalRoute.objects.filter(workflow_template__in=template_qs)
        .select_related('workflow_template')
        .order_by('workflow_template__name', 'order', 'pk')
    )
    return render(request, 'contracts/workflow_approval_route_list.html', {
        'approval_routes': routes,
        'designer_tabs': workflow_designer_tabs(active='approval_rules'),
        'result_count': routes.count(),
        'hide_app_footer': True,
    })


@login_required
def workflow_designer_history(request):
    organization = get_user_organization(request.user)
    template_ids = list(
        _workflow_template_queryset_for_organization(organization).values_list('pk', flat=True)
    )
    logs = (
        AuditLog.objects.filter(
            Q(model_name='WorkflowTemplate', object_id__in=template_ids)
            | Q(model_name='WorkflowTemplateStep', changes__template_id__in=template_ids)
            | Q(changes__event__startswith='workflow_template', changes__template_id__in=template_ids)
        )
        .select_related('user')
        .order_by('-timestamp', '-pk')[:100]
    )
    from contracts.services.workflow_audit import build_audit_feed
    return render(request, 'contracts/workflow_designer_history.html', {
        'audit_feed': build_audit_feed(logs),
        'designer_tabs': workflow_designer_tabs(active='history'),
        'hide_app_footer': True,
    })


class WorkflowTemplateDetailView(TenantScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = WorkflowTemplate
    template_name = 'contracts/workflow_template_detail.html'
    context_object_name = 'workflow_template'

    def get_queryset(self):
        return _workflow_template_queryset_for_organization(self.get_organization())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = WorkflowTemplateStep.objects.filter(template=self.object).order_by('order')
        context['template_versions'] = list_template_versions(self.object)
        context['step_form'] = apply_form_queryset_scopes(
            WorkflowTemplateStepForm(),
            self.get_organization(),
            {'specific_assignee': organization_user_queryset},
        )
        context['preview_form'] = WorkflowTemplatePreviewForm()
        context['preview_result'] = None
        context['step_controls'] = _build_template_step_controls(context['steps'])
        context['workflow_template_audit_feed'] = get_workflow_template_audit_feed(self.object, limit=6)
        context['workflow_template_activity_url'] = reverse_lazy('contracts:workflow_template_activity', kwargs={'pk': self.object.pk})
        return context


class WorkflowTemplateCompareView(TenantScopedQuerysetMixin, LoginRequiredMixin, View):
    template_name = 'contracts/workflow_template_compare.html'

    def get(self, request, pk, other_pk):
        template_qs = _workflow_template_queryset_for_organization(self.get_organization())
        left_template = get_object_or_404(template_qs, pk=pk)
        right_template = get_object_or_404(template_qs, pk=other_pk)
        preset = request.GET.get('preset', 'full')
        comparison = compare_template_versions(left_template, right_template, preset=preset)
        return render(request, self.template_name, {'comparison': comparison, 'comparison_presets': COMPARISON_PRESETS})


class WorkflowTemplateCreateView(TenantAssignCreateMixin, LoginRequiredMixin, CreateView):
    model = WorkflowTemplate
    form_class = WorkflowTemplateForm
    template_name = 'contracts/workflow_template_form.html'
    success_url = reverse_lazy('contracts:workflow_template_list')

    def form_valid(self, form):
        set_organization_on_instance(form.instance, self.get_organization())
        response = super().form_valid(form)
        log_workflow_template_created(self.object, self.request.user, request=self.request)
        return response


class WorkflowTemplateUpdateView(TenantScopedQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = WorkflowTemplate
    form_class = WorkflowTemplateForm
    template_name = 'contracts/workflow_template_form.html'
    success_url = reverse_lazy('contracts:workflow_template_list')

    def get_queryset(self):
        return _workflow_template_queryset_for_organization(self.get_organization())

    def get_success_url(self):
        return reverse_lazy('contracts:workflow_template_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        original_template = WorkflowTemplate.objects.filter(pk=self.get_object().pk).first()
        response = super().form_valid(form)
        changes = build_field_changes(original_template, self.object, ['name', 'description', 'category'])
        if changes:
            log_workflow_template_updated(self.object, self.request.user, changes, request=self.request)
        return response


class WorkflowListView(TenantScopedQuerysetMixin, LoginRequiredMixin, ListView):
    model = Workflow
    template_name = 'contracts/workflow_dashboard.html'
    context_object_name = 'workflows'

    def get_queryset(self):
        org = self.get_organization()
        queryset = scope_queryset_for_organization(Workflow.objects.all(), org)
        contract_pk = self.request.GET.get('contract_pk')
        if contract_pk:
            queryset = queryset.filter(contract=contract_pk)
        return queryset.order_by('-created_at')


class WorkflowDetailView(TenantScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = Workflow
    template_name = 'contracts/workflow_detail.html'
    context_object_name = 'workflow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = WorkflowStep.objects.filter(workflow=self.object).order_by('order')
        context['step_form'] = apply_form_queryset_scopes(WorkflowStepForm(), self.get_organization(), {'assigned_to': organization_user_queryset})
        context['workflow_audit_feed'] = get_workflow_audit_feed(self.object, limit=6)
        context['workflow_activity_url'] = reverse_lazy('contracts:workflow_activity', kwargs={'pk': self.object.pk})
        return context


class WorkflowCreateView(TenantAssignCreateMixin, LoginRequiredMixin, CreateView):
    model = Workflow
    form_class = WorkflowForm
    template_name = 'contracts/workflow_form.html'

    def get_success_url(self):
        return reverse_lazy('contracts:workflow_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form is not None:
            context.update(_build_workflow_editor_context(form, self.get_organization()))
        return context

    def form_valid(self, form):
        set_organization_on_instance(form.instance, get_user_organization(self.request.user))
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        if self.object.contract and not self.object.template_id:
            self.object.template = suggest_workflow_template_for_contract(self.object.contract)
            self.object.save(update_fields=['template'])
        if self.object.contract:
            from contracts.models import ApprovalRequest

            if not ApprovalRequest.objects.filter(contract=self.object.contract, status=ApprovalRequest.Status.PENDING).exists():
                for plan_item in build_approval_request_plan_for_contract(self.object.contract):
                    ApprovalRequest.objects.get_or_create(
                        organization=plan_item['organization'],
                        contract=plan_item['contract'],
                        rule=plan_item['rule'],
                        approval_step=plan_item['approval_step'],
                        defaults={
                            'assigned_to': plan_item['assigned_to'],
                            'due_date': plan_item['due_date'],
                            'status': plan_item['status'],
                        },
                    )
        log_workflow_created(self.object, self.request.user, request=self.request)
        return response


class WorkflowUpdateView(TenantScopedFormMixin, TenantScopedQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = Workflow
    form_class = WorkflowForm
    template_name = 'contracts/workflow_form.html'
    scoped_form_fields = {'contract': Contract}

    def get_success_url(self):
        return reverse_lazy('contracts:workflow_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context.get('form')
        if form is not None:
            context.update(_build_workflow_editor_context(form, self.get_organization()))
        return context


class WorkflowStepUpdateView(TenantScopedFormMixin, TenantScopedQuerysetMixin, LoginRequiredMixin, UpdateView):
    model = WorkflowStep
    form_class = WorkflowStepForm
    template_name = 'contracts/workflow_step_form.html'
    scoped_form_fields = {'assigned_to': organization_user_queryset}

    def get_success_url(self):
        return reverse_lazy('contracts:workflow_detail', kwargs={'pk': self.object.workflow.pk})

    def form_valid(self, form):
        current_step = self.get_object()
        before_step = WorkflowStep.objects.filter(pk=current_step.pk).first()
        new_status = form.cleaned_data.get('status', current_step.status)
        if not current_step.can_transition_to(new_status):
            form.add_error('status', 'Invalid workflow step transition.')
            return self.form_invalid(form)

        response = super().form_valid(form)
        if new_status == WorkflowStep.Status.COMPLETED:
            self.object.completed_at = timezone.now()
            self.object.save(update_fields=['completed_at'])
            advance_workflow_after_completion(self.object)
        elif new_status == WorkflowStep.Status.ESCALATED:
            self.object.escalated_at = timezone.now()
            self.object.save(update_fields=['escalated_at'])
        changes = build_field_changes(before_step, self.object, ['name', 'description', 'status', 'assigned_to', 'due_date', 'order'])
        if new_status == WorkflowStep.Status.COMPLETED:
            log_workflow_step_completed(
                self.object,
                self.request.user,
                request=self.request,
                previous_status=before_step.status if before_step else None,
                extra_changes=[change for change in changes if change.get('field') != 'status'],
            )
        elif new_status == WorkflowStep.Status.ESCALATED:
            log_workflow_step_escalated(
                self.object,
                self.request.user,
                request=self.request,
                extra_changes=[change for change in changes if change.get('field') != 'status'],
            )
        elif changes:
            log_workflow_step_updated(self.object, self.request.user, changes, request=self.request)
        return response


class WorkflowStepCompleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        organization = get_user_organization(request.user)
        step = get_object_or_404(_scope_workflow_steps_for_organization(organization), pk=pk)
        linked_contract = step.workflow.contract
        if linked_contract and not can_access_contract_action(request.user, linked_contract, ContractAction.EDIT):
            return HttpResponseForbidden('You do not have permission to complete this contract workflow step.')
        previous_status = step.status
        step.status = 'COMPLETED'
        step.completed_at = timezone.now()
        step.save()
        advance_workflow_after_completion(step)
        log_workflow_step_completed(step, request.user, request=request, previous_status=previous_status)
        return redirect('contracts:workflow_detail', pk=step.workflow.pk)


class AddWorkflowStepView(LoginRequiredMixin, View):
    def post(self, request, pk):
        organization = get_user_organization(request.user)
        workflow = get_object_or_404(_scope_workflows_for_organization(organization), pk=pk)
        if workflow.contract and not can_access_contract_action(request.user, workflow.contract, ContractAction.EDIT):
            return HttpResponseForbidden('You do not have permission to create workflow steps for this contract.')
        form = apply_form_queryset_scopes(WorkflowStepForm(request.POST), organization, {'assigned_to': organization_user_queryset})
        if form.is_valid():
            step = form.save(commit=False)
            step.workflow = workflow
            if step.order is None:
                max_order = WorkflowStep.objects.filter(workflow=workflow).aggregate(max_order=Max('order'))['max_order'] or 0
                step.order = max_order + 1
            step.save()
            log_workflow_step_added(step, request.user, request=request)
            messages.success(request, f"Added step '{step.name}' to {workflow.title}.")
            return redirect('contracts:workflow_detail', pk=workflow.pk)
        return render(request, 'contracts/workflow_detail.html', _workflow_detail_context(workflow, add_step_form=form))


class AddWorkflowTemplateStepView(LoginRequiredMixin, View):
    def post(self, request, pk):
        organization = get_user_organization(request.user)
        template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
        form = apply_form_queryset_scopes(WorkflowTemplateStepForm(request.POST), organization, {'specific_assignee': organization_user_queryset})
        if form.is_valid():
            step = form.save(commit=False)
            step.template = template
            if step.order is None:
                max_order = WorkflowTemplateStep.objects.filter(template=template).aggregate(max_order=Max('order'))['max_order'] or 0
                step.order = max_order + 1
            step.save()
            log_workflow_template_step_added(step, request.user, request=request)
            messages.success(request, f"Added step '{step.name}' to {template.name}.")
            return redirect('contracts:workflow_template_detail', pk=template.pk)

        return render(
            request,
            'contracts/workflow_template_detail.html',
            _workflow_template_detail_context(template, organization, step_form=form),
        )


@login_required
@require_POST
def workflow_template_step_delete(request, pk, step_pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    step = get_object_or_404(WorkflowTemplateStep.objects.select_related('template'), pk=step_pk, template=template)
    deleted_step_data = {
        'step_id': step.pk,
        'step_name': step.name,
        'order': step.order,
        'step_kind': step.step_kind,
        'condition_expression': step.condition_expression,
        'assignee_role': step.assignee_role or None,
        'specific_assignee_id': step.specific_assignee_id,
        'sla_hours': step.sla_hours,
        'escalation_after_hours': step.escalation_after_hours,
    }
    step.delete()
    log_workflow_template_step_deleted(deleted_step_data, template, request.user, request=request)
    messages.success(request, f"Deleted step '{deleted_step_data['step_name']}' from {template.name}.")
    return redirect('contracts:workflow_template_detail', pk=template.pk)


@login_required
@require_POST
def workflow_template_step_reorder(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    raw_step_ids = request.POST.getlist('step_ids')
    if len(raw_step_ids) == 1 and ',' in raw_step_ids[0]:
        raw_step_ids = [item for item in raw_step_ids[0].split(',') if item]
    if not raw_step_ids:
        messages.error(request, 'Provide an ordered list of step IDs.')
        return redirect('contracts:workflow_template_detail', pk=template.pk)

    try:
        ordered_step_ids = [int(step_id) for step_id in raw_step_ids]
    except ValueError:
        messages.error(request, 'Invalid step ordering payload.')
        return redirect('contracts:workflow_template_detail', pk=template.pk)

    steps = list(WorkflowTemplateStep.objects.filter(template=template))
    step_map = {step.pk: step for step in steps}
    if len(ordered_step_ids) != len(steps) or set(ordered_step_ids) != set(step_map):
        messages.error(request, 'Step ordering must include every step exactly once.')
        return redirect('contracts:workflow_template_detail', pk=template.pk)

    ordered_steps = [step_map[step_id] for step_id in ordered_step_ids]
    before_orders = {step.pk: step.order for step in steps}
    for index, step in enumerate(ordered_steps, start=1):
        step.order = index
    WorkflowTemplateStep.objects.bulk_update(ordered_steps, ['order'])
    log_workflow_template_reordered(
        template,
        request.user,
        changes=[
            {
                'field': f"order[{step.name}]",
                'step_id': step.pk,
                'step_name': step.name,
                'from': before_orders.get(step.pk),
                'to': step.order,
            }
            for step in ordered_steps
            if before_orders.get(step.pk) != step.order
        ],
        request=request,
    )
    messages.success(request, f'Updated step order for {template.name}.')
    return redirect('contracts:workflow_template_detail', pk=template.pk)


@login_required
@require_POST
def workflow_template_publish_toggle(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    # Publishing requires stages + valid routing/owners; unpublish always allowed.
    if not template.is_active:
        validation = validate_template_for_publish(template)
        if not validation.ok:
            messages.error(request, validation.message)
            return redirect('contracts:workflow_template_detail', pk=template.pk)

    old_status = template.is_active
    template.is_active = not template.is_active
    template.save(update_fields=['is_active'])
    log_workflow_template_publish_toggled(template, request.user, old_status, template.is_active, request=request)
    messages.success(
        request,
        f"{'Published' if template.is_active else 'Unpublished'} workflow template {template.name}.",
    )
    return redirect('contracts:workflow_template_detail', pk=template.pk)


@login_required
def workflow_dashboard(request):
    from django.urls import reverse

    from contracts.services.workflow_operations import (
        active_workflow_count,
        annotate_workflow_operations_queryset,
        build_workflow_operations_rows,
        clear_filters_url,
        filter_workflow_operations_queryset,
        pending_approval_count,
        workflow_operations_tabs,
        WorkflowOperationsFilters,
    )
    from contracts.view_support import organization_user_queryset

    organization = get_user_organization(request.user)
    filters = WorkflowOperationsFilters.from_request(request)
    base_qs = annotate_workflow_operations_queryset(
        get_scoped_queryset_for_request(request, Workflow).order_by('-created_at')
    )
    active_count = active_workflow_count(base_qs)
    pending_approvals = pending_approval_count(organization)
    filtered_qs = filter_workflow_operations_queryset(base_qs, filters)
    workflow_rows = build_workflow_operations_rows(
        filtered_qs[:200],
        exception_only=filters.exception_only,
    )
    ops_url = reverse('contracts:workflow_dashboard')
    context = {
        'workflow_rows': workflow_rows,
        'workflows': filtered_qs,  # compatibility for existing callers/tests
        'filters': filters,
        'filters_active': filters.active,
        'more_filters_active': filters.more_filters_active,
        'active_workflow_count': active_count,
        'pending_approval_count': pending_approvals,
        'status_filter_choices': Workflow.Status.choices,
        'contract_type_choices': Contract.ContractType.choices,
        'owner_choices': list(organization_user_queryset(organization)) if organization else [],
        'ops_tabs': workflow_operations_tabs(active='active'),
        'ops_clear_url': clear_filters_url(ops_url),
        'workflow_create_url': reverse('contracts:workflow_create'),
        'approval_rules_url': reverse_lazy('contracts:approval_rule_list'),
        'approval_requests_url': reverse_lazy('contracts:approval_request_list'),
        'hide_app_footer': True,
    }
    return render(request, 'contracts/workflow_dashboard.html', context)


@login_required
def workflow_create(request):
    organization = get_user_organization(request.user)
    if request.method == 'POST':
        form = _configure_workflow_form(WorkflowForm(request.POST), organization)
        if form.is_valid():
            workflow = form.save(commit=False)
            if workflow.contract and not can_access_contract_action(request.user, workflow.contract, ContractAction.EDIT):
                return HttpResponseForbidden('You do not have permission to create workflows for this contract.')
            set_organization_on_instance(workflow, organization)
            workflow.created_by = request.user
            workflow.save()
            if workflow.contract and not workflow.template_id:
                workflow.template = suggest_workflow_template_for_contract(workflow.contract)
                workflow.save(update_fields=['template'])
            materialize_workflow_from_template(workflow)
            log_workflow_created(workflow, request.user, request=request)
            if workflow.contract:
                from contracts.models import ApprovalRequest

                if not ApprovalRequest.objects.filter(contract=workflow.contract, status=ApprovalRequest.Status.PENDING).exists():
                    for plan_item in build_approval_request_plan_for_contract(workflow.contract):
                        ApprovalRequest.objects.get_or_create(
                            organization=plan_item['organization'],
                            contract=plan_item['contract'],
                            rule=plan_item['rule'],
                            approval_step=plan_item['approval_step'],
                            defaults={
                                'assigned_to': plan_item['assigned_to'],
                                'due_date': plan_item['due_date'],
                                'status': plan_item['status'],
                            },
                        )
            return redirect('contracts:workflow_detail', pk=workflow.pk)
    else:
        form = _configure_workflow_form(WorkflowForm(), organization)
        contract_pk = request.GET.get('contract_pk')
        template_pk = request.GET.get('template_pk')
        if contract_pk:
            form.initial['contract'] = contract_pk
        if template_pk:
            form.initial['template'] = template_pk
    context = {'form': form}
    context.update(_build_workflow_editor_context(form, organization))
    return render(request, 'contracts/workflow_form.html', context)


@login_required
def workflow_detail(request, pk):
    organization = get_user_organization(request.user)
    workflow = get_object_or_404(_scope_workflows_for_organization(organization), pk=pk)
    if workflow.contract and not can_access_contract_action(request.user, workflow.contract, ContractAction.COMMENT):
        return HttpResponseForbidden('You do not have access to this contract workflow.')
    return render(request, 'contracts/workflow_detail.html', _workflow_detail_context(workflow, actor=request.user))


@login_required
def workflow_activity(request, pk):
    organization = get_user_organization(request.user)
    workflow = get_object_or_404(_scope_workflows_for_organization(organization), pk=pk)
    if workflow.contract and not can_access_contract_action(request.user, workflow.contract, ContractAction.COMMENT):
        return HttpResponseForbidden('You do not have access to this contract workflow.')
    return render(
        request,
        'contracts/activity_timeline.html',
        {
            'page_title': f'{workflow.title} Activity',
            'page_subtitle': 'Workflow event history and compliance trail.',
            'workflow': workflow,
            'workflow_steps': WorkflowStep.objects.filter(workflow=workflow).order_by('order'),
            'audit_feed': get_workflow_audit_feed(workflow, limit=50),
            'back_url': reverse_lazy('contracts:workflow_detail', kwargs={'pk': workflow.pk}),
        },
    )


@login_required
def update_workflow_step(request, pk):
    organization = get_user_organization(request.user)
    step = get_object_or_404(_scope_workflow_steps_for_organization(organization), pk=pk)
    linked_contract = step.workflow.contract
    if linked_contract and not can_access_contract_action(request.user, linked_contract, ContractAction.EDIT):
        return HttpResponseForbidden('You do not have permission to update this contract workflow step.')
    if request.method == 'POST':
        before_step = WorkflowStep.objects.filter(pk=step.pk).first()
        new_status = request.POST.get('status', step.status)
        if not step.can_transition_to(new_status):
            messages.error(request, 'Invalid workflow step transition.')
            return redirect('contracts:workflow_detail', pk=step.workflow.pk)

        step.status = new_status
        description = request.POST.get('description', '').strip()
        if description:
            step.description = description
        update_fields = ['status', 'description']
        if new_status == 'COMPLETED':
            step.completed_at = timezone.now()
            update_fields.append('completed_at')
        elif new_status == 'ESCALATED':
            step.escalated_at = timezone.now()
            update_fields.append('escalated_at')
        step.save(update_fields=update_fields)
        changes = build_field_changes(before_step, step, ['name', 'description', 'status', 'assigned_to', 'due_date', 'order'])
        if new_status == 'COMPLETED':
            advance_workflow_after_completion(step)
            log_workflow_step_completed(
                step,
                request.user,
                request=request,
                previous_status=before_step.status if before_step else None,
                extra_changes=[change for change in changes if change.get('field') != 'status'],
            )
        elif new_status == 'ESCALATED':
            log_workflow_step_escalated(
                step,
                request.user,
                request=request,
                extra_changes=[change for change in changes if change.get('field') != 'status'],
            )
        elif changes:
            log_workflow_step_updated(step, request.user, changes, request=request)
        return redirect('contracts:workflow_detail', pk=step.workflow.pk)
    return redirect('contracts:workflow_detail', pk=step.workflow.pk)


@login_required
def workflow_template_create(request):
    organization = get_user_organization(request.user)
    template_qs = _workflow_template_queryset_for_organization(organization)
    if request.method == 'POST':
        form = WorkflowTemplateForm(request.POST, template_queryset=template_qs)
        if form.is_valid():
            source_mode = form.cleaned_data.get('source_mode') or 'blank'
            source_template = form.cleaned_data.get('source_template')
            if source_mode == 'duplicate' and source_template:
                template = duplicate_workflow_template(
                    source_template,
                    name=form.cleaned_data['name'],
                )
                template.description = form.cleaned_data.get('description') or template.description
                template.category = form.cleaned_data.get('category') or template.category
                template.contract_type = form.cleaned_data.get('contract_type') or template.contract_type
                set_organization_on_instance(template, organization)
                template.is_active = False
                template.save()
            else:
                template = form.save(commit=False)
                set_organization_on_instance(template, organization)
                # Sub-block D4: a template created through this form has zero
                # steps by definition. Force unpublished at creation.
                template.is_active = False
                template.save()
            log_workflow_template_created(template, request.user, request=request)
            messages.info(
                request,
                f'"{template.name}" was created as a draft. Configure stages in Workflow Designer, then publish.',
            )
            return redirect('contracts:workflow_template_detail', pk=template.pk)
    else:
        form = WorkflowTemplateForm(template_queryset=template_qs)
    return render(request, 'contracts/workflow_template_form.html', {
        'form': form,
        'designer_tabs': workflow_designer_tabs(active='templates'),
        'hide_app_footer': True,
    })


@login_required
@require_POST
def workflow_template_duplicate(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    clone = duplicate_workflow_template(template)
    set_organization_on_instance(clone, organization or template.organization)
    clone.save(update_fields=['organization'])
    log_workflow_template_created(clone, request.user, request=request)
    messages.success(request, f'Duplicated “{template.name}” as “{clone.name}”.')
    return redirect('contracts:workflow_template_detail', pk=clone.pk)


@login_required
@require_POST
def workflow_template_archive(request, pk):
    """Archive = unpublish. Zero-stage templates stay Draft · Incomplete."""
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    if not template.is_active:
        messages.info(request, f'“{template.name}” is already unpublished.')
        return redirect('contracts:workflow_template_list')
    old_status = template.is_active
    template.is_active = False
    template.save(update_fields=['is_active'])
    log_workflow_template_publish_toggled(template, request.user, old_status, template.is_active, request=request)
    messages.success(request, f'Archived workflow template {template.name}.')
    return redirect('contracts:workflow_template_list')


@login_required
@require_POST
def workflow_template_delete(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    if not template.organization_id or (organization and template.organization_id != organization.id):
        messages.error(request, 'System templates cannot be deleted. Duplicate them instead.')
        return redirect('contracts:workflow_template_detail', pk=template.pk)
    if Workflow.objects.filter(template=template, status=Workflow.Status.ACTIVE).exists():
        messages.error(request, 'Cannot delete a template with active workflows. Archive it instead.')
        return redirect('contracts:workflow_template_detail', pk=template.pk)
    name = template.name
    template_id = template.pk
    template.delete()
    log_action(
        request.user,
        AuditLog.Action.DELETE,
        'WorkflowTemplate',
        object_id=template_id,
        object_repr=name,
        changes={'event': 'workflow_template_deleted', 'template_id': template_id, 'template_name': name},
        request=request,
    )
    messages.success(request, f'Deleted workflow template {name}.')
    return redirect('contracts:workflow_template_list')


@login_required
def workflow_template_activity(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    return render(
        request,
        'contracts/activity_timeline.html',
        {
            'page_title': f'{template.name} Activity',
            'page_subtitle': 'Template event history and compliance trail.',
            'workflow_template': template,
            'steps': WorkflowTemplateStep.objects.filter(template=template).order_by('order'),
            'audit_feed': get_workflow_template_audit_feed(template, limit=50),
            'back_url': reverse_lazy('contracts:workflow_template_detail', kwargs={'pk': template.pk}),
        },
    )


@login_required
def workflow_template_detail(request, pk):
    template = get_object_or_404(_workflow_template_queryset_for_organization(get_user_organization(request.user)), pk=pk)
    return render(
        request,
        'contracts/workflow_template_detail.html',
        _workflow_template_detail_context(template, get_user_organization(request.user)),
    )


@login_required
@require_POST
def workflow_template_preview(request, pk):
    organization = get_user_organization(request.user)
    template = get_object_or_404(_workflow_template_queryset_for_organization(organization), pk=pk)
    form = WorkflowTemplatePreviewForm(request.POST)
    context = _workflow_template_detail_context(template, organization, step_form=None)
    context['preview_form'] = form
    if form.is_valid():
        preview_result = simulate_workflow_template(
            template,
            form.cleaned_data,
            organization=organization,
            user=request.user,
        )
        context['preview_result'] = preview_result
        log_workflow_preview_run(
            template,
            request.user,
            {
                'contract_type': form.cleaned_data.get('contract_type'),
                'value': str(form.cleaned_data.get('value')) if form.cleaned_data.get('value') is not None else None,
                'jurisdiction': form.cleaned_data.get('jurisdiction'),
                'governing_law': form.cleaned_data.get('governing_law'),
                'data_transfer_flag': form.cleaned_data.get('data_transfer_flag'),
                'risk_level': form.cleaned_data.get('risk_level'),
                'counterparty_name': form.cleaned_data.get('counterparty_name'),
                'status': form.cleaned_data.get('status'),
                'active_step_count': preview_result.active_step_count,
                'skipped_step_count': preview_result.skipped_step_count,
            },
            request=request,
        )
    else:
        context['preview_result'] = None
    return render(request, 'contracts/workflow_template_detail.html', context)


@login_required
def workflow_template_clone_version(request, pk):
    template = get_object_or_404(_workflow_template_queryset_for_organization(get_user_organization(request.user)), pk=pk)
    if request.method != 'POST':
        return redirect('contracts:workflow_template_detail', pk=template.pk)

    cloned_template = clone_template_version(template)
    log_workflow_template_cloned(template, cloned_template, request.user, request=request)
    messages.success(request, f'Created workflow template version {cloned_template.version}.')
    return redirect('contracts:workflow_template_detail', pk=cloned_template.pk)


@login_required
def workflow_template_restore_version(request, pk):
    template = get_object_or_404(_workflow_template_queryset_for_organization(get_user_organization(request.user)), pk=pk)
    if request.method != 'POST':
        return redirect('contracts:workflow_template_detail', pk=template.pk)

    restored_template = clone_template_version(template, is_active=True)
    log_workflow_template_restored(template, restored_template, request.user, request=request)
    messages.success(request, f'Restored workflow template version {template.version} as version {restored_template.version}.')
    return redirect('contracts:workflow_template_detail', pk=restored_template.pk)


@login_required
def workflow_template_compare(request, pk, other_pk):
    organization = get_user_organization(request.user)
    template_qs = _workflow_template_queryset_for_organization(organization)
    left_template = get_object_or_404(template_qs, pk=pk)
    right_template = get_object_or_404(template_qs, pk=other_pk)
    preset = request.GET.get('preset', 'full')
    comparison = compare_template_versions(left_template, right_template, preset=preset)
    return render(request, 'contracts/workflow_template_compare.html', {'comparison': comparison, 'comparison_presets': COMPARISON_PRESETS})


def _build_template_step_controls(steps):
    step_list = list(steps)
    ordered_ids = [step.pk for step in step_list]
    controls = []
    for index, step in enumerate(step_list):
        move_up_ids = None
        move_down_ids = None
        if index > 0:
            move_up_ids = ordered_ids.copy()
            move_up_ids[index - 1], move_up_ids[index] = move_up_ids[index], move_up_ids[index - 1]
        if index < len(step_list) - 1:
            move_down_ids = ordered_ids.copy()
            move_down_ids[index], move_down_ids[index + 1] = move_down_ids[index + 1], move_down_ids[index]
        controls.append({
            'step': step,
            'move_up_ids': move_up_ids,
            'move_down_ids': move_down_ids,
        })
    return controls


def _workflow_is_dpa(workflow):
    return bool(
        workflow
        and workflow.contract
        and workflow.contract.contract_type == Contract.ContractType.DPA
        and workflow.template
        and workflow.template.name == 'DPA Privacy Review Workflow'
    )


def _workflow_is_msa(workflow):
    return bool(
        workflow
        and workflow.contract
        and workflow.contract.contract_type == Contract.ContractType.MSA
        and workflow.template
        and workflow.template.name == 'MSA Commercial Review Workflow'
    )


def _workflow_is_nda(workflow):
    return bool(
        workflow
        and workflow.contract
        and workflow.contract.contract_type == Contract.ContractType.NDA
        and workflow.template
        and workflow.template.name == 'NDA Self-Serve Workflow'
    )


def _field_values_by_key(workflow):
    values = {}
    qs = FieldValue.objects.filter(workflow=workflow).select_related('field_definition')
    for field_value in qs:
        values[field_value.field_definition.key] = field_value.value
    return values


def _risk_level_for_signals(signals):
    rank = {
        RiskSignal.Severity.LOW: 1,
        RiskSignal.Severity.MEDIUM: 2,
        RiskSignal.Severity.HIGH: 3,
        RiskSignal.Severity.CRITICAL: 4,
    }
    if not signals:
        return 'Low'
    return max(signals, key=lambda s: rank.get(s.severity, 0)).get_severity_display()


def _risk_detail_for_signal(signal):
    details = {
        'dpa_review_required': {
            'title': 'Personal data processing review',
            'source': 'AI Smart Questions · Personal data involved',
            'recommended_action': 'Confirm processing purpose, categories of data, and controller/processor posture.',
            'approval_impact': 'Legal review required; DPO visibility retained.',
            'section_anchor': 'processing-details',
        },
        'scc_transfer_review': {
            'title': 'EEA/SCC risk',
            'source': 'AI Smart Questions · Data leaves EEA',
            'recommended_action': 'Insert or confirm approved SCC transfer fallback and transfer mechanism.',
            'approval_impact': 'DPO approval required before signature.',
            'section_anchor': 'international-transfers',
        },
        'cross_border_no_mechanism': {
            'title': 'Missing transfer mechanism',
            'source': 'Risk checks · Cross-border transfer mechanism',
            'recommended_action': 'Select SCC, BCR, adequacy decision, or document accepted risk.',
            'approval_impact': 'DPO approval required; Legal cannot clear signature until resolved.',
            'section_anchor': 'international-transfers',
        },
        'subprocessor_review': {
            'title': 'Subprocessor review',
            'source': 'AI Smart Questions · Subprocessors involved',
            'recommended_action': 'Review approved subprocessor flow-down clause and notice position.',
            'approval_impact': 'Legal review required; DPO informed if transfer posture changes.',
            'section_anchor': 'subprocessors',
        },
        'subprocessors_undisclosed': {
            'title': 'Subprocessor fallback missing',
            'source': 'Legal Position · Fallback liability position',
            'recommended_action': 'Capture fallback liability and subprocessor notice position.',
            'approval_impact': 'Legal review required before approval route can advance.',
            'section_anchor': 'subprocessors',
        },
        'missing_dpo_contact': {
            'title': 'Missing DPO contact',
            'source': 'AI Smart Questions · DPO contact',
            'recommended_action': 'Add the privacy contact or confirm no named DPO is required.',
            'approval_impact': 'DPO approval may be delayed until ownership is clear.',
            'section_anchor': 'processing-details',
        },
        'breach_window_too_long': {
            'title': 'Breach notice window review',
            'source': 'AI Smart Questions · Breach notification window',
            'recommended_action': 'Align breach notification timing to the approved DPA playbook.',
            'approval_impact': 'Legal review required for any non-standard window.',
            'section_anchor': 'breach-notification',
        },
        'special_categories_risk': {
            'title': 'Special categories risk',
            'source': 'AI Smart Questions · Special categories of data',
            'recommended_action': 'Confirm the lawful basis and additional safeguards for special category data.',
            'approval_impact': 'Legal and DPO approval required before signature.',
            'section_anchor': 'processing-details',
        },
        'privacy_fact_uncertain': {
            'title': 'Privacy fact needs confirmation',
            'source': 'DPA intake · Operational fact marked Not sure',
            'recommended_action': 'Privacy and the DPO must confirm the processing or subprocessor position before approval.',
            'approval_impact': 'Blocked from approval and signature until Privacy and DPO review is complete.',
            'section_anchor': 'subprocessors',
        },
        'scc_fallback_included': {
            'title': 'SCC fallback language included',
            'source': 'AI Smart Questions · SCC fallback language',
            'recommended_action': 'Confirm the approved SCC fallback clause matches the current playbook version.',
            'approval_impact': 'DPO informed; no additional approval beyond the standard transfer review.',
            'section_anchor': 'international-transfers',
        },
    }
    fallback = {
        'title': signal.description,
        'source': 'DPA risk checks',
        'recommended_action': 'Review against the approved DPA playbook.',
        'approval_impact': 'Legal review required.',
        'section_anchor': 'processing-details',
    }
    data = details.get(signal.code, fallback)
    return {
        'title': data['title'],
        'severity': signal.get_severity_display(),
        'severity_code': signal.severity.lower(),
        'reason': signal.description,
        'source': data['source'],
        'recommended_action': data['recommended_action'],
        'approval_impact': data['approval_impact'],
        'status': 'Open' if not signal.is_resolved else 'Resolved',
        'section_anchor': data['section_anchor'],
    }


def _dpa_approval_cards(workflow, values, risk_codes):
    cards = [
        {
            'name': 'Contract owner',
            'status': 'Active',
            'reason': 'Owns field completeness and business context for the generated DPA draft.',
            'trigger': 'Workflow instance created',
        },
        {
            'name': 'Legal',
            'status': 'Triggered',
            'reason': 'Personal data processing and approved DPA playbook checks require legal control.',
            'trigger': 'Personal data processing review',
        },
    ]
    dpo_risk_codes = {'scc_transfer_review', 'cross_border_no_mechanism', 'special_categories_risk', 'privacy_fact_uncertain'}
    if (
        values.get('personal_data_involved')
        or values.get('cross_border_transfer')
        or values.get('special_categories_data')
        or dpo_risk_codes & risk_codes
    ):
        cards.append({
            'name': 'DPO',
            'status': 'Triggered',
            'reason': 'DPO review is required because personal data processing, transfer posture, special-category data, or an unconfirmed privacy fact is in scope.',
            'trigger': 'Privacy and transfer risk rules',
        })
    return cards


def _dpa_document_sections(draft_content, values):
    content = draft_content or ''
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    sections = []
    for index, paragraph in enumerate(paragraphs):
        title = 'Generated DPA draft' if index == 0 else 'DPA clause'
        source = 'Approved template'
        source_detail = 'GDPR Processor DPA · Netherlands · B2B'
        tone = 'template'
        if 'Subject Matter' in paragraph or 'Categories of Data' in paragraph:
            title = 'Processing Details'
            source = 'AI-assisted suggestion'
            source_detail = 'Field values mapped into approved playbook language'
            tone = 'ai'
            fields = ['Processing purpose', 'Personal data categories', 'Data subjects']
            section_id = 'processing-details'
        elif 'Sub-processors' in paragraph:
            title = 'Subprocessor clause'
            source = 'Approved clause library' if values.get('subprocessors_used') else 'Approved template'
            source_detail = 'Subprocessor flow-down position'
            tone = 'library'
            fields = ['Subprocessor position']
            section_id = 'subprocessors'
        elif 'International Transfers' in paragraph:
            title = 'Transfer clause'
            source = 'Risk-triggered fallback' if values.get('cross_border_transfer') else 'Approved template'
            source_detail = 'SCC / EEA transfer rule'
            tone = 'risk' if values.get('cross_border_transfer') else 'template'
            fields = ['Data transfer position', 'Transfer mechanism']
            section_id = 'international-transfers'
        elif 'Security' in paragraph:
            title = 'Security clause'
            source = 'Approved clause library'
            source_detail = 'Standard TOMs obligation'
            tone = 'library'
            fields = []
            section_id = 'security'
        elif 'Breach Notification' in paragraph:
            title = 'Breach notice clause'
            source = 'Approved template'
            source_detail = 'GDPR Processor DPA playbook'
            tone = 'template'
            fields = ['Breach notification window']
            section_id = 'breach-notification'
        elif 'Governing Law' in paragraph:
            title = 'Governing law'
            source = 'Approved template'
            source_detail = 'Legal position field'
            tone = 'template'
            fields = ['Governing law']
            section_id = 'governing-law'
        else:
            fields = ['Counterparty name', 'Effective date'] if index == 0 else []
            section_id = 'generated-dpa-draft' if index == 0 else f'dpa-clause-{index}'
        sections.append({
            'title': title,
            'content': paragraph,
            'source': source,
            'source_detail': source_detail,
            'tone': tone,
            'fields': fields,
            'section_id': section_id,
        })
    return sections


def _workflow_audit_history(workflow, *, limit=12):
    """Return persisted audit rows for a governed workflow workspace."""
    if not workflow or not workflow.organization_id:
        return []

    approval_ids = []
    document_ids = []
    deadline_ids = []
    if workflow.contract_id:
        approval_ids = list(workflow.contract.approval_requests.values_list('pk', flat=True))
        document_ids = list(workflow.contract.documents.values_list('pk', flat=True))
        deadline_ids = list(workflow.contract.deadlines.values_list('pk', flat=True))

    audit_filter = Q(model_name='Workflow', object_id=workflow.pk)
    if workflow.contract_id:
        audit_filter |= Q(model_name='Contract', object_id=workflow.contract_id)
    if approval_ids:
        audit_filter |= Q(model_name='ApprovalRequest', object_id__in=approval_ids)
    if document_ids:
        audit_filter |= Q(model_name='Document', object_id__in=document_ids)
    if deadline_ids:
        audit_filter |= Q(model_name='Deadline', object_id__in=deadline_ids)

    entries = (
        AuditLog.objects.filter(organization=workflow.organization)
        .filter(audit_filter)
        .select_related('user')
        .order_by('-timestamp')[:limit]
    )
    return [
        {
            'event': (entry.event_type or entry.get_action_display()).replace('.', ' ').replace('_', ' ').title(),
            'meta': entry.object_repr or (entry.user.get_full_name() or entry.user.username if entry.user else 'System'),
            'timestamp': entry.timestamp,
            'actor': entry.user.get_full_name() or entry.user.username if entry.user else 'System',
            'action': entry.event_type or entry.get_action_display(),
            'target': entry.object_repr or entry.model_name,
            'reason': (entry.changes or {}).get('reason') or (entry.changes or {}).get('event') or '',
        }
        for entry in entries
    ]


def _dpa_audit_preview(workflow):
    return _workflow_audit_history(workflow)


def _dpa_workspace_context(workflow):
    values = _field_values_by_key(workflow)
    risk_signals = list(RiskSignal.objects.filter(workflow=workflow).order_by('-severity', 'detected_at'))
    risk_codes = {signal.code for signal in risk_signals}
    draft_document = DraftDocument.objects.filter(workflow=workflow, is_current=True).order_by('-version').first()
    template_routes = list(ApprovalRoute.objects.filter(workflow_template=workflow.template).order_by('order')) if workflow.template_id else []
    current_step = WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.IN_PROGRESS).order_by('order').first()
    if current_step is None:
        current_step = WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.PENDING).order_by('order').first()

    return {
        'values': values,
        'current_stage': current_step.name if current_step else 'AI Draft',
        'owner': workflow.created_by.get_full_name() or workflow.created_by.username if workflow.created_by else 'Unassigned',
        'risk_level': _risk_level_for_signals(risk_signals),
        'next_action': 'Review DPA risk signals',
        'timeline': ['Intake', 'AI Draft', 'Privacy Review', 'Legal Review', 'DPO Approval', 'Signature', 'Repository'],
        'active_timeline_index': 2 if risk_signals else 1,
        'draft_document': draft_document,
        'document_sections': _dpa_document_sections(draft_document.content if draft_document else '', values),
        'risk_cards': [_risk_detail_for_signal(signal) for signal in risk_signals],
        'approval_cards': _dpa_approval_cards(workflow, values, risk_codes),
        'dpo_approval_triggered': bool(
            values.get('personal_data_involved')
            or values.get('cross_border_transfer')
            or values.get('special_categories_data')
            or {'scc_transfer_review', 'cross_border_no_mechanism', 'special_categories_risk'} & risk_codes
        ),
        'template_routes': template_routes,
        'audit_preview': _dpa_audit_preview(workflow),
        'field_count': FieldValue.objects.filter(workflow=workflow).count(),
    }


def _msa_risk_detail_for_signal(signal):
    details = {
        'finance_approval_required': {
            'title': 'Finance approval signal',
            'source': 'AI Smart Questions · Finance threshold',
            'recommended_action': 'Confirm commercial value, payment terms, and finance approval threshold alignment.',
            'approval_impact': 'Finance approval required before signature.',
            'section_anchor': 'fees-payment',
        },
        'nonstandard_payment_terms': {
            'title': 'Payment-term deviation',
            'source': 'Commercial terms · Payment terms',
            'recommended_action': 'Confirm why the draft deviates from standard Net 30 terms before approval.',
            'approval_impact': 'Finance approval required before signature.',
            'section_anchor': 'fees-payment',
        },
        'liability_cap_nonstandard': {
            'title': 'Liability cap deviation',
            'source': 'AI Smart Questions · Liability cap position',
            'recommended_action': 'Review fallback liability clause against the MSA commercial playbook.',
            'approval_impact': 'Legal approval required before the workflow can advance.',
            'section_anchor': 'liability',
        },
        'client_paper_review_required': {
            'title': 'Client-paper review',
            'source': 'AI Smart Questions · Paper source',
            'recommended_action': 'Review third-party template terms against the approved Payrollminds playbook.',
            'approval_impact': 'Legal approval required before signature.',
            'section_anchor': 'generated-msa-draft',
        },
        'msa_dpa_review_required': {
            'title': 'DPA / privacy review signal',
            'source': 'AI Smart Questions · Personal data processing',
            'recommended_action': 'Review the data protection section and launch or link a DPA workflow if required.',
            'approval_impact': 'Legal review required; linked DPA workflow may be needed.',
            'section_anchor': 'data-protection',
        },
        'renewal_notice_review': {
            'title': 'Renewal notice signal',
            'source': 'AI Smart Questions · Auto-renewal included',
            'recommended_action': 'Confirm notice periods and obligation tracking for renewal terms.',
            'approval_impact': 'Commercial review required before signature.',
            'section_anchor': 'term-renewal',
        },
        'nonstandard_ip_ownership': {
            'title': 'Non-standard IP ownership',
            'source': 'AI Smart Questions · IP ownership',
            'recommended_action': 'Review the IP ownership fallback and document the approved commercial position.',
            'approval_impact': 'Legal approval required.',
            'section_anchor': 'intellectual-property',
        },
        'nonpreferred_governing_law': {
            'title': 'Governing law escalation',
            'source': 'AI Smart Questions · Preferred jurisdiction',
            'recommended_action': 'Escalate governing law outside the preferred jurisdiction to Legal.',
            'approval_impact': 'Legal escalation required before signature.',
            'section_anchor': 'governing-law',
        },
    }
    fallback = {
        'title': signal.description,
        'source': 'MSA risk checks',
        'recommended_action': 'Review against the approved MSA commercial playbook.',
        'approval_impact': 'Legal review required.',
        'section_anchor': 'services',
    }
    data = details.get(signal.code, fallback)
    return {
        'title': data['title'],
        'severity': signal.get_severity_display(),
        'severity_code': signal.severity.lower(),
        'reason': signal.description,
        'source': data['source'],
        'recommended_action': data['recommended_action'],
        'approval_impact': data['approval_impact'],
        'status': 'Open' if not signal.is_resolved else 'Resolved',
        'section_anchor': data['section_anchor'],
    }


def _msa_approval_cards(workflow, values, risk_codes, actor=None):
    from contracts.services.approval_workflow import actor_can_decide

    requests_by_step = {
        request.approval_step: request
        for request in ApprovalRequest.objects.filter(contract=workflow.contract)
        .select_related('assigned_to')
        .order_by('-created_at')
    }

    def _with_request(card, step=None):
        request = requests_by_step.get(step) if step else None
        if request is None:
            return card
        card.update({
            'id': request.pk,
            'status': request.get_status_display(),
            'assigned_to': (
                request.assigned_to.get_full_name() or request.assigned_to.username
                if request.assigned_to else 'Unassigned'
            ),
            'can_decide': bool(actor and actor_can_decide(request, actor, 'approve')),
        })
        return card

    cards = [
        {
            'name': 'Contract owner',
            'status': 'Active',
            'reason': 'Owns field completeness, business context, and commercial posture for the generated MSA draft.',
            'trigger': 'Workflow instance created',
        },
    ]
    if {'liability_cap_nonstandard', 'client_paper_review_required', 'msa_dpa_review_required', 'nonstandard_ip_ownership', 'nonpreferred_governing_law'} & risk_codes:
        cards.append(_with_request({
            'name': 'Legal',
            'status': 'Triggered',
            'reason': 'Fallback positions, privacy scope, IP ownership, or governing law require legal control.',
            'trigger': 'Commercial and legal risk rules',
        }, 'LEGAL'))
    if {'finance_approval_required', 'nonstandard_payment_terms'} & risk_codes:
        cards.append(_with_request({
            'name': 'Finance',
            'status': 'Triggered',
            'reason': 'Contract value or payment terms require finance review.',
            'trigger': 'Finance threshold or non-standard payment terms',
        }, 'FINANCE'))
    return cards


def _msa_document_sections(draft_content, values, risk_codes=None):
    risk_codes = risk_codes or set()
    content = draft_content or ''
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    sections = []
    for index, paragraph in enumerate(paragraphs):
        title = 'Generated MSA draft' if index == 0 else 'MSA clause'
        source = 'Approved template'
        source_detail = 'Enterprise Services MSA · Netherlands · B2B'
        tone = 'template'
        if '1. Services' in paragraph:
            title = 'Services'
            source = 'AI-assisted suggestion'
            source_detail = 'Field values mapped into approved services language'
            tone = 'ai'
            fields = ['Services description', 'Statement of Work required', 'Deliverables defined', 'Acceptance criteria required']
            section_id = 'services'
            value_keys = ['services_description', 'sow_required', 'deliverables_defined', 'acceptance_criteria_required']
        elif '2. Fees and Payment' in paragraph:
            title = 'Fees and Payment'
            source = 'Risk-triggered fallback' if 'nonstandard_payment_terms' in risk_codes else 'Approved template'
            source_detail = 'Commercial terms field mapping'
            tone = 'risk' if 'nonstandard_payment_terms' in risk_codes else 'template'
            fields = ['Contract value', 'Currency', 'Payment terms']
            section_id = 'fees-payment'
            value_keys = ['value', 'currency', 'payment_terms']
        elif '3. Term and Renewal' in paragraph:
            title = 'Term and Renewal'
            source = 'Risk-triggered fallback' if values.get('auto_renewal_included') or str(values.get('renewal_type', '')).lower() == 'auto-renew' else 'Approved template'
            source_detail = 'Term, renewal, and notice position'
            tone = 'risk' if values.get('auto_renewal_included') or str(values.get('renewal_type', '')).lower() == 'auto-renew' else 'template'
            fields = ['Initial term', 'Renewal type', 'Termination notice period']
            section_id = 'term-renewal'
            value_keys = ['initial_term', 'renewal_type', 'termination_notice_period']
        elif '4. Liability' in paragraph:
            title = 'Liability'
            source = 'Risk-triggered fallback' if values.get('liability_cap_nonstandard') else 'Approved clause library'
            source_detail = 'Approved liability cap position'
            tone = 'risk' if values.get('liability_cap_nonstandard') else 'library'
            fields = ['Liability cap']
            section_id = 'liability'
            value_keys = ['liability_cap']
        elif '5. Intellectual Property' in paragraph:
            title = 'Intellectual Property'
            source = 'Risk-triggered fallback' if values.get('ip_ownership_nonstandard') else 'Approved clause library'
            source_detail = 'IP ownership position'
            tone = 'risk' if values.get('ip_ownership_nonstandard') else 'library'
            fields = ['IP ownership']
            section_id = 'intellectual-property'
            value_keys = ['ip_ownership']
        elif '6. Data Protection' in paragraph:
            title = 'Data Protection'
            source = 'AI-assisted suggestion' if values.get('personal_data_involved') or values.get('services_involve_personal_data') else 'Approved template'
            source_detail = 'Privacy scope and linked DPA guidance'
            tone = 'ai' if values.get('personal_data_involved') or values.get('services_involve_personal_data') else 'template'
            fields = ['Personal data involved']
            section_id = 'data-protection'
            value_keys = ['personal_data_involved']
        elif '7. Governing Law' in paragraph:
            title = 'Governing Law'
            source = 'Risk-triggered fallback' if values.get('governing_law_nonpreferred') or ('netherlands' not in str(values.get('governing_law', '')).lower() and values.get('governing_law')) else 'Approved template'
            source_detail = 'Jurisdiction and governing law position'
            tone = 'risk' if values.get('governing_law_nonpreferred') or ('netherlands' not in str(values.get('governing_law', '')).lower() and values.get('governing_law')) else 'template'
            fields = ['Governing law', 'Jurisdiction']
            section_id = 'governing-law'
            value_keys = ['governing_law', 'jurisdiction']
        else:
            fields = ['Counterparty name', 'Effective date'] if index == 0 else []
            section_id = 'generated-msa-draft' if index == 0 else f'msa-clause-{index}'
            value_keys = ['counterparty', 'start_date'] if index == 0 else []
        sections.append({
            'title': title,
            'content': paragraph,
            'source': source,
            'source_detail': source_detail,
            'tone': tone,
            'fields': fields,
            'value_keys': value_keys,
            'section_id': section_id,
            'has_exception': tone == 'risk',
            'has_changes': tone in {'ai', 'risk'},
        })
    return sections


MSA_LIFECYCLE_STAGES = (
    'Intake',
    'Drafting',
    'Commercial review',
    'Legal review',
    'Finance approval',
    'Signature',
    'Active',
)

MSA_STAGE_ALIASES = {
    'Intake': 'Intake',
    'Draft': 'Drafting',
    'AI Draft': 'Drafting',
    'Drafting': 'Drafting',
    'Draft generation': 'Drafting',
    'Commercial Review': 'Commercial review',
    'Commercial review': 'Commercial review',
    'Legal Review': 'Legal review',
    'Legal review': 'Legal review',
    'Legal approval': 'Legal review',
    'Finance Review': 'Finance approval',
    'Finance Approval': 'Finance approval',
    'Finance approval': 'Finance approval',
    'Approval': 'Signature',
    'Signature': 'Signature',
    'Repository': 'Active',
    'Active': 'Active',
}

MSA_SECTION_STATE_TONES = {
    'Exception': 'danger',
    'Needs input': 'attention',
    'Pending review': 'progress',
    'Approved': 'success',
    'Complete': 'success',
}


def _msa_normalize_stage(stage_name):
    if not stage_name:
        return 'Drafting'
    return MSA_STAGE_ALIASES.get(stage_name, stage_name)


def _msa_section_needs_input(value_keys, values):
    if not value_keys:
        return False
    for key in value_keys:
        value = values.get(key)
        if value in (None, '', [], {}):
            return True
    return False


def _msa_enrich_document_sections(sections, *, values, risk_cards, current_stage):
    exception_anchors = {
        card['section_anchor']
        for card in risk_cards
        if card.get('status') == 'Open' and card.get('section_anchor')
    }
    review_stages = {'Commercial review', 'Legal review', 'Finance approval'}
    approved_stages = {'Signature', 'Active'}

    enriched = []
    for section in sections:
        section = dict(section)
        has_exception = section['section_id'] in exception_anchors or section.get('has_exception')
        needs_input = _msa_section_needs_input(section.get('value_keys') or [], values)
        if has_exception:
            state = 'Exception'
        elif needs_input:
            state = 'Needs input'
        elif current_stage in approved_stages and not has_exception:
            state = 'Approved'
        elif current_stage in review_stages and (section.get('has_changes') or section.get('tone') in {'ai', 'risk'}):
            state = 'Pending review'
        else:
            state = 'Complete'
        section['state'] = state
        section['state_tone'] = MSA_SECTION_STATE_TONES[state]
        enriched.append(section)
    return enriched


def _msa_audit_preview(workflow):
    """Render the persisted tamper-evident audit history, never a projection."""
    return _workflow_audit_history(workflow)


def _msa_workspace_context(workflow, actor=None):
    values = _field_values_by_key(workflow)
    required_definitions = list(
        FieldDefinition.objects.filter(
            workflow_template=workflow.template,
            is_required=True,
        ).only('key')
    )
    required_completed_count = sum(
        values.get(field.key) not in (None, '', [], {})
        for field in required_definitions
    )
    risk_signals = list(RiskSignal.objects.filter(workflow=workflow).order_by('-severity', 'detected_at'))
    risk_codes = {signal.code for signal in risk_signals}
    draft_document = DraftDocument.objects.filter(workflow=workflow, is_current=True).order_by('-version').first()
    template_routes = list(ApprovalRoute.objects.filter(workflow_template=workflow.template).order_by('order')) if workflow.template_id else []
    current_step = (
        WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.IN_PROGRESS)
        .select_related('assigned_to')
        .order_by('order')
        .first()
    )
    if current_step is None:
        current_step = (
            WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.PENDING)
            .select_related('assigned_to')
            .order_by('order')
            .first()
        )

    if {'finance_approval_required', 'nonstandard_payment_terms'} & risk_codes:
        next_action = 'Review Finance approval route'
    elif 'msa_dpa_review_required' in risk_codes:
        next_action = 'Review privacy scope and linked DPA need'
    elif risk_codes:
        next_action = 'Review MSA risk signals'
    else:
        next_action = 'Review generated MSA draft'

    raw_stage = current_step.name if current_step else 'Drafting'
    current_stage = _msa_normalize_stage(raw_stage)
    if current_stage not in MSA_LIFECYCLE_STAGES:
        current_stage = 'Commercial review' if risk_signals else 'Drafting'
    active_timeline_index = MSA_LIFECYCLE_STAGES.index(current_stage)

    owner = (
        workflow.created_by.get_full_name() or workflow.created_by.username
        if workflow.created_by else 'Unassigned'
    )
    if current_step and current_step.assigned_to_id:
        stage_owner = current_step.assigned_to.get_full_name() or current_step.assigned_to.username
    else:
        stage_owner = owner
    stage_status = current_step.get_status_display() if current_step else 'In progress'

    risk_level = _risk_level_for_signals(risk_signals)
    risk_cards = [_msa_risk_detail_for_signal(signal) for signal in risk_signals]
    open_exceptions = sum(1 for card in risk_cards if card.get('status') == 'Open')
    document_sections = _msa_enrich_document_sections(
        _msa_document_sections(draft_document.content if draft_document else '', values, risk_codes),
        values=values,
        risk_cards=risk_cards,
        current_stage=current_stage,
    )

    counterparty = (
        values.get('counterparty')
        or (workflow.contract.counterparty if workflow.contract_id else '')
        or 'Counterparty pending'
    )
    risk_badge_tone = {
        'Low': 'success',
        'Medium': 'attention',
        'High': 'danger',
        'Critical': 'danger',
    }.get(risk_level, 'neutral')

    return {
        'values': values,
        'display_title': f'MSA · {counterparty}',
        'counterparty': counterparty,
        'current_stage': current_stage,
        'owner': owner,
        'risk_level': risk_level,
        'risk_badge_label': f'{risk_level} risk',
        'risk_badge_tone': risk_badge_tone,
        'open_exceptions': open_exceptions,
        'open_exceptions_label': (
            f'{open_exceptions} open exception{"s" if open_exceptions != 1 else ""}'
            if open_exceptions else 'No open exceptions'
        ),
        'next_action': next_action,
        'primary_cta': next_action,
        'timeline': list(MSA_LIFECYCLE_STAGES),
        'active_timeline_index': active_timeline_index,
        'active_stage_owner': stage_owner,
        'active_stage_status': stage_status,
        'draft_document': draft_document,
        'document_sections': document_sections,
        'risk_cards': risk_cards,
        'approval_cards': _msa_approval_cards(workflow, values, risk_codes, actor=actor),
        'finance_approval_triggered': bool({'finance_approval_required', 'nonstandard_payment_terms'} & risk_codes),
        'template_routes': template_routes,
        'audit_preview': _msa_audit_preview(workflow),
        'field_count': FieldValue.objects.filter(workflow=workflow).count(),
        'required_field_progress': {
            'completed': required_completed_count,
            'total': len(required_definitions),
        },
    }


def _nda_risk_detail_for_signal(signal):
    details = {
        'confidentiality_period_nonstandard': {
            'title': 'Long confidentiality period',
            'source': 'AI Smart Questions · Confidentiality period',
            'recommended_action': 'Review the confidentiality term against the approved NDA self-serve playbook.',
            'approval_impact': 'Legal approval required before signature.',
            'section_anchor': 'term',
        },
        'nda_privacy_review_required': {
            'title': 'Privacy / DPA review signal',
            'source': 'AI Smart Questions · Personal data involved',
            'recommended_action': 'Review privacy scope and determine whether a linked DPA workflow is required.',
            'approval_impact': 'Legal review required before signature.',
            'section_anchor': 'personal-data',
        },
        'residual_knowledge_risk': {
            'title': 'Residual knowledge risk',
            'source': 'AI Smart Questions · Residual knowledge language',
            'recommended_action': 'Confirm the approved fallback for residual knowledge language before signature.',
            'approval_impact': 'Legal approval required before signature.',
            'section_anchor': 'residual-knowledge',
        },
        'nonpreferred_governing_law': {
            'title': 'Governing law escalation',
            'source': 'AI Smart Questions · Preferred jurisdiction',
            'recommended_action': 'Escalate non-preferred governing law to Legal for approval.',
            'approval_impact': 'Legal approval required before signature.',
            'section_anchor': 'governing-law',
        },
    }
    data = details.get(signal.code, {
        'title': signal.description,
        'source': 'NDA risk checks',
        'recommended_action': 'Review against the approved NDA self-serve playbook.',
        'approval_impact': 'Legal review required before signature.',
        'section_anchor': 'purpose',
    })
    return {
        'title': data['title'],
        'severity': signal.get_severity_display(),
        'severity_code': signal.severity.lower(),
        'reason': signal.description,
        'source': data['source'],
        'recommended_action': data['recommended_action'],
        'approval_impact': data['approval_impact'],
        'status': 'Open' if not signal.is_resolved else 'Resolved',
        'section_anchor': data['section_anchor'],
    }


def _nda_approval_cards(workflow, risk_codes):
    cards = [
        {
            'name': 'Contract owner',
            'status': 'Active',
            'reason': 'Owns self-serve completion, business context, and readiness to send the NDA for signature.',
            'trigger': 'Workflow instance created',
        },
    ]
    if risk_codes:
        cards.append({
            'name': 'Legal',
            'status': 'Triggered',
            'reason': 'Non-standard confidentiality, privacy, residual knowledge, or governing law requires legal control.',
            'trigger': 'NDA risk rules',
        })
    else:
        cards.append({
            'name': 'Signature',
            'status': 'Ready',
            'reason': 'No NDA risk triggers were detected, so the workflow can remain self-serve.',
            'trigger': 'Self-serve eligible',
        })
    return cards


def _nda_document_sections(draft_content, values):
    content = draft_content or ''
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    sections = []
    for index, paragraph in enumerate(paragraphs):
        title = 'Generated NDA draft' if index == 0 else 'NDA clause'
        source = 'Approved template'
        source_detail = 'Mutual NDA · Netherlands · B2B'
        tone = 'template'
        if '1. Purpose' in paragraph:
            title = 'Purpose'
            source = 'AI-assisted suggestion'
            source_detail = 'Field values mapped into approved confidentiality purpose language'
            tone = 'ai'
            fields = ['NDA type', 'Confidentiality purpose']
            section_id = 'purpose'
        elif '2. Confidential Information' in paragraph:
            title = 'Confidential Information'
            source = 'Approved template'
            source_detail = 'Disclosure scope field mapping'
            tone = 'template'
            fields = ['Disclosure scope']
            section_id = 'confidential-information'
        elif '3. Confidentiality Obligations' in paragraph:
            title = 'Confidentiality Obligations'
            source = 'Approved clause library'
            source_detail = 'Standard NDA protection obligations'
            tone = 'library'
            fields = []
            section_id = 'confidentiality-obligations'
        elif '4. Term' in paragraph:
            title = 'Term'
            source = 'Risk-triggered fallback' if str(values.get('confidentiality_period', '')).strip() and float(values.get('confidentiality_period') or 0) > 3 or values.get('confidentiality_period_nonstandard') else 'Approved template'
            source_detail = 'Confidentiality period position'
            tone = 'risk' if str(values.get('confidentiality_period', '')).strip() and float(values.get('confidentiality_period') or 0) > 3 or values.get('confidentiality_period_nonstandard') else 'template'
            fields = ['Confidentiality period']
            section_id = 'term'
        elif '5. Permitted Recipients' in paragraph:
            title = 'Permitted Recipients'
            source = 'Approved template'
            source_detail = 'Permitted recipients field mapping'
            tone = 'template'
            fields = ['Permitted recipients']
            section_id = 'permitted-recipients'
        elif '6. Personal Data' in paragraph:
            title = 'Personal Data'
            source = 'AI-assisted suggestion' if values.get('personal_data_involved') else 'Approved template'
            source_detail = 'Privacy scope and linked DPA guidance'
            tone = 'ai' if values.get('personal_data_involved') else 'template'
            fields = ['Personal data involved']
            section_id = 'personal-data'
        elif '7. Governing Law' in paragraph:
            title = 'Governing Law'
            source = 'Risk-triggered fallback' if values.get('governing_law_nonpreferred') or ('netherlands' not in str(values.get('governing_law', '')).lower() and values.get('governing_law')) else 'Approved template'
            source_detail = 'Governing law and jurisdiction position'
            tone = 'risk' if values.get('governing_law_nonpreferred') or ('netherlands' not in str(values.get('governing_law', '')).lower() and values.get('governing_law')) else 'template'
            fields = ['Governing law', 'Jurisdiction']
            section_id = 'governing-law'
        elif '8. Residual Knowledge' in paragraph:
            title = 'Residual Knowledge'
            source = 'Risk-triggered fallback' if values.get('residual_knowledge_included') or values.get('residual_knowledge_nonstandard') else 'Approved clause library'
            source_detail = 'Residual knowledge fallback position'
            tone = 'risk' if values.get('residual_knowledge_included') or values.get('residual_knowledge_nonstandard') else 'library'
            fields = ['Residual knowledge clause included']
            section_id = 'residual-knowledge'
        elif '9. Injunctive Relief' in paragraph:
            title = 'Injunctive Relief'
            source = 'Approved clause library'
            source_detail = 'Standard NDA enforcement position'
            tone = 'library'
            fields = ['Injunctive relief included']
            section_id = 'injunctive-relief'
        else:
            fields = ['Counterparty name', 'Effective date'] if index == 0 else []
            section_id = 'generated-nda-draft' if index == 0 else f'nda-clause-{index}'
        sections.append({
            'title': title,
            'content': paragraph,
            'source': source,
            'source_detail': source_detail,
            'tone': tone,
            'fields': fields,
            'section_id': section_id,
        })
    return sections


def _nda_audit_preview(workflow):
    return _workflow_audit_history(workflow)


def _nda_workspace_context(workflow):
    values = _field_values_by_key(workflow)
    risk_signals = list(RiskSignal.objects.filter(workflow=workflow).order_by('-severity', 'detected_at'))
    risk_codes = {signal.code for signal in risk_signals}
    draft_document = DraftDocument.objects.filter(workflow=workflow, is_current=True).order_by('-version').first()
    current_step = WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.IN_PROGRESS).order_by('order').first()
    if current_step is None:
        current_step = WorkflowStep.objects.filter(workflow=workflow, status=WorkflowStep.Status.PENDING).order_by('order').first()

    if 'nda_privacy_review_required' in risk_codes:
        next_action = 'Review privacy scope and linked DPA need'
    elif risk_codes:
        next_action = 'Review NDA legal risk signals'
    else:
        next_action = 'Review generated NDA draft'

    risk_cards = [_nda_risk_detail_for_signal(signal) for signal in risk_signals]
    if not risk_cards:
        risk_cards = [{
            'title': 'Self-serve eligible',
            'severity': 'Low',
            'severity_code': 'low',
            'reason': 'No NDA risk triggers were detected from the approved self-serve playbook.',
            'source': 'NDA self-serve rules',
            'recommended_action': 'Proceed to signature from the governed workspace.',
            'approval_impact': 'Legal review not required.',
            'status': 'Ready',
            'section_anchor': 'purpose',
        }]

    return {
        'values': values,
        'current_stage': current_step.name if current_step else 'AI Draft',
        'owner': workflow.created_by.get_full_name() or workflow.created_by.username if workflow.created_by else 'Unassigned',
        'risk_level': _risk_level_for_signals(risk_signals),
        'next_action': next_action,
        'timeline': ['Intake', 'AI Draft', 'Self-Serve Check', 'Legal Review', 'Signature', 'Repository'],
        'active_timeline_index': 3 if risk_signals else 2,
        'draft_document': draft_document,
        'document_sections': _nda_document_sections(draft_document.content if draft_document else '', values),
        'risk_cards': risk_cards,
        'approval_cards': _nda_approval_cards(workflow, risk_codes),
        'self_serve_eligible': not risk_codes,
        'legal_review_triggered': bool(risk_codes),
        'audit_preview': _nda_audit_preview(workflow),
        'field_count': FieldValue.objects.filter(workflow=workflow).count(),
    }


def _workflow_detail_context(workflow, add_step_form=None, actor=None):
    organization = workflow.organization
    steps = WorkflowStep.objects.filter(workflow=workflow).order_by('order')
    approval_requests = ApprovalRequest.objects.filter(organization=organization, contract=workflow.contract).select_related('assigned_to', 'delegated_to', 'rule').order_by('-created_at') if workflow.contract_id else ApprovalRequest.objects.none()
    approval_rules = ApprovalRule.objects.filter(organization=organization, is_active=True).order_by('order', 'sla_hours', 'id')
    max_order = steps.aggregate(max_order=Max('order'))['max_order'] or 0
    form = add_step_form or WorkflowStepForm(initial={'order': max_order + 1})
    form = apply_form_queryset_scopes(form, organization, {'assigned_to': organization_user_queryset})
    context = {
        'workflow': workflow,
        'workflow_steps': steps,
        'add_step_form': form,
        'approval_requests': approval_requests,
        'approval_rules': approval_rules,
        'approval_rules_url': reverse_lazy('contracts:approval_rule_list'),
        'approval_requests_url': reverse_lazy('contracts:approval_request_list'),
        'workflow_audit_feed': get_workflow_audit_feed(workflow, limit=6),
        'workflow_activity_url': reverse_lazy('contracts:workflow_activity', kwargs={'pk': workflow.pk}),
    }
    if _workflow_is_dpa(workflow):
        context['is_dpa_workspace'] = True
        context['dpa_workspace'] = _dpa_workspace_context(workflow)
    elif _workflow_is_msa(workflow):
        context['is_msa_workspace'] = True
        context['msa_workspace'] = _msa_workspace_context(workflow, actor=actor)
    elif _workflow_is_nda(workflow):
        context['is_nda_workspace'] = True
        context['nda_workspace'] = _nda_workspace_context(workflow)
    return context


def _workflow_template_detail_context(template, organization, step_form=None):
    steps = WorkflowTemplateStep.objects.filter(template=template).order_by('order')
    template_versions = list_template_versions(template)
    form = step_form or WorkflowTemplateStepForm()
    form = apply_form_queryset_scopes(form, organization, {'specific_assignee': organization_user_queryset})
    publish_validation = validate_template_for_publish(template)
    return {
        'workflow_template': template,
        'steps': steps,
        'template_versions': template_versions,
        'step_form': form,
        'preview_form': WorkflowTemplatePreviewForm(),
        'preview_result': None,
        'step_controls': _build_template_step_controls(steps),
        'workflow_template_audit_feed': get_workflow_template_audit_feed(template, limit=6),
        'workflow_template_activity_url': reverse_lazy('contracts:workflow_template_activity', kwargs={'pk': template.pk}),
        'publish_validation': publish_validation,
        'can_publish': publish_validation.ok and not template.is_active,
        'is_incomplete_template': not bool(steps),
        'designer_tabs': workflow_designer_tabs(active='templates'),
    }


def _build_workflow_editor_context(form, organization):
    contract = None
    contract_value = form.data.get('contract') if form.is_bound else form.initial.get('contract')
    if contract_value:
        contract = Contract.objects.filter(pk=contract_value).first()

    selected_template = None
    template_value = form.data.get('template') if form.is_bound else form.initial.get('template')
    if template_value:
        selected_template = WorkflowTemplate.objects.filter(pk=template_value).first()

    suggested_template = suggest_workflow_template_for_contract(contract) if contract else None
    template_versions = list_template_versions(selected_template or suggested_template) if (selected_template or suggested_template) else []

    comparison = None
    if selected_template and suggested_template and selected_template.pk != suggested_template.pk:
        comparison = compare_template_versions(selected_template, suggested_template)

    return {
        'selected_contract': contract,
        'selected_template': selected_template,
        'suggested_template': suggested_template,
        'template_versions': template_versions,
        'template_comparison': comparison,
    }
