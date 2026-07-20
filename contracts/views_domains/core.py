import hashlib
import logging
from datetime import date, timedelta
from urllib.parse import urlparse, urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView, View
from django.contrib.auth import get_user_model
from django.core.management import call_command

from contracts.forms import UserProfileForm, RegistrationForm, LoginForm


def _safe_next(request, fallback='/dashboard/') -> str:
    """Return next URL only if it is a safe same-host redirect target."""
    url = request.POST.get('next') or request.GET.get('next') or ''
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return url
    return fallback
from contracts.models import AuditLog, BackgroundJob, Case, CaseMatter, Client, Deadline, Invoice, Notification, OrganizationMembership, OrgPolicy, RiskLog, TimeEntry, TrustAccount, UserProfile, Workflow, CaseSignal, ApprovalRequest, SignatureRequest, DSARRequest, Document
from contracts.middleware import log_action
from contracts.observability import db_health_snapshot, request_metrics_snapshot, scheduler_health_snapshot, evaluate_alert_policy
from contracts.permissions import can_manage_organization
from contracts.services.operations_dashboard import (
    build_incidents,
    build_metric_cards,
    build_queue_health,
    operations_audit_events,
    relative_updated_label,
    scheduled_status_tone,
    serialize_job_row,
)
from contracts.tenancy import get_user_organization, scope_queryset_for_organization

User = get_user_model()
logger = logging.getLogger(__name__)


def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')


def health_check(request):
    response_format = request.GET.get('format', '').lower()
    if response_format != 'json':
        return HttpResponse('OK', content_type='text/plain')

    scheduler = scheduler_health_snapshot()
    database = db_health_snapshot()
    request_metrics = request_metrics_snapshot()
    status = 'ok'
    status_code = 200
    if scheduler.get('status') == 'stale' or database.get('status') == 'down':
        status = 'degraded'
        status_code = 503
    elif database.get('status') == 'slow':
        status = 'degraded'

    return JsonResponse(
        {
            'status': status,
            'scheduler': scheduler,
            'database': database,
            'request_metrics': request_metrics,
        },
        status=status_code,
    )


OPERATIONS_TABS = ('overview', 'jobs', 'schedules', 'alerts', 'audit')


def _operations_redirect(tab='overview', job_id=None):
    url = reverse('operations_dashboard')
    params = {}
    if tab and tab != 'overview':
        params['tab'] = tab
    if job_id:
        params['job'] = job_id
        params['tab'] = 'jobs'
    if params:
        return f'{url}?{urlencode(params)}'
    return url


