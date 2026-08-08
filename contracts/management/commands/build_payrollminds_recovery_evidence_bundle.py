import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from contracts.services.recovery_drill import SecretDetected, assemble_evidence_bundle


class Command(BaseCommand):
    """Assemble the recovery-drill evidence bundle from already-written JSON artifacts.

    Reads recovery-before.json / recovery-database-after.json /
    recovery-database-comparison.json / recovery-object-comparison.json
    (whichever are present) and combines them into one bundle file, after
    re-checking every value for secret-shaped content. Refuses to write
    the bundle at all if anything looks like a live secret — this is a
    second, independent check on top of the one each producing command
    already applies, not a replacement for it.
    """

    help = 'Assemble the PayrollMinds recovery-drill evidence bundle, rejecting secret-shaped values.'

    ARTIFACT_NAMES = (
        'recovery-before.json',
        'recovery-database-after.json',
        'recovery-database-comparison.json',
        'recovery-object-comparison.json',
    )

    def add_arguments(self, parser):
        parser.add_argument('--evidence-dir', default='.', help='Directory containing the artifact JSON files.')
        parser.add_argument('--output', default='recovery-evidence-bundle.json')

    def handle(self, *args, **options):
        evidence_dir = Path(options['evidence_dir'])
        documents = {}
        for name in self.ARTIFACT_NAMES:
            path = evidence_dir / name
            if not path.exists():
                continue
            with open(path, encoding='utf-8') as handle:
                documents[name] = json.load(handle)

        if not documents:
            raise CommandError(
                f'No recovery-drill artifacts found in {evidence_dir}. Expected one or more of: '
                f'{", ".join(self.ARTIFACT_NAMES)}'
            )

        try:
            bundle = assemble_evidence_bundle(**documents)
        except SecretDetected as exc:
            raise CommandError(f'Refusing to write evidence bundle: {exc}') from exc

        with open(options['output'], 'w', encoding='utf-8') as handle:
            json.dump(bundle, handle, indent=2, sort_keys=True)
            handle.write('\n')

        self.stdout.write(self.style.SUCCESS(f"Wrote evidence bundle ({', '.join(documents)}) to {options['output']}"))
