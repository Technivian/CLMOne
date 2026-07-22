"""PAR-ID-001 R1 CERTAIN non-ADMIN remediation (dry-run / apply / rollback)."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from contracts.services.process_role_r1_remediation import (
    R1ScopeError,
    apply_r1_remediation,
    plan_r1_remediation,
    rollback_r1_remediation,
)


class Command(BaseCommand):
    help = (
        'R1 CERTAIN non-ADMIN ProcessRoleAssignment remediation. '
        'Dry-run/apply/rollback only; does not enable PROCESS_ROLE_* flags.'
    )

    def add_arguments(self, parser):
        g = parser.add_mutually_exclusive_group(required=True)
        g.add_argument('--dry-run', action='store_true')
        g.add_argument('--apply', action='store_true')
        g.add_argument('--rollback', action='store_true')
        parser.add_argument('--run-id', default='', help='Required for --rollback; optional for --apply')
        parser.add_argument('--json', action='store_true')

    def handle(self, *args, **options):
        try:
            if options['dry_run']:
                result = plan_r1_remediation()
            elif options['apply']:
                result = apply_r1_remediation(
                    run_id=options['run_id'] or None,
                )
            else:
                run_id = (options['run_id'] or '').strip()
                if not run_id:
                    raise CommandError('--run-id is required for --rollback')
                result = rollback_r1_remediation(run_id=run_id)
        except R1ScopeError as exc:
            raise CommandError(str(exc)) from exc

        if options['json']:
            self.stdout.write(json.dumps(result, sort_keys=True, indent=2))
        else:
            self.stdout.write(json.dumps(result, sort_keys=True))
            if result.get('mode') == 'dry-run':
                self.stdout.write(
                    f"dry-run to_create={result['to_create_count']} "
                    f"already={result['already_active_count']} scope_valid={result['scope_valid']}"
                )
            elif result.get('mode') == 'apply':
                self.stdout.write(
                    f"apply created={result['created_count']} skipped={result['skipped_count']} "
                    f"run_id={result['remediation_run_id']}"
                )
            else:
                self.stdout.write(
                    f"rollback deactivated={result['deactivated_count']} "
                    f"run_id={result['remediation_run_id']}"
                )