@login_required
@require_http_methods(['GET', 'POST'])
def operations_dashboard(request):
    org = get_user_organization(request.user)
    if not org:
        messages.error(request, 'No active organization found.')
        return redirect('settings_hub')

    if not can_manage_organization(request.user, org):
        return HttpResponseForbidden('Only organization owners/admins can access Operations.')

    tab = (request.GET.get('tab') or 'overview').lower()
    if tab not in OPERATIONS_TABS:
        tab = 'overview'

    if request.method == 'POST':
        action = (request.POST.get('action') or '').strip()
        if action == 'run_drill':
            alert_exit_code = 0
            try:
                call_command('run_operational_drill')
            except SystemExit as exc:
                # P1/P2 from evaluate_observability_alerts is drill evidence, not a failed action.
                alert_exit_code = int(getattr(exc, 'code', 0) or 0)
            summary = cache.get('operations_drill.last_summary') or (
                'Queued reminder/OCR work, processed pending jobs, and evaluated alert policy.'
            )
            if alert_exit_code == 2 and 'P1' not in summary:
                summary += ' Alert policy reported P1.'
            elif alert_exit_code == 1 and 'P2' not in summary:
                summary += ' Alert policy reported P2.'
            # Durable evidence — cache is best-effort (Redis IGNORE_EXCEPTIONS can drop writes).
            cache.set('operations_drill.last_run_iso', timezone.now().isoformat(), timeout=None)
            cache.set('operations_drill.last_summary', summary, timeout=None)
            log_action(
                request.user,
                AuditLog.Action.UPDATE,
                'BackgroundJob',
                object_repr='Operational drill',
                changes={
                    'event': 'operations_drill_run',
                    'organization_id': org.id,
                    'summary': summary,
                    'alert_exit_code': alert_exit_code,
                },
                request=request,
                organization=org,
            )
            if alert_exit_code == 2:
                messages.warning(request, 'Operational drill completed with P1 alerts. Review the Alerts tab.')
            elif alert_exit_code == 1:
                messages.warning(request, 'Operational drill completed with P2 alerts. Review the Alerts tab.')
            else:
                messages.success(request, 'Operational drill completed. Queue and alert evidence refreshed.')
            return redirect(_operations_redirect(tab='overview'))

        if action == 'retry_job':
            job_id = request.POST.get('job_id')
            job = get_object_or_404(BackgroundJob, id=job_id, organization=org)
            if job.status != BackgroundJob.Status.FAILED:
                messages.error(request, f'Job {job.id} is {job.status}, not FAILED.')
            else:
                job.status = BackgroundJob.Status.PENDING
                job.attempt_count = 0
                job.error_message = ''
                job.dead_lettered_at = None
                job.scheduled_at = timezone.now()
                job.save(update_fields=[
                    'status', 'attempt_count', 'error_message', 'dead_lettered_at', 'scheduled_at',
                ])
                log_action(
                    request.user,
                    AuditLog.Action.UPDATE,
                    'BackgroundJob',
                    object_id=job.id,
                    object_repr=str(job),
                    changes={
                        'event': 'background_job_retried',
                        'organization_id': org.id,
                        'job_type': job.job_type,
                    },
                    request=request,
                    organization=org,
                )
                messages.success(request, f'Re-queued {job.job_type} (#{job.id}).')
            return redirect(_operations_redirect(tab='jobs', job_id=job.id))

        messages.error(request, 'Unknown Operations action.')
        return redirect(_operations_redirect(tab=tab))

    from contracts.models import ScheduledJobRun

    job_qs = BackgroundJob.objects.filter(organization=org).select_related('created_by')
    recent_jobs = list(job_qs.order_by('-created_at')[:50])
    job_counts = {
        'pending': job_qs.filter(status=BackgroundJob.Status.PENDING).count(),
        'running': job_qs.filter(status=BackgroundJob.Status.RUNNING).count(),
        'completed': job_qs.filter(status=BackgroundJob.Status.COMPLETED).count(),
        'failed': job_qs.filter(status=BackgroundJob.Status.FAILED).count(),
    }
    org_runs = ScheduledJobRun.objects.filter(organization=org)
    recent_job_runs = list(org_runs.order_by('-started_at')[:25])
    failed_job_runs_24h = org_runs.filter(
        status__in=[ScheduledJobRun.Status.FAILED, ScheduledJobRun.Status.PARTIAL],
        started_at__gte=timezone.now() - timedelta(hours=24),
    ).count()

    scheduler = scheduler_health_snapshot()
    database = db_health_snapshot()
    request_metrics = request_metrics_snapshot()
    alerts = evaluate_alert_policy()
    now = timezone.now()

    selected_job = None
    selected_job_row = None
    selected_job_audit = []
    job_param = request.GET.get('job')
    if job_param:
        selected_job = job_qs.filter(id=job_param).first()
        if selected_job:
            selected_job_row = serialize_job_row(selected_job)
            selected_job_audit = list(
                AuditLog.objects.filter(organization=org, model_name='BackgroundJob', object_id=selected_job.id)
                .select_related('user')
                .order_by('-timestamp')[:10]
            )

    job_rows = [serialize_job_row(job) for job in recent_jobs]
    scheduled_rows = [
        {
            'id': run.id,
            'job_name': run.job_name,
            'status': run.status,
            'status_display': run.get_status_display(),
            'status_tone': scheduled_status_tone(run.status),
            'started_at': run.started_at,
            'finished_at': run.finished_at,
            'records_examined': run.records_examined,
            'records_changed': run.records_changed,
            'notifications_created': run.notifications_created,
            'error_summary': run.error_summary or '',
            'run_id': str(run.run_id),
        }
        for run in recent_job_runs
    ]

    drill_state = {
        'last_run_iso': cache.get('operations_drill.last_run_iso'),
        'last_summary': cache.get('operations_drill.last_summary'),
    }
    if not drill_state['last_run_iso']:
        latest_drill = (
            AuditLog.objects.filter(
                organization=org,
                changes__event='operations_drill_run',
            )
            .order_by('-timestamp')
            .first()
        )
        if latest_drill:
            drill_state = {
                'last_run_iso': latest_drill.timestamp.isoformat(),
                'last_summary': (latest_drill.changes or {}).get('summary') or '',
            }

    context = {
        'organization': org,
        'hide_app_footer': True,
        'active_tab': tab,
        'operations_tabs': [
            {'id': 'overview', 'label': 'Overview'},
            {'id': 'jobs', 'label': 'Jobs'},
            {'id': 'schedules', 'label': 'Schedules'},
            {'id': 'alerts', 'label': 'Alerts'},
            {'id': 'audit', 'label': 'Audit'},
        ],
        'scheduler': scheduler,
        'database': database,
        'request_metrics': request_metrics,
        'alerts': alerts,
        'metric_cards': build_metric_cards(
            scheduler=scheduler,
            database=database,
            alerts=alerts,
            request_metrics=request_metrics,
        ),
        'incidents': build_incidents(alerts=alerts, failed_job_runs_24h=failed_job_runs_24h),
        'queue_health': build_queue_health(job_counts),
        'job_counts': job_counts,
        'job_rows': job_rows,
        'scheduled_rows': scheduled_rows,
        'failed_job_runs_24h': failed_job_runs_24h,
        'operations_audit': operations_audit_events(org),
        'selected_job': selected_job,
        'selected_job_row': selected_job_row,
        'selected_job_audit': selected_job_audit,
        'last_updated_at': now,
        'last_updated_label': relative_updated_label(now),
        'page_subtitle': (
            f'Queue health, scheduler status, and operational evidence for {org.name}.'
        ),
        'drill_state': drill_state,
    }
    return render(request, 'contracts/operations_dashboard.html', context)


