from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from contracts.middleware import log_action
from contracts.models import AuditLog, Notification
from contracts.tenancy import get_user_organization
from contracts.view_support import TenantScopedQuerysetMixin


class AuditLogListView(LoginRequiredMixin, ListView):
    model = AuditLog
    template_name = 'contracts/audit_log_list.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        org = get_user_organization(self.request.user)
        if org is None:
            return AuditLog.objects.none()
        # Tenant boundary: ONLY this org's rows. New rows carry the organization
        # FK; legacy rows are matched by changes.organization_id but still scoped
        # to this org (never another tenant's data).
        queryset = AuditLog.objects.select_related('user', 'organization').filter(
            Q(organization=org)
            | Q(organization__isnull=True, changes__organization_id=org.id)
        )
        action = self.request.GET.get('action')
        model = self.request.GET.get('model')
        event_type = self.request.GET.get('event_type')
        outcome = self.request.GET.get('outcome')
        actor = self.request.GET.get('actor')
        since = self.request.GET.get('since')
        until = self.request.GET.get('until')
        if action:
            queryset = queryset.filter(action=action)
        if model:
            queryset = queryset.filter(model_name=model)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if outcome:
            queryset = queryset.filter(outcome=outcome)
        if actor:
            queryset = queryset.filter(user__username=actor)
        if since:
            queryset = queryset.filter(timestamp__date__gte=since)
        if until:
            queryset = queryset.filter(timestamp__date__lte=until)
        return queryset.order_by('-timestamp')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        org = get_user_organization(self.request.user)
        if org is not None:
            from contracts.services.audit import verify_chain
            ctx['chain_status'] = verify_chain(org.id)
        return ctx


@login_required
def notification_list(request):
    all_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    filter_type = (request.GET.get('type') or '').strip().upper()
    filter_state = (request.GET.get('state') or '').strip().lower()

    if filter_type and filter_type in {choice for choice, _ in Notification.NotificationType.choices}:
        all_notifications = all_notifications.filter(notification_type=filter_type)
    if filter_state == 'unread':
        all_notifications = all_notifications.filter(is_read=False)
    elif filter_state == 'read':
        all_notifications = all_notifications.filter(is_read=True)

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    notifications = all_notifications[:50]
    return render(request, 'contracts/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_type': filter_type,
        'filter_state': filter_state,
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    log_action(
        request.user,
        AuditLog.Action.UPDATE,
        'Notification',
        object_id=notification.id,
        object_repr=str(notification),
        changes={'event': 'mark_notification_read'},
        request=request,
    )
    if notification.link:
        return redirect(notification.link)
    return redirect('contracts:notification_list')


@login_required
@require_POST
def mark_all_notifications_read(request):
    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)
    updated_count = unread_qs.update(is_read=True)
    log_action(
        request.user,
        AuditLog.Action.UPDATE,
        'Notification',
        object_repr=f'{updated_count} notifications',
        changes={'event': 'mark_all_notifications_read', 'count': updated_count},
        request=request,
    )
    return redirect('contracts:notification_list')
