"""PostgreSQL-only audit guarantees: append-only trigger + concurrency.

Skipped on SQLite (the default test DB). The CI 'audit-postgres' job runs the
whole suite against PostgreSQL so these execute as a release gate.
"""
from __future__ import annotations

import threading
from unittest import skipUnless

from django.db import connection, connections, transaction
from django.test import TransactionTestCase

from contracts.models import AuditLog, Organization
from contracts.services.audit import append_audit, verify_chain, VERDICT_VALID

_IS_PG = connection.vendor == 'postgresql'


@skipUnless(_IS_PG, 'PostgreSQL-only (append-only trigger)')
class AuditTriggerPostgresTests(TransactionTestCase):
    reset_sequences = True

    def _seed_row(self):
        org = Organization.objects.create(name='Trig Org', slug='trig-org')
        return append_audit(action='CREATE', model_name='Contract', organization=org,
                            object_id=1, changes={'event': 'contract.created'})

    def test_update_is_rejected_by_db_trigger(self):
        row = self._seed_row()
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute(
                        "UPDATE contracts_auditlog SET outcome='failure' WHERE id=%s",
                        [row.pk],
                    )

    def test_delete_is_rejected_by_db_trigger(self):
        row = self._seed_row()
        with self.assertRaises(Exception):
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute("DELETE FROM contracts_auditlog WHERE id=%s", [row.pk])


@skipUnless(_IS_PG, 'PostgreSQL-only (advisory-lock concurrency)')
class AuditConcurrencyPostgresTests(TransactionTestCase):
    reset_sequences = True

    def _hammer(self, organization, n_threads=8, per_thread=12, model_name='Contract'):
        errors = []

        def worker():
            try:
                for i in range(per_thread):
                    append_audit(action='CREATE', model_name=model_name,
                                 organization=organization, object_id=i,
                                 event_type='demo.event',
                                 changes={'event': 'demo.event', 'i': i})
            except Exception as exc:  # noqa: BLE001
                errors.append(repr(exc))
            finally:
                connections.close_all()  # release this thread's connection

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return errors, n_threads * per_thread

    def test_concurrent_tenant_appends_from_genesis(self):
        org = Organization.objects.create(name='Conc Org', slug='conc-org')
        # Starts at genesis (empty chain) so threads race for seq=1 too.
        errors, total = self._hammer(org)
        self.assertEqual(errors, [], f'concurrent append errors: {errors}')
        org_id = org.id
        seqs = list(
            AuditLog.objects.filter(organization_id=org_id, seq__isnull=False)
            .order_by('seq').values_list('seq', flat=True)
        )
        self.assertEqual(seqs, list(range(1, total + 1)))  # contiguous, no gaps/dups
        self.assertEqual(verify_chain(org_id)['status'], VERDICT_VALID)

    def test_concurrent_system_chain_appends(self):
        # The NULL system chain has its own advisory-lock target + partial unique
        # constraint; concurrent appends must stay contiguous and valid. Use a
        # platform target ('User') — org-owned models are barred from this chain.
        errors, total = self._hammer(None, model_name='User')
        self.assertEqual(errors, [], f'system-chain append errors: {errors}')
        seqs = list(
            AuditLog.objects.filter(organization__isnull=True, seq__isnull=False)
            .order_by('seq').values_list('seq', flat=True)
        )
        self.assertEqual(seqs, list(range(1, total + 1)))
        self.assertEqual(verify_chain(None)['status'], VERDICT_VALID)


@skipUnless(_IS_PG, 'PostgreSQL-only (partial unique on NULL org)')
class SystemChainUniquenessPostgresTests(TransactionTestCase):
    reset_sequences = True

    def test_duplicate_system_seq_rejected_by_partial_constraint(self):
        AuditLog.objects.create(organization=None, action='LOGIN', model_name='User',
                                event_type='auth.login_failed', seq=1, hash_version=2,
                                entry_hash='a')
        with self.assertRaises(Exception):
            with transaction.atomic():
                AuditLog.objects.create(organization=None, action='LOGIN', model_name='User',
                                        event_type='auth.login_failed', seq=1, hash_version=2,
                                        entry_hash='b')
