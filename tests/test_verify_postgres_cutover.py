import json
import os
from io import StringIO
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase


def _mock_connection(vendor='sqlite', engine='django.db.backends.sqlite3'):
    conn = MagicMock()
    conn.vendor = vendor
    conn.settings_dict = {'ENGINE': engine, 'NAME': ':memory:', 'USER': 'n/a'}
    cursor = MagicMock()
    cursor.__enter__ = lambda s: s
    cursor.__exit__ = MagicMock(return_value=False)
    cursor.fetchone.return_value = ('1',)
    conn.cursor.return_value = cursor
    return conn


def _mock_executor(unapplied=None):
    executor = MagicMock()
    executor.loader.graph.leaf_nodes.return_value = []
    executor.migration_plan.return_value = unapplied or []
    return executor


class VerifyPostgresCutoverSimulationTests(SimpleTestCase):
    """Tests for verify_postgres_cutover --simulation mode (no real DB required)."""

    _PATCHES = [
        'contracts.management.commands.verify_postgres_cutover.connection',
        'contracts.management.commands.verify_postgres_cutover.MigrationExecutor',
    ]

    def _run(self, unapplied=None, vendor='sqlite',
             engine='django.db.backends.sqlite3', env='', **kwargs):
        mock_conn = _mock_connection(vendor=vendor, engine=engine)
        mock_executor = _mock_executor(unapplied=unapplied)
        out = StringIO()
        with patch('contracts.management.commands.verify_postgres_cutover.connection', mock_conn), \
             patch('contracts.management.commands.verify_postgres_cutover.MigrationExecutor',
                   return_value=mock_executor), \
             patch.dict(os.environ, {'DJANGO_ENV': env}):
            call_command('verify_postgres_cutover', stdout=out, **kwargs)
        return json.loads(out.getvalue())

    def test_simulation_mode_exits_zero_in_sqlite(self):
        payload = self._run(simulation=True)
        self.assertIn('cutover_ready', payload)
        self.assertTrue(payload['simulation'])

    def test_simulation_mode_sets_simulation_note_when_not_postgres(self):
        payload = self._run(simulation=True)
        if not payload['cutover_ready']:
            self.assertIn('simulation_note', payload)
            self.assertIn('rehearsal', payload['simulation_note'].lower())

    def test_simulation_mode_captures_migration_status(self):
        payload = self._run(simulation=True)
        self.assertIn('migrations', payload)
        self.assertIn('unapplied_count', payload['migrations'])
        self.assertIn('status', payload['migrations'])

    def test_simulation_mode_captures_database_section(self):
        payload = self._run(simulation=True)
        db = payload['database']
        self.assertIn('engine', db)
        self.assertIn('connectivity_latency_ms', db)
        self.assertIn('version', db)

    def test_non_simulation_mode_raises_in_production_non_postgres(self):
        with self.assertRaises(CommandError):
            self._run(simulation=False, env='production')
