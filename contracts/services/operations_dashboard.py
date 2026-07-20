"""Helpers for the Admin → Operations dashboard."""

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.utils.timesince import timesince

from contracts.models import AuditLog, BackgroundJob, ScheduledJobRun


ALERT_CATALOG = {
    'OBS-P1-5XX-RATE': {
        'severity': 'P1',
        'title': 'Elevated 5xx error rate',
        'impact': 'User-facing requests are failing above the fail SLO.',
        'owner': 'Platform operations',
        'status': 'Open',
        'recommended_action': 'Inspect recent failed requests, stabilize workers, and re-check alert policy.',
    },
    'OBS-P2-5XX-RATE': {
        'severity': 'P2',
        'title': 'Rising 5xx error rate',
        'impact': 'Error rate is approaching the fail SLO and may degrade user experience.',
        'owner': 'Platform operations',
        'status': 'Watching',
        'recommended_action': 'Review recent deployments and failed background jobs before the rate breaches P1.',
    },
    'OBS-P1-SCHEDULER-STALLED': {
        'severity': 'P1',
        'title': 'Scheduler heartbeat stalled',
        'impact': 'Reminders and periodic automation may not be enqueueing work.',
        'owner': 'Platform operations',
        'status': 'Open',
        'recommended_action': 'Verify the reminder scheduler process, then run an operational drill to capture evidence.',
    },
    'OBS-P1-DB-DOWN': {
        'severity': 'P1',
        'title': 'Database health check failed',
        'impact': 'Reads and writes may be unavailable or timing out for all tenants.',
        'owner': 'Platform operations',
        'status': 'Open',
        'recommended_action': 'Check database connectivity and latency, then refresh Operations after recovery.',
    },
    'OBS-P2-DB-SLOW': {
        'severity': 'P2',
        'title': 'Database latency elevated',
        'impact': 'Pages and jobs may feel slow; sustained latency can escalate to an outage.',
        'owner': 'Platform operations',
        'status': 'Watching',
        'recommended_action': 'Inspect slow queries and connection pressure before latency hits the fail threshold.',
    },
}


def _health_from_status(status: str) -> str:
    normalized = (status or '').lower()
    if normalized in {'healthy', 'ok', 'success', 'clear'}:
        return 'healthy'
    if normalized in {'slow', 'attention', 'watching', 'p2', 'unknown'}:
        return 'attention'
    if normalized in {'stale', 'down', 'failed', 'danger', 'p1', 'critical'}:
        return 'critical'
    return 'neutral'


def _trend_for_health(health: str) -> str:
    if health == 'healthy':
        return 'Stable'
    if health == 'attention':
        return 'Degrading'
    if health == 'critical':
        return 'Critical'
    return 'Unchanged'


def build_metric_cards(*, scheduler, database, alerts, request_metrics) -> list[dict]:
    """Contextual KPI cards: value + time range + threshold + trend + health."""
    scheduler_health = _health_from_status(scheduler.get('status'))
    db_health = _health_from_status(database.get('status'))
    alert_health = {
        'OK': 'healthy',
        'P2': 'attention',
        'P1': 'critical',
    }.get(alerts.get('alert_status'), 'neutral')

    warn_pct = alerts.get('inputs', {}).get('slo_thresholds', {}).get(
        'five_xx_warn_pct',
        float(getattr(settings, 'SLO_5XX_RATE_WARN_PCT', 0.8)),
    )
    fail_pct = alerts.get('inputs', {}).get('slo_thresholds', {}).get(
        'five_xx_fail_pct',
        float(getattr(settings, 'SLO_5XX_RATE_FAIL_PCT', 2.0)),
    )
    stale_after = scheduler.get('stale_after_seconds') or (
        int(getattr(settings, 'REMINDER_SCHEDULER_EXPECTED_INTERVAL_MINUTES', 60)) * 60 * 2
    )
    db_warn = database.get('warn_ms', getattr(settings, 'HEALTH_DB_LATENCY_WARN_MS', 250))
    db_fail = database.get('fail_ms', getattr(settings, 'HEALTH_DB_LATENCY_FAIL_MS', 1500))

    avg_latency = request_metrics.get('avg_latency_ms') or 0
    request_health = 'healthy'
    if avg_latency >= db_fail:
        request_health = 'critical'
    elif avg_latency >= db_warn:
        request_health = 'attention'

    return [
        {
            'label': 'Scheduler',
            'value': (scheduler.get('status') or 'unknown').title(),
            'time_range': 'Live heartbeat',
            'threshold': f'Stale after {int(stale_after // 60)}m',
            'trend': _trend_for_health(scheduler_health),
            'health': scheduler_health,
            'note': (
                f"Last success {scheduler.get('seconds_since_success') or 'n/a'}s ago"
                if scheduler.get('seconds_since_success') is not None
                else 'No heartbeat recorded yet'
            ),
        },
        {
            'label': 'Database',
            'value': (database.get('status') or 'unknown').title(),
            'time_range': 'Live probe',
            'threshold': f'Warn {db_warn}ms · Fail {db_fail}ms',
            'trend': _trend_for_health(db_health),
            'health': db_health,
            'note': f"{database.get('latency_ms', '—')}ms latency",
        },
        {
            'label': 'Alerts',
            'value': alerts.get('alert_status') or 'OK',
            'time_range': 'Current window',
            'threshold': f'5xx warn {warn_pct}% · fail {fail_pct}%',
            'trend': _trend_for_health(alert_health),
            'health': alert_health,
            'note': f"{alerts.get('five_xx_rate_pct', 0)}% 5xx rate",
        },
        {
            'label': 'Requests',
            'value': request_metrics.get('total_requests', 0),
            'time_range': 'Process lifetime',
            'threshold': f'Latency warn {db_warn}ms',
            'trend': _trend_for_health(request_health),
            'health': request_health,
            'note': f"Avg {request_metrics.get('avg_latency_ms', 0)}ms latency",
        },
    ]


