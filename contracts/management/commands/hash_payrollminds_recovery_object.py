import json

from django.core.management.base import BaseCommand, CommandError

from contracts.services.recovery_drill import RecoveryDrillError, hash_stored_object


class Command(BaseCommand):
    """Read one object through a Django-configured storage backend and report its SHA-256.

    Provider-neutral: pass ``--storage-alias default`` for the canonical
    document bucket, ``--storage-alias quarantine`` for the quarantine
    bucket, or any other alias an operator has added to ``STORAGES`` for
    a recovery-target bucket (see the runbook's R2 recovery section).
    Never prints storage credentials — only the storage alias name (its
    "bucket logical role"), the object key, size, and hash.
    """

    help = 'Hash one stored object via a Django storage backend (canonical, quarantine, or a recovery alias).'

    def add_arguments(self, parser):
        parser.add_argument('--storage-alias', required=True, help='e.g. default, quarantine, or a recovery-target alias.')
        parser.add_argument('--key', required=True, help='Object key/path within that storage backend.')
        parser.add_argument('--output', help='Optional path to also write the result as JSON.')

    def handle(self, *args, **options):
        try:
            result = hash_stored_object(storage_alias=options['storage_alias'], key=options['key'])
        except RecoveryDrillError as exc:
            raise CommandError(str(exc)) from exc

        if options.get('output'):
            with open(options['output'], 'w', encoding='utf-8') as handle:
                json.dump(result, handle, indent=2, sort_keys=True)
                handle.write('\n')

        self.stdout.write(self.style.SUCCESS(json.dumps(result, indent=2, sort_keys=True)))
