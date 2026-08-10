from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from contracts.models import AuditLog, Contract, Document, DocumentReviewRun, Organization, OrganizationAPIToken, OrganizationMembership


User = get_user_model()


class DocumentIngestionTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Ingestion Workspace', slug='ingestion-workspace')
        self.user = User.objects.create_user(username='ingestion-owner', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.client = Client()
        self.client.login(username='ingestion-owner', password='pass12345')

    def _agreement(self, filename='northwind-msa.txt'):
        return SimpleUploadedFile(
            filename,
            (
                b'Master Service Agreement between Contoso Ltd and Northwind Ltd.\n'
                b'Effective date: 2026-09-01\n'
                b'Governed by the laws of England and Wales.\n'
                b'Contract value EUR 50,000.00\n'
            ),
            content_type='text/plain',
        )

    def test_mass_import_surface_explains_unverified_extraction_and_email_endpoint(self):
        response = self.client.get(reverse('contracts:mass_document_import'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Extracted details remain unverified')
        self.assertContains(response, reverse('contracts:document_mass_import_api'))
        self.assertContains(response, reverse('contracts:email_forwarded_document_ingest_api'))

    def test_mass_import_creates_provenanced_documents_and_unverified_metadata(self):
        response = self.client.post(
            reverse('contracts:document_mass_import_api'),
            {'files': [self._agreement()]},
        )
        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload['created_count'], 1)
        item = payload['created'][0]
        contract = Contract.objects.get(pk=item['contract_id'])
        document = Document.objects.get(pk=item['document_id'])
        review_run = DocumentReviewRun.objects.get(pk=item['review_run_id'])

        self.assertEqual(contract.origin_kind, Contract.OriginKind.IMPORT_INBOUND)
        self.assertEqual(contract.lifecycle_stage, Contract.LifecycleStage.INTAKE)
        self.assertEqual(document.contract, contract)
        self.assertEqual(document.version_source, 'import')
        self.assertEqual(contract.contract_type, Contract.ContractType.OTHER)
        self.assertEqual(contract.counterparty, '')
        metadata = review_run.extracted_metadata
        self.assertEqual(metadata['extraction_status'], 'extracted_unverified')
        self.assertEqual(metadata['metadata_extraction']['contract_type']['value'], 'MSA')
        self.assertFalse(metadata['governing_law_confirmed'])
        self.assertTrue(AuditLog.objects.filter(event_type='document.ingested', object_id=document.pk).exists())
        self.assertTrue(AuditLog.objects.filter(event_type='document.metadata_extracted').exists())
        self.assertEqual(item['review_url'], reverse('contracts:contract_review_workspace', args=[contract.pk]))

    def test_mass_import_rejects_unsupported_file_without_writing_a_record(self):
        response = self.client.post(
            reverse('contracts:document_mass_import_api'),
            {'files': [SimpleUploadedFile('agreement.exe', b'not a contract')]},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Contract.objects.filter(organization=self.organization).count(), 0)

    @override_settings(EMAIL_FORWARDED_INGESTION_ENABLED=True)
    def test_email_forwarding_is_scoped_and_idempotent_by_message_id(self):
        token, raw_token = OrganizationAPIToken.create_token(
            self.organization,
            scopes=['contracts:write'],
            label='Forwarding test token',
            created_by=self.user,
        )
        url = reverse('contracts:email_forwarded_document_ingest_api')
        first = Client().post(
            url,
            {'message_id': '<mail-123@example.test>', 'attachments': [self._agreement()]},
            HTTP_AUTHORIZATION=f'Bearer {raw_token}',
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.json()['created_count'], 1)
        contract = Contract.objects.get(pk=first.json()['created'][0]['contract_id'])
        self.assertEqual(contract.origin_kind, Contract.OriginKind.INTEGRATION)
        self.assertEqual(contract.source_system, 'email_forwarding')
        self.assertTrue(contract.source_system_id)
        self.assertIsNone(contract.created_by)
        self.assertTrue(AuditLog.objects.filter(
            event_type='document.ingested',
            object_id=first.json()['created'][0]['document_id'],
            actor_type=AuditLog.ActorType.WEBHOOK,
        ).exists())

        replay = Client().post(
            url,
            {'message_id': '<mail-123@example.test>', 'attachments': [self._agreement()]},
            HTTP_AUTHORIZATION=f'Bearer {raw_token}',
        )
        self.assertEqual(replay.status_code, 201)
        self.assertEqual(replay.json()['created_count'], 0)
        self.assertEqual(replay.json()['skipped_count'], 1)
        token.refresh_from_db()
        self.assertIsNotNone(token.last_used_at)

    def test_email_forwarding_is_default_off(self):
        _token, raw_token = OrganizationAPIToken.create_token(
            self.organization, scopes=['contracts:write'], created_by=self.user,
        )
        response = Client().post(
            reverse('contracts:email_forwarded_document_ingest_api'),
            {'message_id': '<mail-off@example.test>', 'attachments': [self._agreement()]},
            HTTP_AUTHORIZATION=f'Bearer {raw_token}',
        )
        self.assertEqual(response.status_code, 404)
