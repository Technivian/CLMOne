from django.core.management.base import BaseCommand, CommandError

from contracts.services.recovery_drill import RecoveryDrillError, create_recovery_fixture


class Command(BaseCommand):
    """Create one explicitly synthetic PayrollMinds recovery-drill fixture.

    Production-safe only because it is explicit: it never runs without
    ``--confirm-synthetic-recovery-drill``, it never touches
    employee/salary/payroll data, and every object it creates lives under
    a single fresh Organization/slug namespaced
    ``payrollminds-recovery-drill-<timestamp>`` — nothing pre-existing is
    read or modified. See
    docs/pilots/payrollminds/OPERATOR_BACKUP_RESTORE_DRILL_RUNBOOK.md.
    """

    help = 'Create a synthetic PayrollMinds recovery-drill fixture (requires --confirm-synthetic-recovery-drill).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm-synthetic-recovery-drill',
            action='store_true',
            default=False,
            help='Required. Confirms you intend to create a new, isolated, synthetic fixture now.',
        )

    def handle(self, *args, **options):
        if not options['confirm_synthetic_recovery_drill']:
            raise CommandError(
                'Refusing to run without --confirm-synthetic-recovery-drill. '
                'This creates a new synthetic Organization/Contract/Document graph; '
                'the flag exists so this can never fire by accident.'
            )
        try:
            result = create_recovery_fixture()
        except RecoveryDrillError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f'namespace={result.namespace}'))
        self.stdout.write(f'organization_id={result.organization_id}')
        self.stdout.write(f'contract_id={result.contract_id}')
        self.stdout.write(f'workflow_id={result.workflow_id}')
        self.stdout.write(f'document_id={result.document_id}')
        self.stdout.write(f'document_version_id={result.document_version_id}')
        self.stdout.write(f'deadline_id={result.deadline_id}')
        self.stdout.write(f'audit_log_count={len(result.audit_log_ids)}')
        self.stdout.write(f'canonical_runtime_exercised={result.canonical_runtime_exercised}')
        self.stdout.write(f'created_at={result.created_at}')
        self.stdout.write(
            'Next: python manage.py export_payrollminds_recovery_manifest '
            f'--namespace {result.namespace} --output recovery-before.json'
        )