@login_required
def switch_organization(request):
    org_id = request.POST.get('organization_id')
    membership = (
        OrganizationMembership.objects
        .filter(
            user=request.user,
            is_active=True,
            organization__is_active=True,
            organization_id=org_id,
        )
        .select_related('organization')
        .first()
    )
    if membership:
        request.session['active_organization_id'] = membership.organization_id
        log_action(
            request.user,
            AuditLog.Action.UPDATE,
            'OrganizationMembership',
            object_id=membership.id,
            object_repr=str(membership),
            changes={'event': 'switch_organization', 'organization_id': membership.organization_id},
            request=request,
        )
        messages.success(request, f'Switched to {membership.organization.name}.')
    else:
        messages.error(request, 'You do not have access to that organization.')
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


class ProfileView(LoginRequiredMixin, View):
    def get(self, request):
        profile = get_or_create_profile(request.user)
        form = UserProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        })
        return render(request, 'profile.html', {'form': form, 'profile': profile})

    def post(self, request):
        profile = get_or_create_profile(request.user)
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            request.user.first_name = form.cleaned_data.get('first_name', '')
            request.user.last_name = form.cleaned_data.get('last_name', '')
            request.user.email = form.cleaned_data.get('email', '')
            request.user.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        return render(request, 'profile.html', {'form': form, 'profile': profile})


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SignUpView(FormView):
    form_class = RegistrationForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/register.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            logger.exception('signup_view_failed')
            if settings.DEBUG:
                return HttpResponse(f'Signup failed: {exc.__class__.__name__}: {exc}', status=500, content_type='text/plain')
            raise  # production: render branded handler500, no internals leaked

    def form_valid(self, form):
        self.object = form.save()
        UserProfile.objects.get_or_create(user=self.object)

        login(
            self.request,
            self.object,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        return super().form_valid(form)


@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(never_cache, name='dispatch')
class LoginView(FormView):
    form_class = LoginForm
    success_url = reverse_lazy('dashboard')
    template_name = 'registration/login.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as exc:
            logger.exception('login_view_failed')
            if settings.DEBUG:
                return HttpResponse(f'Login failed: {exc.__class__.__name__}: {exc}', status=500, content_type='text/plain')
            raise  # production: render branded handler500, no internals leaked

    def form_valid(self, form):
        user = form.cleaned_data['user']
        login(
            self.request,
            user,
            backend='django.contrib.auth.backends.ModelBackend',
        )
        if not form.cleaned_data.get('remember'):
            self.request.session.set_expiry(0)

        # MFA enforcement (fail-closed): authoritative source is
        # Organization.require_mfa via the mfa_policy service. We deliberately do
        # NOT wrap this in a broad try/except — a failure here must block login,
        # never silently bypass MFA. See contracts/services/mfa_policy.py.
        from contracts.tenancy import get_user_organization
        from contracts.services.mfa_policy import organization_requires_mfa
        org = get_user_organization(user)
        if organization_requires_mfa(org):
            profile, _ = UserProfile.objects.get_or_create(user=user)
            # A fresh challenge is required this session.
            self.request.session['mfa_verified'] = False
            if not profile.mfa_enabled:
                return redirect('mfa_enroll')
            code = profile.issue_mfa_enrollment_code()
            _send_mfa_email(user, code)
            return redirect('mfa_challenge')

        next_url = _safe_next(self.request)
        if next_url != '/dashboard/':
            return redirect(next_url)
        return super().form_valid(form)


if settings.DEBUG:
    SignUpView = method_decorator(csrf_exempt, name='dispatch')(SignUpView)


import json


@csrf_exempt
def csp_report(request):
    if request.method != 'POST':
        return HttpResponse(status=405)
    try:
        report = json.loads(request.body.decode('utf-8', errors='replace'))
        try:
            import sentry_sdk
            violation = (report.get('csp-report') or report).get('violated-directive', 'unknown')
            with sentry_sdk.new_scope() as scope:
                scope.set_context('csp_report', report)
                sentry_sdk.capture_message(f'CSP Violation: {violation}', level='warning')
        except Exception:
            logger.warning('CSP violation (Sentry unavailable): %s', report)
    except Exception:
        pass
    return HttpResponse(status=204)


# ---------------------------------------------------------------------------
# MFA support
# ---------------------------------------------------------------------------

def _send_mfa_email(user, code: str) -> None:
    """Thin wrapper kept for call-site compatibility; delegates to notifications service."""
    from contracts.services.notifications import send_mfa_code_email
    send_mfa_code_email(user, code)


class MfaRequiredMixin:
    """Block access if the org requires MFA and this session hasn't verified it."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Fail-closed: authoritative MFA check, no broad exception swallow.
            from contracts.tenancy import get_user_organization
            from contracts.services.mfa_policy import organization_requires_mfa
            org = get_user_organization(request.user)
            if organization_requires_mfa(org) and not request.session.get('mfa_verified'):
                from django.urls import reverse
                redirect_url = reverse('mfa_challenge') + '?' + urlencode({'next': request.path})
                return redirect(redirect_url)
        return super().dispatch(request, *args, **kwargs)


@login_required
def mfa_challenge(request):
    """Enter the emailed OTP to set the mfa_verified session flag."""
    next_url = _safe_next(request)
    error = None

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        if profile.check_mfa_code(code):
            # Valid OTP — mark session verified.
            request.session['mfa_verified'] = True
            return redirect(next_url)

        # Try as a recovery code via the canonical service (atomic consumption,
        # audit event, replay prevention, suspicious-use notification).
        from contracts.services.recovery_codes import consume_recovery_code
        from contracts.tenancy import get_user_organization
        org = get_user_organization(request.user)
        if consume_recovery_code(profile, code, request=request, organization=org):
            return redirect(next_url)

        error = 'Invalid or expired code. Request a new one below.'

    return render(request, 'contracts/mfa_challenge.html', {
        'next': next_url,
        'error': error,
    })


@login_required
def mfa_challenge_resend(request):
    """Re-issue the OTP and redirect back to the challenge page."""
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        code = profile.issue_mfa_enrollment_code()
        _send_mfa_email(request.user, code)
        messages.success(request, 'A new verification code has been sent to your email.')
    next_url = _safe_next(request)
    return redirect(reverse('mfa_challenge') + '?' + urlencode({'next': next_url}))


@login_required
def mfa_enroll(request):
    """First-time MFA enrollment: issue code, verify, activate MFA for user."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            code = profile.issue_mfa_enrollment_code()
            _send_mfa_email(request.user, code)
            messages.success(request, 'Verification code sent to your email.')
            return redirect('mfa_enroll')

        code = request.POST.get('code', '').strip()
        if profile.verify_mfa_enrollment_code(code):
            request.session['mfa_verified'] = True
            messages.success(request, 'MFA enabled. Your account is now protected.')
            # Security notification: inform the user MFA was enabled on their account.
            try:
                from contracts.services.notifications import send_mfa_enrolled_notification
                send_mfa_enrolled_notification(request.user)
            except Exception:
                logger.exception('mfa_enrolled_notification failed user=%s', request.user.pk)
            return redirect('dashboard')
        error = 'Invalid or expired code. Please try again.'

    return render(request, 'contracts/mfa_enroll.html', {
        'profile': profile,
        'error': error,
    })


# ---------------------------------------------------------------------------
# Password recovery (Phase 5L)
# ---------------------------------------------------------------------------

class CLMOnePasswordResetForm(PasswordResetForm):
    """Override domain/protocol so reset links use APP_BASE_URL, never request.get_host()."""

    def save(self, *args, **kwargs):
        base = getattr(settings, 'APP_BASE_URL', '') or 'http://localhost:8000'
        parsed = urlparse(base)
        kwargs['domain_override'] = parsed.netloc
        kwargs['use_https'] = parsed.scheme == 'https'
        return super().save(*args, **kwargs)


class CLMOnePasswordResetView(PasswordResetView):
    """Password reset request view with rate limiting and canonical URL links."""

    form_class = CLMOnePasswordResetForm
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    # Rate limit: 3 reset requests per email per hour.
    _RATE_LIMIT = 3
    _RATE_WINDOW = 3600

    def form_valid(self, form):
        email = form.cleaned_data.get('email', '').lower().strip()
        # Hash the email for the cache key to avoid storing PII.
        email_key = hashlib.sha256(email.encode()).hexdigest()[:20]
        rl_key = f'pwd_reset_rl:{email_key}'
        attempts = cache.get(rl_key, 0)
        if attempts >= self._RATE_LIMIT:
            # Generic redirect — does not reveal rate limiting to callers.
            return redirect(self.get_success_url())
        cache.set(rl_key, attempts + 1, timeout=self._RATE_WINDOW)
        return super().form_valid(form)


class CLMOnePasswordResetConfirmView(PasswordResetConfirmView):
    """Password reset confirmation view; audits on successful completion."""

    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Audit password reset completion. Token/uid never stored.
        try:
            from contracts.services.audit import append_audit
            append_audit(
                action='UPDATE',
                model_name='User',
                organization=None,
                user=form.user,
                object_id=form.user.pk,
                object_repr=form.user.username,
                event_type='auth.password_reset_completed',
                actor_type='human',
                outcome='success',
                changes={'event': 'auth.password_reset_completed'},
            )
        except Exception:
            logger.exception('password_reset audit failed user=%s', getattr(form.user, 'pk', None))
        return response
