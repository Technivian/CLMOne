"""Job-run evidence + overlap protection for scheduled/maintenance jobs.

Every scheduled job records a ``ScheduledJobRun`` row so operators can prove,
from the production database, that the job ran for a given tenant and what it
changed. This replaces the previous (misleading) practice of treating green CI
artifacts — produced against an empty SQLite DB — as evidence of tenant work.

Usage::

    with record_job_run('run_retention_jobs', organization=org) as run:
        run.records_examined += 1
        ...
        run.records_changed += 1
    # status is finalized to SUCCESS, or FAILED/PARTIAL on error, automatically.

Overlap protection: ``record_job_run(..., prevent_overlap=True)`` skips the run
(status SKIPPED) if another run of the same (job_name, organization) has been
RUNNING within ``overlap_window``, so two schedulers can't double-execute.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import timedelta

from django.utils import timezone

from contracts.models import ScheduledJobRun

logger = logging.getLogger(__name__)

_ERROR_SUMMARY_MAX = 2000
_DEFAULT_OVERLAP_WINDOW = timedelta(minutes=30)


class JobRunSkipped(Exception):
    """Raised internally when a run is skipped due to an in-flight overlap."""


class _RunAccumulator:
    """Mutable counters a job body updates; flushed to the row on completion."""

    def __init__(self, row: ScheduledJobRun):
        self._row = row
        self.records_examined = 0
        self.records_changed = 0
        self.notifications_created = 0
        self.partial = False  # set True to force PARTIAL status on success exit
        self.detail: dict = {}

    @property
    def run_id(self):
        return self._row.run_id

    @property
    def row(self) -> ScheduledJobRun:
        return self._row


def _has_active_run(job_name: str, organization, window: timedelta) -> bool:
    cutoff = timezone.now() - window
    return ScheduledJobRun.objects.filter(
        job_name=job_name,
        organization=organization,
        status=ScheduledJobRun.Status.RUNNING,
        started_at__gte=cutoff,
    ).exists()


@contextmanager
def record_job_run(
    job_name: str,
    *,
    organization=None,
    prevent_overlap: bool = False,
    overlap_window: timedelta = _DEFAULT_OVERLAP_WINDOW,
):
    """Context manager that records a ScheduledJobRun around a job body.

    Yields a ``_RunAccumulator``; the caller mutates its counters. On clean exit
    the run is marked SUCCESS (or PARTIAL if ``acc.partial`` is set). On an
    exception the run is marked FAILED, the error summary recorded (truncated,
    never including secrets/document bodies), and the exception re-raised.

    If ``prevent_overlap`` and another run is already in flight, yields ``None``
    after recording a SKIPPED row; the caller should treat ``None`` as "did not
    run".
    """
    if prevent_overlap and _has_active_run(job_name, organization, overlap_window):
        ScheduledJobRun.objects.create(
            job_name=job_name,
            organization=organization,
            status=ScheduledJobRun.Status.SKIPPED,
            finished_at=timezone.now(),
            error_summary='Skipped: another run was already in progress.',
        )
        logger.info('job_run skipped (overlap): job=%s org=%s', job_name, getattr(organization, 'slug', None))
        yield None
        return

    row = ScheduledJobRun.objects.create(
        job_name=job_name,
        organization=organization,
        status=ScheduledJobRun.Status.RUNNING,
        started_at=timezone.now(),
    )
    acc = _RunAccumulator(row)
    try:
        yield acc
    except Exception as exc:
        row.status = ScheduledJobRun.Status.FAILED
        row.finished_at = timezone.now()
        row.records_examined = acc.records_examined
        row.records_changed = acc.records_changed
        row.notifications_created = acc.notifications_created
        row.error_summary = f'{type(exc).__name__}: {exc}'[:_ERROR_SUMMARY_MAX]
        row.detail = acc.detail
        row.save(update_fields=[
            'status', 'finished_at', 'records_examined', 'records_changed',
            'notifications_created', 'error_summary', 'detail',
        ])
        logger.warning('job_run failed: job=%s org=%s err=%s',
                       job_name, getattr(organization, 'slug', None), exc)
        # Audit scheduled-job failures (security/governance signal). Written
        # outside the business transaction; links to the ScheduledJobRun. Stores
        # only the truncated exception type+message, never a full traceback.
        try:
            from contracts.services.audit import append_audit
            append_audit(
                action='UPDATE', model_name='ScheduledJobRun',
                organization=organization, user=None,
                object_id=row.pk, object_repr=f'{job_name} run {row.run_id}',
                event_type='job.failed', actor_type='scheduled_job', outcome='failure',
                job_run_id=row.run_id,
                changes={'event': 'job.failed', 'job_name': job_name,
                         'error': row.error_summary},
            )
        except Exception:
            logger.exception('audit job.failed write failed for %s', job_name)
        raise
    else:
        row.status = ScheduledJobRun.Status.PARTIAL if acc.partial else ScheduledJobRun.Status.SUCCESS
        row.finished_at = timezone.now()
        row.records_examined = acc.records_examined
        row.records_changed = acc.records_changed
        row.notifications_created = acc.notifications_created
        row.detail = acc.detail
        row.save(update_fields=[
            'status', 'finished_at', 'records_examined', 'records_changed',
            'notifications_created', 'detail',
        ])


def recent_runs(limit: int = 50, organization=None):
    qs = ScheduledJobRun.objects.all()
    if organization is not None:
        qs = qs.filter(organization=organization)
    return list(qs[:limit])
