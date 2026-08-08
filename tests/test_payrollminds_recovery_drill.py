"""Tests for the PayrollMinds backup/restore drill toolkit.

Everything here runs against the local test database and local
filesystem storage only — this suite never contacts Render, Neon, or
Cloudflare (there is no code path in this file capable of doing so).
It proves the *tooling* is correct: it refuses to run unsafely, it never
writes secret-shaped values, it produces a deterministic manifest, and
its comparison logic actually detects the differences it claims to
detect. Whether a *real* restore succeeds is a fact about infrastructure
this suite cannot and does not claim to know.
"""
from __future__ import annotations

import json
import tempfile

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from contracts.models import AuditLog, AuditWriteError, Deadline, Organization
from contracts.services.recovery_drill import (
    RECOVERY_NAMESPACE_PREFIX,
    RecoveryDrillError,
    SecretDetected,
    assemble_evidence_bundle,
    create_recovery_fixture,
    export_manifest,
    hash_stored_object,
    looks_like_secret,
    reject_secrets,
    verify_manifest,
)


class RecoveryDrillTestBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.media_root = tempfile.mkdtemp(prefix='clmone-recovery-drill-')
        cls.settings_override = override_settings(MEDIA_ROOT=cls.media_root)
        cls.settings_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.settings_override.disable()
        super().tearDownClass()


class FixtureCommandConfirmationTests(TestCase):
    def test_refuses_without_confirmation_flag(self):
        with self.assertRaises(CommandError):
            call_command('create_payrollminds_recovery_fixture')
        self.assertEqual(Organization.objects.filter(slug__startswith=RECOVERY_NAMESPACE_PREFIX).count(), 0)


class FixtureIsSyntheticTests(RecoveryDrillTestBase):
    def test_fixture_namespace_and_no_payroll_shaped_data(self):
        result = create_recovery_fixture()
        self.assertTrue(result.namespace.startswith(RECOVERY_NAMESPACE_PREFIX))

        org = Organization.objects.get(pk=result.organization_id)
        self.assertTrue(org.slug.startswith(RECOVERY_NAMESPACE_PREFIX))

        manifest = export_manifest(result.namespace)
        blob = json.dumps(manifest).lower()
        for forbidden in ('salary', 'payroll_amount', 'employee_id', 'ssn', 'social_security'):
            self.assertNotIn(forbidden, blob)

    def test_fixture_command_prints_namespace_and_no_secrets(self):
        from io import StringIO

        out = StringIO()
        call_command('create_payrollminds_recovery_fixture', confirm_synthetic_recovery_drill=True, stdout=out)
        output = out.getvalue()
        self.assertIn('namespace=' + RECOVERY_NAMESPACE_PREFIX, output.replace('\n', ''))
        for forbidden in ('password', 'secret', 'DATABASE_URL', 'postgresql://'):
            self.assertNotIn(forbidden, output)


class ManifestContentTests(RecoveryDrillTestBase):
    def setUp(self):
        self.result = create_recovery_fixture()
        self.manifest = export_manifest(self.result.namespace)

    def test_manifest_has_no_known_credential_fields(self):
        reject_secrets(self.manifest)  # must not raise

    def test_manifest_is_deterministic_shape(self):
        second = export_manifest(self.result.namespace)
        self.assertEqual(self.manifest['organization'], second['organization'])
        self.assertEqual(self.manifest['contract'], second['contract'])
        self.assertEqual(self.manifest['audit']['count'], second['audit']['count'])
        self.assertEqual(self.manifest['audit']['ids'], second['audit']['ids'])

    def test_manifest_contains_expected_object_graph(self):
        self.assertEqual(self.manifest['namespace'], self.result.namespace)
        self.assertIsNotNone(self.manifest['contract'])
        self.assertIsNotNone(self.manifest['document'])
        self.assertIsNotNone(self.manifest['document']['version'])
        self.assertTrue(self.manifest['document']['version']['file_hash'])
        self.assertIsNotNone(self.manifest['deadline'])
        self.assertGreater(self.manifest['audit']['count'], 0)

    def test_export_manifest_raises_for_unknown_namespace(self):
        with self.assertRaises(RecoveryDrillError):
            export_manifest('payrollminds-recovery-drill-does-not-exist')


