from __future__ import annotations

import json
import tempfile
from datetime import timedelta
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.files.storage import storages
from django.core.exceptions import PermissionDenied
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    AuditLog,
    Document,
    DocumentIngestionAttempt,
    DocumentOCRReview,
    Organization,
    OrganizationMembership,
)
from contracts.services.document_ingestion import (
    DocumentIngestionRejected,
    DocumentIngestionUnavailable,
    DocumentReleaseDenied,
    ScanResult,
    ScanVerdict,
    get_document_ingestion_service,
)
from contracts.services.document_malware_scanners import ClamAVScanner


User = get_user_model()


class CleanScanner:
    def scan(self, file_obj, **kwargs):
        file_obj.read()
        return ScanResult(ScanVerdict.CLEAN, 'synthetic-test-scanner', 'test-signatures-1')


class MaliciousScanner:
    def scan(self, file_obj, **kwargs):
        file_obj.read()
        return ScanResult(
            ScanVerdict.MALICIOUS,
            'synthetic-test-scanner',
            'test-signatures-1',
            'MALWARE_DETECTED',
        )


class FailingScanner:
    def scan(self, file_obj, **kwargs):
        raise TimeoutError('provider detail must not escape')


class InvalidScanner:
    def scan(self, file_obj, **kwargs):
        return {'verdict': 'CLEAN'}


class FakeClamSocket:
    def __init__(self, response):
        self.response = response
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def sendall(self, payload):
        self.sent.append(payload)

    def recv(self, _size):
        response, self.response = self.response, b''
        return response


