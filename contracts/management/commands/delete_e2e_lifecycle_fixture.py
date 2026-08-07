from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from contracts.models import Contract


class Command(BaseCommand):
    """Delete a single Contract created by a browser lifecycle test.

    Test-only ownership cleanup for the browser suite (see
    docs/pilots/payrollminds/BROWSER_TEST_ISOLATION_AND_VISUAL_REPAIR.md).
    Refuses to run outside DJANGO_E2E so it can never reach a production
    database. Only deletes the named Contract (and its cascading Workflow);
    it never touches AuditLog, which stays append-only so the creation event
    remains in the record even after the synthetic contract is removed.
    """

    help = 'Delete a single E2E-created Contract by id (DJANGO_E2E only).'

    def add_arguments(self, parser):
        parser.add_argument('--contract-id', type=int, required=True)

    def handle(self, *args, **options):
        if not getattr(settings, 'DJANGO_E2E', False):
            raise CommandError('delete_e2e_lifecycle_fixture requires DJANGO_E2E=1.')

        contract_id = options['contract_id']
        deleted, _ = Contract.objects.filter(pk=contract_id).delete()
        if deleted:
            self.stdout.write(self.style.SUCCESS(f'Deleted E2E contract {contract_id}.'))
        else:
            self.stdout.write(f'No contract {contract_id} to delete (already clean).')
