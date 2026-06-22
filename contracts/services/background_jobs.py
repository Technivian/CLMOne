from __future__ import annotations

import logging
from datetime import timedelta

from django.core.management import call_command
from django.db.models import F, Q
from django.utils import timezone

from contracts.models import BackgroundJob

logger = logging.getLogger(__name__)

_STALE_JOB_MINUTES = 30


def _enqueue_rq(job: BackgroundJob, scheduled_at=None) -> None:
    """Enqueue job to Redis via django-rq.  Silently skips if unavailable."""
    try:
        import django_rq
        from contracts.tasks import execute_background_job

        queue = django_rq.get_queue('default')
        if scheduled_at and scheduled_at > timezone.now():
            delay = (scheduled_at - timezone.now()).total_seconds()
            queue.enqueue_in(timedelta(seconds=max(0, delay)), execute_background_job, job.pk)
        else:
            queue.enqueue(execute_background_job, job.pk)
    except Exception:
        logger.debug('RQ enqueue skipped (Redis unavailable); DB polling will pick up job %s', job.pk)


def queue_background_job(job_type: str, organization=None, payload=None, created_by=None, scheduled_at=None):
    if organization is not None and BackgroundJob.objects.filter(
        organization=organization,
        job_type=job_type,
        status=BackgroundJob.Status.PENDING,
        scheduled_at__gte=timezone.now() - timedelta(minutes=15),
    ).exists():
        return BackgroundJob.objects.filter(
            organization=organization,
            job_type=job_type,
            status=BackgroundJob.Status.PENDING,
        ).order_by('-scheduled_at', '-created_at').first()
    job = BackgroundJob.objects.create(
        organization=organization,
        job_type=job_type,
        payload=payload or {},
        created_by=created_by,
        scheduled_at=scheduled_at or timezone.now(),
    )
    _enqueue_rq(job, scheduled_at=scheduled_at)
    return job


def claim_background_job(job: BackgroundJob) -> bool:
    """Atomically transition a job PENDING -> RUNNING.

    Overlap protection: a single conditional UPDATE means only ONE processor can
    claim a given job, even if a continuous worker, a cron drain, and an RQ
    worker all attempt it concurrently. Returns True if this caller won the
    claim. Portable across SQLite and PostgreSQL (no SELECT ... FOR UPDATE
    needed — the WHERE status=PENDING guard is the lock).
    """
    now = timezone.now()
    claimed = (
        BackgroundJob.objects
        .filter(pk=job.pk, status=BackgroundJob.Status.PENDING)
        .update(
            status=BackgroundJob.Status.RUNNING,
            started_at=now,
            attempt_count=F('attempt_count') + 1,
        )
    )
    if not claimed:
        return False
    job.refresh_from_db(fields=['status', 'started_at', 'attempt_count'])
    return True


def process_background_job(job: BackgroundJob, *, claim: bool = True):
    # Claim atomically; if another processor already took it, do nothing.
    # claim=False is for callers that have already claimed the row (or for
    # routing-only unit tests that pass a stand-in job).
    if claim:
        if not claim_background_job(job):
            logger.info('process_background_job: job %s already claimed; skipping', job.pk)
            return
    else:
        job.status = BackgroundJob.Status.RUNNING
        job.started_at = timezone.now()
        job.attempt_count = int(job.attempt_count or 0) + 1
        job.save(update_fields=['status', 'started_at', 'attempt_count'])
    try:
        if job.job_type == 'send_contract_reminders':
            call_command('send_contract_reminders')
            job.result = {'processed': True}
        elif job.job_type == 'process_document_ocr_reviews':
            call_command('process_document_ocr_reviews')
            job.result = {'processed': True}
        elif job.job_type == 'sync_salesforce_contracts':
            if not job.organization:
                raise RuntimeError('sync_salesforce_contracts requires organization context')
            call_command(
                'sync_salesforce_contracts',
                organization_slug=job.organization.slug,
                limit=int((job.payload or {}).get('limit', 200) or 200),
                dry_run=bool((job.payload or {}).get('dry_run', False)),
            )
            job.result = {'processed': True}
        elif job.job_type == 'run_obligation_reminders':
            if not job.organization:
                raise RuntimeError('run_obligation_reminders requires organization context')
            call_command(
                'run_obligation_reminders',
                organization_slug=job.organization.slug,
                dry_run=bool((job.payload or {}).get('dry_run', False)),
            )
            job.result = {'processed': True}
        elif job.job_type == 'export_dsar_evidence':
            request_id = int((job.payload or {}).get('request_id', 0))
            if not request_id:
                raise RuntimeError('export_dsar_evidence requires request_id in payload')
            call_command('export_dsar_evidence', request_id=request_id)
            job.result = {'processed': True}
        else:
            job.result = {'processed': False, 'reason': 'unknown_job_type'}
        job.status = BackgroundJob.Status.COMPLETED
        job.completed_at = timezone.now()
        job.save(update_fields=['status', 'result', 'completed_at'])
    except Exception as exc:
        max_attempts = max(1, int(job.max_attempts or 3))
        if int(job.attempt_count or 0) < max_attempts:
            delay_minutes = min(60, 5 * (2 ** (int(job.attempt_count or 0) - 1)))
            job.status = BackgroundJob.Status.PENDING
            job.error_message = str(exc)
            job.scheduled_at = timezone.now() + timedelta(minutes=delay_minutes)
            job.save(update_fields=['status', 'error_message', 'scheduled_at'])
        else:
            job.status = BackgroundJob.Status.FAILED
            job.error_message = str(exc)
            job.dead_lettered_at = timezone.now()
            job.completed_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'dead_lettered_at', 'completed_at'])
        raise


def reset_stale_running_jobs() -> int:
    """Move RUNNING jobs that have been stuck for too long back to PENDING.

    Handles the case where a worker dyno crashed mid-execution, leaving the
    BackgroundJob record in RUNNING state with no worker to finish it.
    """
    stale_cutoff = timezone.now() - timedelta(minutes=_STALE_JOB_MINUTES)
    count = BackgroundJob.objects.filter(
        status=BackgroundJob.Status.RUNNING,
        started_at__lt=stale_cutoff,
    ).update(
        status=BackgroundJob.Status.PENDING,
        scheduled_at=timezone.now(),
        error_message='Reset from RUNNING: worker likely crashed.',
    )
    if count:
        logger.warning('reset_stale_running_jobs: reset %d stale job(s) to PENDING', count)
    return count


def process_pending_background_jobs(limit=50):
    reset_stale_running_jobs()
    processed = 0
    pending_jobs = (
        BackgroundJob.objects
        .filter(status=BackgroundJob.Status.PENDING)
        .filter(Q(scheduled_at__isnull=True) | Q(scheduled_at__lte=timezone.now()))
        .order_by('scheduled_at', 'created_at')[:limit]
    )
    for job in pending_jobs:
        process_background_job(job)
        processed += 1
    return processed
