import json

from django.core.management.base import BaseCommand, CommandError

from contracts.services.recovery_drill import RecoveryDrillError, export_manifest


class Command(BaseCommand):
    """Export the pre-recovery manifest for a synthetic recovery-drill namespace.

    Output is deterministic JSON containing only non-secret verification
    data (IDs, non-sensitive metadata, dates, audit IDs/count, storage
    key/size/SHA-256 of the synthetic stored document). Never includes
    DATABASE_URL, storage credentials, passwords, session tokens, or
    secret keys — enforced by contracts.services.recovery_drill.reject_secrets.
    """

    help = 'Export recovery-before.json for a synthetic PayrollMinds recovery-drill namespace.'

    def add_arguments(self, parser):
        parser.add_argument('--namespace', required=True, help='e.g. payrollminds-recovery-drill-20260101-120000')
        parser.add_argument('--output', required=True, help='Path to write the manifest JSON to.')

    def handle(self, *args, **options):
        try:
            manifest = export_manifest(options['namespace'])
        except RecoveryDrillError as exc:
            raise CommandError(str(exc)) from exc

        with open(options['output'], 'w', encoding='utf-8') as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write('\n')

        self.stdout.write(self.style.SUCCESS(f"Wrote manifest for {options['namespace']} to {options['output']}"))
        self.stdout.write(f"audit_count={manifest['audit']['count']}")
