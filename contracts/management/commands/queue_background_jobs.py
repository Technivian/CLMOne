from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.models import BackgroundJob, Organization, SalesforceOrganizationConnection, SalesforceSyncRun
from contracts.services.job_runs import record_job_run

JOB_NAME = 'queue_background_jobs'


class Command(BaseCommand):
    help = 'Queue reminder and document-processing background jobs.'

    def handle(self, *args, **options):
        with record_job_run(JOB_NAME) as run:
            queued = self._queue_all()
            run.records_changed = queued
            run.detail = {'jobs_queued': queued}
        self.stdout.write(self.style.SUCCESS(f'Queued {queued} background job(s).'))

    def _queue_all(self):
        queued = 0
        for organization in Organization.objects.filter(is_active=True):
            for job_type in ['send_contract_reminders', 'process_document_ocr_reviews']:
                exists = BackgroundJob.objects.filter(
                    organization=organization,
                    job_type=job_type,
                    status=BackgroundJob.Status.PENDING,
                    scheduled_at__gte=timezone.now() - timedelta(minutes=15),
                ).exists()
                if exists:
                    continue
                BackgroundJob.objects.create(
                    organization=organization,
                    job_type=job_type,
                    payload={},
                    scheduled_at=timezone.now(),
                )
                queued += 1
            has_active_salesforce = SalesforceOrganizationConnection.objects.filter(
                organization=organization,
                is_active=True,
            ).exists()
            has_running_sync = SalesforceSyncRun.objects.filter(
                organization=organization,
                status=SalesforceSyncRun.Status.RUNNING,
                started_at__gte=timezone.now() - timedelta(hours=2),
            ).exists()
            if has_active_salesforce and not has_running_sync:
                sync_exists = BackgroundJob.objects.filter(
                    organization=organization,
                    job_type='sync_salesforce_contracts',
                    status=BackgroundJob.Status.PENDING,
                    scheduled_at__gte=timezone.now() - timedelta(minutes=15),
                ).exists()
                if not sync_exists:
                    BackgroundJob.objects.create(
                        organization=organization,
                        job_type='sync_salesforce_contracts',
                        payload={'limit': 200, 'dry_run': False},
                        max_attempts=3,
                        scheduled_at=timezone.now(),
                    )
                    queued += 1
            # Obligation reminders
            reminder_exists = BackgroundJob.objects.filter(
                organization=organization,
                job_type='run_obligation_reminders',
                status=BackgroundJob.Status.PENDING,
                scheduled_at__gte=timezone.now() - timedelta(hours=12),
            ).exists()
            if not reminder_exists:
                BackgroundJob.objects.create(
                    organization=organization,
                    job_type='run_obligation_reminders',
                    payload={},
                    scheduled_at=timezone.now(),
                )
                queued += 1
        return queued
