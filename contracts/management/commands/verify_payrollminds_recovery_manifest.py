import json
import sys

from django.core.management.base import BaseCommand, CommandError

from contracts.services.recovery_drill import RecoveryDrillError, verify_manifest


class Command(BaseCommand):
    """Verify a pre-recovery manifest against whatever database this process is connected to.

    Run this against the isolated restored recovery branch's DATABASE_URL
    — never against the live production database. Writes
    recovery-database-after.json and recovery-database-comparison.json,
    and exits non-zero if any unexplained difference or missing object is
    found (Rule #10/#11: this command reports a real comparison, it does
    not decide "success" for you beyond that exit code).
    """

    help = 'Verify a recovery-before.json manifest against the currently-connected database.'

    def add_arguments(self, parser):
        parser.add_argument('--manifest', required=True, help='Path to recovery-before.json.')
        parser.add_argument('--after-output', default='recovery-database-after.json')
        parser.add_argument('--comparison-output', default='recovery-database-comparison.json')
        parser.add_argument(
            '--verify-authorization',
            action='store_true',
            default=False,
            help='Also prove owner/unrelated-member/cross-workspace/audit-append-only behavior on this database.',
        )

    def handle(self, *args, **options):
        with open(options['manifest'], encoding='utf-8') as handle:
            manifest = json.load(handle)

        try:
            after, comparison = verify_manifest(manifest, verify_authorization=options['verify_authorization'])
        except RecoveryDrillError as exc:
            raise CommandError(str(exc)) from exc

        with open(options['after_output'], 'w', encoding='utf-8') as handle:
            json.dump(after, handle, indent=2, sort_keys=True)
            handle.write('\n')
        with open(options['comparison_output'], 'w', encoding='utf-8') as handle:
            json.dump(comparison, handle, indent=2, sort_keys=True)
            handle.write('\n')

        self.stdout.write(f"matched_object_count={comparison['matched_object_count']}")
        self.stdout.write(f"missing_object_count={comparison['missing_object_count']}")
        if comparison['differences']:
            self.stdout.write(self.style.ERROR(f"differences={comparison['differences']}"))
        if comparison.get('authorization') is not None:
            self.stdout.write(f"authorization={comparison['authorization']}")

        if not comparison['zero_unexplained_differences']:
            self.stdout.write(self.style.ERROR('Recovery verification FAILED — unexplained differences or missing objects.'))
            sys.exit(1)
        if options['verify_authorization'] and comparison.get('authorization') and not comparison['authorization']['all_expected']:
            self.stdout.write(self.style.ERROR('Recovery verification FAILED — authorization check did not match expectations.'))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Recovery verification: zero unexplained differences.'))
