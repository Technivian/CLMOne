import json
import uuid
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.middleware import log_action
from contracts.models import AuditLog, Contract, Organization, RetentionPolicy
from contracts.services.contract_lifecycle import get_contract_lifecycle_service
from contracts.services.job_runs import record_job_run

JOB_NAME = 'run_retention_jobs'


class Command(BaseCommand):
    help = 'Execute retention policies and archive eligible contracts with immutable audit logs.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', default='')
        parser.add_argument('--dry-run', action='store_true', default=False)
        parser.add_argument('--limit', type=int, default=500)

    def handle(self, *args, **options):
        dry_run = bool(options['dry_run'])
        limit = max(1, int(options['limit']))
        org_slug = str(options.get('organization_slug') or '').strip()

        organizations = Organization.objects.all().order_by('id')
        if org_slug:
            organizations = organizations.filter(slug=org_slug)

        summary = {
            'captured_at': timezone.now().isoformat(),
            'dry_run': dry_run,
            'organizations_scanned': 0,
            'policies_scanned': 0,
            'contracts_evaluated': 0,
            'contracts_archived': 0,
            'audit_entries_created': 0,
            'actions': [],
        }

        lifecycle = get_contract_lifecycle_service()
        for organization in organizations:
            summary['organizations_scanned'] += 1
            # Per-org evidence + overlap protection (skip if another retention
            # run for this org is already in flight). dry_run is exploratory, so
            # it does not take the overlap lock.
            with record_job_run(
                JOB_NAME, organization=organization, prevent_overlap=not dry_run,
            ) as run:
                if run is None:
                    summary['actions'].append({'organization_id': organization.id, 'skipped': 'overlap'})
                    continue
                run.detail = {'dry_run': dry_run}
                policies = RetentionPolicy.objects.filter(
                    organization=organization,
                    is_active=True,
                    category=RetentionPolicy.Category.CONTRACTS,
                ).order_by('id')
                for policy in policies:
                    summary['policies_scanned'] += 1
                    cutoff_date = timezone.now().date() - timedelta(days=policy.retention_period_days)
                    candidates = Contract.objects.filter(
                        organization=organization,
                        end_date__isnull=False,
                        end_date__lte=cutoff_date,
                    ).exclude(status=Contract.Status.ARCHIVED).order_by('id')[:limit]
                    for contract in candidates:
                        summary['contracts_evaluated'] += 1
                        run.records_examined += 1
                        trace_id = str(uuid.uuid4())
                        action_payload = {
                            'trace_id': trace_id,
                            'organization_id': organization.id,
                            'policy_id': policy.id,
                            'contract_id': contract.id,
                            'retention_period_days': policy.retention_period_days,
                            'cutoff_date': cutoff_date.isoformat(),
                            'dry_run': dry_run,
                        }
                        if not dry_run:
                            # Archive is a record status, not a workflow stage.
                            lifecycle.transition(
                                contract,
                                Contract.Status.ARCHIVED,
                                actor=None,
                                system=True,
                                reason='Retention policy archive',
                                actor_type=AuditLog.ActorType.SCHEDULED_JOB,
                                job_run_id=run.run_id,
                            )
                            log_action(
                                None, AuditLog.Action.UPDATE, 'RetentionExecution',
                                object_id=contract.id, object_repr=contract.title[:300],
                                organization=organization, actor_type='scheduled_job',
                                event_type='retention.contract_archived',
                                job_run_id=run.run_id,
                                changes={'event': 'retention.contract_archived', **action_payload},
                            )
                            summary['contracts_archived'] += 1
                            summary['audit_entries_created'] += 2
                            run.records_changed += 1
                        summary['actions'].append(action_payload)

        self.stdout.write(json.dumps(summary, indent=2, sort_keys=True))
