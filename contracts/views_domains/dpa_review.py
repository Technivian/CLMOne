"""DPA Review Pack — first-class Data Processing Agreement review module.

Analysis (contracts.services.dpa_review.run_dpa_analysis) only ever
produces suggestions: it updates the checklist fields on a DPAReviewPack
and returns candidate DPARiskItem specs. It never touches approval_status.
Final approval is a separate, explicit, permission-gated human action
(DPAReviewPackApproveView) — there is no code path that sets
DPAReviewPack.approval_status to APPROVED except that view.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView

from contracts.middleware import log_action
from contracts.models import AuditLog, Contract, DPAPlaybookPosition, DPAReviewPack, DPARiskItem
from contracts.permissions import ContractAction, can_access_contract_action, can_manage_organization
from contracts.services.dpa_review import run_dpa_analysis
from contracts.tenancy import get_user_organization
from contracts.view_support import TenantScopedQuerysetMixin


class DPAReviewPackListView(TenantScopedQuerysetMixin, LoginRequiredMixin, ListView):
    """DPA dashboard: role qualification, processing scope, transfer/
    subprocessor risk, security, breach notification, audit, deletion,
    liability conflicts, and approval status — one row per DPA review pack."""
    model = DPAReviewPack
    template_name = 'contracts/dpa_review_pack_list.html'
    context_object_name = 'review_packs'

    def get_queryset(self):
        org = get_user_organization(self.request.user)
        if not org:
            return DPAReviewPack.objects.none()
        return (
            DPAReviewPack.objects.filter(organization=org)
            .select_related('contract', 'counterparty')
            .prefetch_related('risk_items')
            .order_by('-updated_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        packs = ctx['review_packs']
        ctx['total_packs'] = len(packs)
        ctx['pending_approval_count'] = sum(1 for p in packs if p.approval_status in (DPAReviewPack.ApprovalStatus.DRAFT, DPAReviewPack.ApprovalStatus.UNDER_REVIEW))
        ctx['escalated_count'] = sum(1 for p in packs if p.approval_status == DPAReviewPack.ApprovalStatus.ESCALATED)
        ctx['open_critical_risk_count'] = sum(
            1 for p in packs for r in p.risk_items.all()
            if r.status == DPARiskItem.Status.OPEN and r.severity == DPARiskItem.Severity.CRITICAL
        )
        return ctx


class DPAReviewPackDetailView(TenantScopedQuerysetMixin, LoginRequiredMixin, DetailView):
    model = DPAReviewPack
    template_name = 'contracts/dpa_review_pack_detail.html'
    context_object_name = 'review_pack'

    def get_queryset(self):
        org = get_user_organization(self.request.user)
        if not org:
            return DPAReviewPack.objects.none()
        return (
            DPAReviewPack.objects.filter(organization=org)
            .select_related('contract', 'counterparty')
            .prefetch_related('risk_items', 'subprocessors', 'transfer_records')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        review_pack = ctx['review_pack']
        ctx['risk_items'] = review_pack.risk_items.all()
        ctx['can_edit'] = can_access_contract_action(self.request.user, review_pack.contract, ContractAction.EDIT)
        ctx['can_approve'] = can_manage_organization(self.request.user, review_pack.organization)
        ctx['payroll_data_fields'] = [
            (label, getattr(review_pack, field_name)) for field_name, label in (
                ('has_employee_identity_data', 'Employee identity data'),
                ('has_salary_wage_data', 'Salary / wage data'),
                ('has_tax_data', 'Tax data'),
                ('has_social_security_data', 'Social security data'),
                ('has_bank_account_data', 'Bank account details'),
                ('has_pension_benefits_data', 'Pension / benefits data'),
                ('has_absence_leave_data', 'Absence / leave data'),
                ('has_employment_contract_data', 'Employment contract data'),
                ('has_national_identifiers', 'National identifiers'),
                ('has_payroll_corrections', 'Payroll corrections'),
                ('has_payslip_data', 'Payslip data'),
                ('has_cross_border_payroll_data', 'Cross-border payroll data'),
            )
        ]
        ctx['security_fields'] = [
            (label, getattr(review_pack, field_name)) for field_name, label in (
                ('security_encryption', 'Encryption'),
                ('security_access_control', 'Access control'),
                ('security_mfa', 'Multi-factor authentication'),
                ('security_logging', 'Logging'),
                ('security_backup', 'Backup'),
                ('security_incident_response', 'Incident response'),
                ('security_data_segregation', 'Data segregation'),
            )
        ]
        return ctx


class DPAPlaybookListView(LoginRequiredMixin, ListView):
    """Read-only reference: standing DPA negotiation positions. Org-specific
    overrides win over the global default (organization IS NULL) per topic."""
    model = DPAPlaybookPosition
    template_name = 'contracts/dpa_playbook_list.html'
    context_object_name = 'positions'

    def get_queryset(self):
        org = get_user_organization(self.request.user)
        qs = DPAPlaybookPosition.objects.filter(Q(organization=org) | Q(organization__isnull=True))
        by_topic = {}
        for position in qs.order_by('topic', '-organization_id'):
            by_topic.setdefault(position.topic, position)  # org-specific (non-null id, sorted first) wins
        return sorted(by_topic.values(), key=lambda p: p.topic)


def _get_owned_review_pack_or_404(request, pk):
    org = get_user_organization(request.user)
    queryset = DPAReviewPack.objects.filter(organization=org).select_related('contract') if org else DPAReviewPack.objects.none()
    return get_object_or_404(queryset, pk=pk)


@require_POST
def dpa_review_run_analysis(request, pk):
    """Suggestion-only re-scan of the DPA text. Persists checklist field
    updates and refreshes auto-detected OPEN risk items (manually-added or
    already-acknowledged/resolved items are left untouched) — never touches
    approval_status."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=403)

    review_pack = _get_owned_review_pack_or_404(request, pk)
    if not can_access_contract_action(request.user, review_pack.contract, ContractAction.EDIT):
        return JsonResponse({'error': 'You do not have permission to analyze this DPA.'}, status=403)

    suggestions = run_dpa_analysis(review_pack)
    review_pack.last_analyzed_at = timezone.now()
    review_pack.save()

    review_pack.risk_items.filter(detected_automatically=True, status=DPARiskItem.Status.OPEN).delete()
    DPARiskItem.objects.bulk_create([
        DPARiskItem(
            review_pack=review_pack, category=s.category, title=s.title, description=s.description,
            severity=s.severity, owners=s.owners, fallback_recommendation=s.fallback_recommendation,
            detected_automatically=True,
        )
        for s in suggestions
    ])

    log_action(
        request.user, AuditLog.Action.UPDATE, 'DPAReviewPack',
        object_id=review_pack.pk, object_repr=str(review_pack), organization=review_pack.organization,
        changes={'event': 'dpa_analysis_run', 'suggested_risk_count': len(suggestions)},
        request=request,
    )
    return JsonResponse({'ok': True, 'suggested_risk_count': len(suggestions)})