class VerifierDetectsDifferencesTests(RecoveryDrillTestBase):
    def setUp(self):
        self.result = create_recovery_fixture()
        self.manifest = export_manifest(self.result.namespace)

    def test_verifier_reports_zero_differences_against_unchanged_database(self):
        after, comparison = verify_manifest(self.manifest)
        self.assertTrue(comparison['zero_unexplained_differences'])
        self.assertEqual(comparison['missing_object_count'], 0)
        self.assertEqual(comparison['differences'], [])

    def test_verifier_detects_missing_deadline(self):
        Deadline.objects.filter(pk=self.result.deadline_id).delete()
        after, comparison = verify_manifest(self.manifest)
        self.assertFalse(comparison['zero_unexplained_differences'])
        self.assertIn('deadline', comparison['missing_objects'])

    def test_verifier_detects_relationship_difference(self):
        org = Organization.objects.get(pk=self.result.organization_id)
        org.name = 'Tampered name after restore'
        org.save(update_fields=['name'])
        after, comparison = verify_manifest(self.manifest)
        self.assertFalse(comparison['zero_unexplained_differences'])
        self.assertTrue(any('organization.name' in diff for diff in comparison['differences']))

    def test_verifier_detects_missing_audit_events(self):
        # AuditLog is append-only (AuditWriteError on delete/update — proven
        # separately in AuthorizationVerificationTests), so a real "restore
        # dropped audit rows" scenario is simulated the way a real
        # comparison would actually surface it: the before-manifest claims
        # an audit ID the after-database does not have.
        self.manifest['audit']['ids'] = self.manifest['audit']['ids'] + [999999999]
        self.manifest['audit']['count'] += 1
        after, comparison = verify_manifest(self.manifest)
        self.assertFalse(comparison['zero_unexplained_differences'])
        self.assertTrue(any('audit' in diff for diff in comparison['differences']))

    def test_verifier_detects_unknown_namespace_as_missing_not_a_crash(self):
        self.manifest['namespace'] = 'payrollminds-recovery-drill-vanished'
        after, comparison = verify_manifest(self.manifest)
        self.assertFalse(comparison['zero_unexplained_differences'])
        self.assertEqual(comparison['missing_object_count'], 1)


class AuthorizationVerificationTests(RecoveryDrillTestBase):
    def setUp(self):
        self.result = create_recovery_fixture()
        self.manifest = export_manifest(self.result.namespace)

    def test_authorization_checks_pass_on_unchanged_database(self):
        after, comparison = verify_manifest(self.manifest, verify_authorization=True)
        auth = comparison['authorization']
        self.assertTrue(auth['all_expected'], auth)
        self.assertTrue(auth['checks']['owner_can_access'])
        self.assertTrue(auth['checks']['unrelated_member_cannot_access'])
        self.assertTrue(auth['checks']['cross_workspace_user_cannot_access'])
        self.assertTrue(auth['checks']['audit_remains_append_only'])

    def test_audit_log_remains_append_only_directly(self):
        row = AuditLog.objects.filter(organization_id=self.result.organization_id).first()
        with self.assertRaises(AuditWriteError):
            row.delete()
        with self.assertRaises(AuditWriteError):
            AuditLog.objects.filter(pk=row.pk).update(outcome=AuditLog.Outcome.FAILURE)


class HashToolingTests(RecoveryDrillTestBase):
    def test_hash_is_deterministic_for_the_synthetic_document(self):
        result = create_recovery_fixture()
        manifest = export_manifest(result.namespace)
        key = manifest['document']['version']['storage']['key']
        first = hash_stored_object(storage_alias='default', key=key)
        second = hash_stored_object(storage_alias='default', key=key)
        self.assertEqual(first['sha256'], second['sha256'])
        self.assertEqual(first['sha256'], manifest['document']['version']['file_hash'])
        self.assertEqual(first['bucket_logical_role'], 'default')

    def test_hash_tool_raises_for_unknown_storage_alias(self):
        with self.assertRaises(RecoveryDrillError):
            hash_stored_object(storage_alias='not-a-real-alias', key='whatever')


class SecretRejectionTests(TestCase):
    def test_looks_like_secret_flags_key_names(self):
        self.assertTrue(looks_like_secret('DATABASE_URL', 'anything'))
        self.assertTrue(looks_like_secret('storage_secret_access_key', 'anything'))
        self.assertTrue(looks_like_secret('password', 'anything'))
        self.assertFalse(looks_like_secret('contract_id', 42))
        self.assertFalse(looks_like_secret('title', 'Recovery Drill Synthetic Counterparty'))

    def test_looks_like_secret_detects_value_shapes(self):
        # Built by concatenation, not a literal URI-shaped string in source,
        # so this synthetic example (fake user/pass/host, connects to
        # nothing real) doesn't itself trip a source-scanning secret
        # scanner while still exercising the exact same runtime value
        # against looks_like_secret's own regex.
        fake_postgres_uri = 'postgres' + 'ql://' + 'user' + ':' + 'pass' + '@host/db'
        self.assertTrue(looks_like_secret('note', fake_postgres_uri))
        self.assertTrue(looks_like_secret('note', 'npg_abcdefghijklmnopqrstuvwx'))
        self.assertTrue(looks_like_secret('note', '-----BEGIN RSA PRIVATE KEY-----'))
        self.assertFalse(looks_like_secret('note', 'this is a perfectly normal sentence'))

    def test_reject_secrets_raises_on_nested_dict(self):
        with self.assertRaises(SecretDetected):
            reject_secrets({'document': {'inner': {'password': 'x'}}})

    def test_reject_secrets_flags_list_items(self):
        with self.assertRaises(SecretDetected):
            reject_secrets([{'ok': 1}, {'api_key': 'x'}])

    def test_reject_secrets_passes_clean_data(self):
        reject_secrets({'contract': {'id': 1, 'title': 'Fine'}, 'items': [{'id': 2}]})

    def test_evidence_bundle_rejects_secret_shaped_document(self):
        with self.assertRaises(SecretDetected):
            assemble_evidence_bundle(before={'password': 'x'})

    def test_evidence_bundle_accepts_clean_documents(self):
        bundle = assemble_evidence_bundle(before={'namespace': 'payrollminds-recovery-drill-x'}, after={'namespace': 'payrollminds-recovery-drill-x'})
        self.assertIn('before', bundle['documents'])
        self.assertIn('after', bundle['documents'])