def build_incidents(*, alerts, failed_job_runs_24h: int) -> list[dict]:
    """Critical/open issues for the incident banner."""
    incidents = []
    for code in list(alerts.get('p1_alerts') or []) + list(alerts.get('p2_alerts') or []):
        meta = ALERT_CATALOG.get(code, {
            'severity': 'P1' if code in (alerts.get('p1_alerts') or []) else 'P2',
            'title': code,
            'impact': 'Operational signal requires review.',
            'owner': 'Platform operations',
            'status': 'Open',
            'recommended_action': 'Open the Alerts tab and follow the runbook.',
        })
        incidents.append({**meta, 'code': code})

    if failed_job_runs_24h:
        incidents.append({
            'code': 'OPS-SCHEDULED-FAILURES',
            'severity': 'P2' if failed_job_runs_24h < 3 else 'P1',
            'title': 'Scheduled job failures in the last 24 hours',
            'impact': f'{failed_job_runs_24h} failed or partial scheduled run(s) for this organization.',
            'owner': 'Workspace admin',
            'status': 'Open',
            'recommended_action': 'Open Schedules, inspect error summaries, and retry related background jobs.',
        })
    return incidents


def build_queue_health(job_counts: dict) -> dict:
    pending = int(job_counts.get('pending') or 0)
    running = int(job_counts.get('running') or 0)
    completed = int(job_counts.get('completed') or 0)
    failed = int(job_counts.get('failed') or 0)
    active = pending + running
    if failed:
        health = 'critical'
        label = 'Needs attention'
    elif active:
        health = 'attention'
        label = 'Processing'
    else:
        health = 'healthy'
        label = 'Clear'
    badge_tone = {
        'healthy': 'success',
        'attention': 'attention',
        'critical': 'danger',
    }.get(health, 'neutral')
    return {
        'health': health,
        'label': label,
        'badge_tone': badge_tone,
        'pending': pending,
        'running': running,
        'completed': completed,
        'failed': failed,
        'active': active,
        'summary': f'{active} active · {failed} failed · {completed} completed',
    }


def _format_duration(delta: timedelta | None) -> str:
    if delta is None:
        return '—'
    total_seconds = max(0, int(delta.total_seconds()))
    if total_seconds < 60:
        return f'{total_seconds}s'
    minutes, seconds = divmod(total_seconds, 60)
    if minutes < 60:
        return f'{minutes}m {seconds}s'
    hours, minutes = divmod(minutes, 60)
    return f'{hours}h {minutes}m'


def job_duration(job: BackgroundJob) -> str:
    if job.started_at and job.completed_at:
        return _format_duration(job.completed_at - job.started_at)
    if job.started_at and job.status == BackgroundJob.Status.RUNNING:
        return _format_duration(timezone.now() - job.started_at)
    return '—'


def job_trigger_label(job: BackgroundJob) -> str:
    payload = job.payload if isinstance(job.payload, dict) else {}
    trigger = payload.get('trigger') or payload.get('source')
    if trigger:
        return str(trigger).replace('_', ' ').title()
    if job.created_by_id:
        return 'Manual'
    return 'Scheduler'


def job_status_tone(status: str) -> str:
    return {
        BackgroundJob.Status.COMPLETED: 'success',
        BackgroundJob.Status.RUNNING: 'progress',
        BackgroundJob.Status.PENDING: 'neutral',
        BackgroundJob.Status.FAILED: 'danger',
    }.get(status, 'neutral')


def scheduled_status_tone(status: str) -> str:
    return {
        ScheduledJobRun.Status.SUCCESS: 'success',
        ScheduledJobRun.Status.RUNNING: 'progress',
        ScheduledJobRun.Status.PARTIAL: 'attention',
        ScheduledJobRun.Status.FAILED: 'danger',
        ScheduledJobRun.Status.SKIPPED: 'neutral',
    }.get(status, 'neutral')


def serialize_job_row(job: BackgroundJob) -> dict:
    return {
        'id': job.id,
        'job_type': job.job_type,
        'status': job.status,
        'status_display': job.get_status_display(),
        'status_tone': job_status_tone(job.status),
        'started_at': job.started_at or job.created_at,
        'duration': job_duration(job),
        'attempts': f'{job.attempt_count}/{job.max_attempts}',
        'trigger': job_trigger_label(job),
        'error_message': job.error_message or '',
        'can_retry': job.status == BackgroundJob.Status.FAILED,
        'result': job.result or {},
        'payload': job.payload or {},
        'dead_lettered_at': job.dead_lettered_at,
        'created_at': job.created_at,
        'completed_at': job.completed_at,
    }


def operations_audit_events(organization, *, limit: int = 25):
    """Recent audit events relevant to operations actions and job evidence."""
    from django.db.models import Q

    return list(
        AuditLog.objects.filter(organization=organization)
        .filter(
            Q(model_name__in=['BackgroundJob', 'ScheduledJobRun'])
            | Q(changes__event__in=[
                'operations_drill_run',
                'background_job_retried',
            ])
            | Q(job_run_id__isnull=False)
        )
        .select_related('user')
        .order_by('-timestamp')[:limit]
    )


def relative_updated_label(moment=None) -> str:
    moment = moment or timezone.now()
    return f'Updated {timesince(moment)} ago'
