"""RQ task functions for background job execution.

Each function here is a thin wrapper that loads a BackgroundJob by ID
and delegates to process_background_job().  The DB record remains the
source of truth for status/retries; RQ provides the execution runtime.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def execute_background_job(job_id: int) -> None:
    """Entry point called by the RQ worker for a single BackgroundJob."""
    import django
    django.setup()  # safe to call multiple times; no-op after first call

    from contracts.models import BackgroundJob
    from contracts.services.background_jobs import process_background_job

    try:
        job = BackgroundJob.objects.get(pk=job_id)
    except BackgroundJob.DoesNotExist:
        logger.warning('execute_background_job: job %s not found (already deleted?)', job_id)
        return

    if job.status not in (BackgroundJob.Status.PENDING, BackgroundJob.Status.FAILED):
        logger.info('execute_background_job: job %s in status %s, skipping', job_id, job.status)
        return

    process_background_job(job)