class DocumentIngestionSecurityTests(TestCase):
    def setUp(self):
        self.default_media = tempfile.TemporaryDirectory()
        self.quarantine_media = tempfile.TemporaryDirectory()
        self.addCleanup(self.default_media.cleanup)
        self.addCleanup(self.quarantine_media.cleanup)
        self.storage_override = override_settings(STORAGES={
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {'location': self.default_media.name},
            },
            'quarantine': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {'location': self.quarantine_media.name, 'base_url': None},
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        })
        self.storage_override.enable()
        self.addCleanup(self.storage_override.disable)
        self.organization = Organization.objects.create(name='Quarantine One', slug='quarantine-one')
        self.other_organization = Organization.objects.create(name='Quarantine Two', slug='quarantine-two')
        self.user = User.objects.create_user(username='quarantine-owner', password='test-pass-123')
        self.other_user = User.objects.create_user(username='quarantine-other', password='test-pass-123')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.other_organization,
            user=self.other_user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.service = get_document_ingestion_service()

    def upload(self, name='agreement.txt', content=b'Private synthetic agreement text.'):
        return SimpleUploadedFile(name, content, content_type='application/octet-stream')

    def enabled_settings(self, scanner='tests.test_document_ingestion_security.CleanScanner', **extra):
        values = {
            'DJANGO_ENV': 'test',
            'DOCUMENT_QUARANTINE_ENFORCEMENT_ENABLED': True,
            'DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED': False,
            'DOCUMENT_QUARANTINE_ENVIRONMENTS': 'test',
            'DOCUMENT_QUARANTINE_ORG_ALLOWLIST': self.organization.slug,
            'DOCUMENT_MALWARE_SCANNER_CLASS': scanner,
            'DOCUMENT_QUARANTINE_RELEASE_ENABLED': False,
            'DOCUMENT_QUARANTINE_PURGE_ENABLED': False,
            'DOCUMENT_QUARANTINE_RETENTION_DAYS': 0,
        }
        values.update(extra)
        return override_settings(**values)

    def test_default_off_creates_no_quarantine_or_document(self):
        with self.assertRaises(DocumentIngestionUnavailable):
            self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
        self.assertFalse(DocumentIngestionAttempt.objects.exists())
        self.assertFalse(Document.objects.exists())

    def test_clean_file_stays_noncanonical_until_explicit_release(self):
        with self.enabled_settings(DOCUMENT_QUARANTINE_RELEASE_ENABLED=True):
            attempt = self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
            self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.QUARANTINED)
            self.assertFalse(Document.objects.exists())
            self.assertFalse(DocumentOCRReview.objects.exists())
            attempt = self.service.scan(attempt=attempt, actor=self.user)
            self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.CLEAN)
            self.assertFalse(Document.objects.exists())
            with self.captureOnCommitCallbacks(execute=True):
                document, version = self.service.release(
                    attempt=attempt,
                    actor=self.user,
                    title='Synthetic agreement',
                    document_type=Document.DocType.CONTRACT,
                )
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.RELEASED)
        self.assertEqual(attempt.released_document, document)
        self.assertEqual(attempt.released_document_version, version)
        self.assertEqual(document.organization, self.organization)
        self.assertFalse(document.share_with_counterparty)
        self.assertEqual(document.file_hash, attempt.file_hash)
        self.assertIsNotNone(attempt.cleanup_completed_at)
        self.assertFalse(self.service.storage_alias == 'default')
        self.assertTrue(AuditLog.objects.filter(
            organization=self.organization,
            event_type='document.ingestion.released',
            object_id=attempt.pk,
        ).exists())

    def test_malicious_verdict_is_never_releasable(self):
        with self.enabled_settings(
            scanner='tests.test_document_ingestion_security.MaliciousScanner',
            DOCUMENT_QUARANTINE_RELEASE_ENABLED=True,
        ):
            attempt = self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
            attempt = self.service.scan(attempt=attempt, actor=self.user)
            self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.REJECTED)
            self.assertEqual(attempt.verdict, DocumentIngestionAttempt.Verdict.MALICIOUS)
            with self.assertRaises(DocumentReleaseDenied):
                self.service.release(attempt=attempt, actor=self.user, title='Blocked')
        self.assertFalse(Document.objects.exists())

    def test_release_cleanup_failure_preserves_document_and_marks_compensation(self):
        with self.enabled_settings(DOCUMENT_QUARANTINE_RELEASE_ENABLED=True):
            attempt = self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
            attempt = self.service.scan(attempt=attempt, actor=self.user)
            with patch.object(storages['quarantine'], 'delete', side_effect=OSError('private detail')):
                with self.captureOnCommitCallbacks(execute=True):
                    document, _version = self.service.release(
                        attempt=attempt,
                        actor=self.user,
                        title='Cleanup compensation',
                    )
        attempt.refresh_from_db()
        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.RELEASED)
        self.assertEqual(attempt.failure_code, 'CLEANUP_PENDING')
        self.assertTrue(Document.objects.filter(pk=document.pk).exists())
        evidence = AuditLog.objects.get(
            event_type='document.ingestion.release_failed',
            object_id=attempt.pk,
        )
        self.assertEqual(evidence.changes['failure_code'], 'CLEANUP_PENDING')
        self.assertNotIn('private detail', json.dumps(evidence.changes))

    def test_scanner_timeout_and_invalid_response_fail_closed_without_detail(self):
        for scanner in (
            'tests.test_document_ingestion_security.FailingScanner',
            'tests.test_document_ingestion_security.InvalidScanner',
        ):
            with self.subTest(scanner=scanner), self.enabled_settings(scanner=scanner):
                attempt = self.service.quarantine(
                    organization=self.organization,
                    uploaded_file=self.upload(),
                    actor=self.user,
                )
                attempt = self.service.scan(attempt=attempt, actor=self.user)
                self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.ERROR)
                self.assertEqual(attempt.failure_code, 'SCANNER_ERROR')
                self.assertNotIn('provider detail', json.dumps(
                    list(AuditLog.objects.filter(object_id=attempt.pk).values('changes'))
                ))
        self.assertFalse(Document.objects.exists())

    def test_cross_workspace_actor_and_target_are_denied_without_mutation(self):
        with self.enabled_settings():
            with self.assertRaises(PermissionDenied):
                self.service.quarantine(
                    organization=self.organization,
                    uploaded_file=self.upload(),
                    actor=self.other_user,
                )
            other_contract = self.other_organization.contracts.create(
                title='Restricted contract',
                created_by=self.other_user,
            )
            with self.assertRaises(PermissionDenied):
                self.service.quarantine(
                    organization=self.organization,
                    uploaded_file=self.upload(),
                    actor=self.user,
                    contract=other_contract,
                )
        self.assertFalse(DocumentIngestionAttempt.objects.exists())

    def test_extension_mismatch_binary_text_and_malformed_pdf_are_rejected(self):
        with self.enabled_settings():
            for upload in (
                self.upload('agreement.txt', b'\x00binary'),
                self.upload('agreement.pdf', b'not-a-pdf'),
            ):
                with self.subTest(name=upload.name), self.assertRaises(DocumentIngestionRejected):
                    self.service.quarantine(
                        organization=self.organization,
                        uploaded_file=upload,
                        actor=self.user,
                    )
        self.assertFalse(DocumentIngestionAttempt.objects.exists())

    def test_abort_switch_fails_closed(self):
        with self.enabled_settings(DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED=True):
            with self.assertRaises(DocumentIngestionUnavailable):
                self.service.quarantine(
                    organization=self.organization,
                    uploaded_file=self.upload(),
                    actor=self.user,
                )

    def test_retention_requires_explicit_policy_and_purge_gate(self):
        with self.enabled_settings():
            attempt = self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
            DocumentIngestionAttempt.objects.filter(pk=attempt.pk).update(
                received_at=timezone.now() - timedelta(days=31),
            )
            attempt.refresh_from_db()
            with self.assertRaises(DocumentReleaseDenied):
                self.service.expire(attempt=attempt, actor=self.user)
        attempt.refresh_from_db()
        self.assertNotEqual(attempt.status, DocumentIngestionAttempt.Status.EXPIRED)
        with self.enabled_settings(
            DOCUMENT_QUARANTINE_RETENTION_DAYS=30,
            DOCUMENT_QUARANTINE_PURGE_ENABLED=True,
        ):
            attempt = self.service.expire(attempt=attempt, actor=self.user)
        self.assertEqual(attempt.status, DocumentIngestionAttempt.Status.EXPIRED)
        self.assertTrue(AuditLog.objects.filter(
            event_type='document.ingestion.expired',
            object_id=attempt.pk,
        ).exists())

    def test_preflight_is_boolean_only_and_retention_defaults_to_dry_run(self):
        with self.enabled_settings(DOCUMENT_QUARANTINE_RETENTION_DAYS=30):
            attempt = self.service.quarantine(
                organization=self.organization,
                uploaded_file=self.upload(),
                actor=self.user,
            )
            DocumentIngestionAttempt.objects.filter(pk=attempt.pk).update(
                received_at=timezone.now() - timedelta(days=31),
            )
            from io import StringIO
            output = StringIO()
            call_command(
                'verify_document_ingestion_preflight',
                organization_slug=self.organization.slug,
                stdout=output,
            )
            payload = json.loads(output.getvalue())
            self.assertTrue(payload['ready_for_bounded_observation'])
            self.assertTrue(all(isinstance(value, bool) for value in payload.values()))
            output = StringIO()
            call_command(
                'run_document_quarantine_retention',
                organization_slug=self.organization.slug,
                stdout=output,
            )
            payload = json.loads(output.getvalue())
            self.assertFalse(payload['execute'])
            self.assertEqual(payload['candidates'], 1)
        attempt.refresh_from_db()
        self.assertNotEqual(attempt.status, DocumentIngestionAttempt.Status.EXPIRED)

    def test_explicit_api_lifecycle_and_tenant_scoped_status(self):
        self.client.force_login(self.user)
        with self.enabled_settings(DOCUMENT_QUARANTINE_RELEASE_ENABLED=True):
            response = self.client.post(
                reverse('contracts:document_ingestion_quarantine_api'),
                {'file': self.upload()},
            )
            self.assertEqual(response.status_code, 202)
            correlation_id = response.json()['correlation_id']
            self.assertTrue(response.json()['releasable'])
            self.assertFalse(Document.objects.exists())
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(
                    reverse(
                        'contracts:document_ingestion_release_api',
                        kwargs={'correlation_id': correlation_id},
                    ),
                    {'title': 'Released synthetic agreement', 'document_type': Document.DocType.CONTRACT},
                )
            self.assertEqual(response.status_code, 201)
            self.assertTrue(Document.objects.filter(pk=response.json()['document_id']).exists())

            self.client.force_login(self.other_user)
            response = self.client.get(reverse(
                'contracts:document_ingestion_status_api',
                kwargs={'correlation_id': correlation_id},
            ))
            self.assertEqual(response.status_code, 404)

    def test_existing_upload_and_preview_fail_closed_under_enforcement(self):
        self.client.force_login(self.user)
        with self.enabled_settings():
            preview = self.client.post(
                reverse('contracts:document_extract_preview_api'),
                {'file': self.upload()},
            )
            self.assertEqual(preview.status_code, 409)
            self.assertFalse(DocumentIngestionAttempt.objects.exists())
            upload = self.client.post(
                reverse('contracts:document_upload_api'),
                {'file': self.upload(), 'title': 'Pending security review'},
            )
            self.assertEqual(upload.status_code, 202)
            self.assertTrue(upload.json()['releasable'])
            self.assertFalse(Document.objects.exists())

    def test_browser_document_create_routes_bytes_to_quarantine(self):
        self.client.force_login(self.user)
        with self.enabled_settings():
            response = self.client.post(
                reverse('contracts:document_create'),
                {
                    'title': 'Browser security review',
                    'document_type': Document.DocType.CONTRACT,
                    'status': Document.Status.DRAFT,
                    'description': '',
                    'file': self.upload(),
                    'tags': '',
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'remains quarantined until explicit release')
            self.assertEqual(DocumentIngestionAttempt.objects.count(), 1)
            self.assertFalse(Document.objects.exists())


class ClamAVScannerTests(TestCase):
    def test_clean_protocol_result_is_content_minimized(self):
        version_socket = FakeClamSocket(b'ClamAV 1.4/test-db\x00')
        scan_socket = FakeClamSocket(b'stream: OK\x00')
        scanner = ClamAVScanner()
        with patch.object(scanner, '_connect', side_effect=[version_socket, scan_socket]):
            result = scanner.scan(
                BytesIO(b'synthetic'),
                timeout_seconds=3,
                file_size=9,
                digest='0' * 64,
                media_type='text/plain',
            )
        self.assertEqual(result.verdict, ScanVerdict.CLEAN)
        self.assertEqual(result.provider, 'clamav')
        self.assertEqual(result.signature_version, 'ClamAV 1.4/test-db')
        self.assertEqual(scan_socket.sent[0], b'zINSTREAM\x00')

    def test_malware_signature_name_is_not_returned(self):
        version_socket = FakeClamSocket(b'ClamAV 1.4/test-db\x00')
        scan_socket = FakeClamSocket(b'stream: Synthetic.Secret.Name FOUND\x00')
        scanner = ClamAVScanner()
        with patch.object(scanner, '_connect', side_effect=[version_socket, scan_socket]):
            result = scanner.scan(
                BytesIO(b'synthetic'),
                timeout_seconds=3,
                file_size=9,
                digest='0' * 64,
                media_type='text/plain',
            )
        self.assertEqual(result.verdict, ScanVerdict.MALICIOUS)
        self.assertEqual(result.failure_code, 'MALWARE_DETECTED')
        self.assertNotIn('Synthetic.Secret.Name', repr(result))