@require_POST
def dpa_review_set_approval_status(request, pk):
    """Human-only approval routing. This is the ONLY place approval_status
    can change — the analyzer never sets it, and there is no auto-approve
    path anywhere in this module."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=403)

    review_pack = _get_owned_review_pack_or_404(request, pk)
    if not can_manage_organization(request.user, review_pack.organization):
        return JsonResponse({'error': 'Only an organization owner or admin can set DPA approval status.'}, status=403)

    import json
    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        payload = {}
    new_status = payload.get('status')
    valid_statuses = {choice for choice, _ in DPAReviewPack.ApprovalStatus.choices}
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid approval status.'}, status=400)

    review_pack.approval_status = new_status
    if new_status == DPAReviewPack.ApprovalStatus.APPROVED:
        review_pack.approved_by = request.user
        review_pack.approved_at = timezone.now()
    else:
        review_pack.approved_by = None
        review_pack.approved_at = None
    review_pack.save()

    log_action(
        request.user, AuditLog.Action.UPDATE, 'DPAReviewPack',
        object_id=review_pack.pk, object_repr=str(review_pack), organization=review_pack.organization,
        changes={'event': 'dpa_approval_status_changed', 'status': new_status},
        request=request,
    )
    return JsonResponse({'ok': True, 'status': new_status})


@require_POST
def dpa_risk_item_set_status(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=403)

    org = get_user_organization(request.user)
    queryset = DPARiskItem.objects.filter(review_pack__organization=org).select_related('review_pack__contract') if org else DPARiskItem.objects.none()
    risk_item = get_object_or_404(queryset, pk=pk)
    if not can_access_contract_action(request.user, risk_item.review_pack.contract, ContractAction.EDIT):
        return JsonResponse({'error': 'You do not have permission to update this risk item.'}, status=403)

    import json
    try:
        payload = json.loads(request.body or '{}')
    except ValueError:
        payload = {}
    new_status = payload.get('status')
    valid_statuses = {choice for choice, _ in DPARiskItem.Status.choices}
    if new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid risk item status.'}, status=400)

    risk_item.status = new_status
    risk_item.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'ok': True, 'status': new_status})
