import json
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from contracts.models import AuditLog, Contract, Organization
from contracts.services.contract_lifecycle import build_contract_audit_changes, build_contract_lifecycle_guidance


class Command(BaseCommand):
    help = 'Promote contracts into renewal review before the retention archive window.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', default='')
        parser.add_argument('--dry-run', action='store_true', default=False)
        parser.add_argument('--renewal-window-days', type=int, default=30)
        parser.add_argument('--renewal-date-window-days', type=int, default=14)
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
            'contracts_evaluated': 0,
            'contracts_promoted_to_renewal': 0,
            'contracts_archived': 0,
            'audit_entries_created': 0,
            'actions': [],
        }

        for organization in organizations:
            summary['organizations_scanned'] += 1
            candidates = (
                Contract.objects.filter(organization=organization)
                .exclude(lifecycle_stage='ARCHIVED')
                .order_by('id')[:limit]
            )
            for contract in candidates:
                summary['contracts_evaluated'] += 1
                guidance = build_contract_lifecycle_guidance(contract)
                trace_id = str(uuid.uuid4())

                action_payload = {
                    'trace_id': trace_id,
                    'organization_id': organization.id,
                    'contract_id': contract.id,
                    'dry_run': dry_run,
                    'current_stage': contract.lifecycle_stage,
                    'recommended_stage': guidance['next_stage'],
                    'guidance_state': guidance['state'],
                    'guidance_severity': guidance['severity'],
                    'guidance_action': guidance['action'],
                }

                should_promote_to_renewal = guidance['next_stage'] == 'RENEWAL' and contract.lifecycle_stage in {'EXECUTED', 'OBLIGATION_TRACKING'}

                if not dry_run and should_promote_to_renewal and contract.can_transition_lifecycle_stage('RENEWAL'):
                    before_contract = Contract.objects.get(pk=contract.pk)
                    contract.lifecycle_stage = 'RENEWAL'
                    contract.save(update_fields=['lifecycle_stage', 'updated_at'])
                    AuditLog.objects.create(
                        action=AuditLog.Action.UPDATE,
                        model_name='Contract',
                        object_id=contract.id,
                        object_repr=contract.title[:300],
                        changes={
                            'event': 'contract_lifecycle_stage_changed',
                            'changed_fields': ['lifecycle_stage'],
                            'field_changes': build_contract_audit_changes(before_contract, contract),
                            'trace_id': trace_id,
                            'automated': True,
                            'reason': guidance['action'],
                        },
                    )
                    summary['contracts_promoted_to_renewal'] += 1
                    summary['audit_entries_created'] += 1

                summary['actions'].append(action_payload)

        self.stdout.write(json.dumps(summary, indent=2, sort_keys=True))