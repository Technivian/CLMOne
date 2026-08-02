import json

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from contracts.models import AuditLog, Contract, Organization, OrganizationMembership


class RepositoryImportPreviewTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Import Preview Org', slug='import-preview-org')
        self.owner = User.objects.create_user(
            username='import-owner', email='import-owner@example.test', password='testpass123',
        )
        self.member = User.objects.create_user(username='import-member', password='testpass123')
        OrganizationMembership.objects.create(
            organization=self.organization, user=self.owner,
            role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.organization, user=self.member,
            role=OrganizationMembership.Role.MEMBER, is_active=True,
        )
        self.url = reverse('contracts:api_import_contracts_csv')
        self.json_url = reverse('contracts:api_import_contracts_json')
        self.page_url = reverse('contracts:contract_import_preview')
        self.template_url = reverse('contracts:contract_import_template_download')

    def test_preview_page_is_owner_or_admin_only(self):
        self.client.login(username='import-member', password='testpass123')
        self.assertEqual(self.client.get(self.page_url).status_code, 403)

        self.client.login(username='import-owner', password='testpass123')
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preview contract CSV import')

    def test_template_download_is_owner_or_admin_only(self):
        self.client.login(username='import-member', password='testpass123')
        self.assertEqual(self.client.get(self.template_url).status_code, 403)

        self.client.login(username='import-owner', password='testpass123')
        response = self.client.get(self.template_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn('title,counterparty,contract_type,owner_email,status,lifecycle_stage,start_date,end_date,renewal_date,notice_period_days,termination_notice_date', response.content.decode())

    def test_preview_is_owner_or_admin_only(self):
        self.client.login(username='import-member', password='testpass123')

        response = self.client.post(
            f'{self.url}?dry_run=true',
            'title,contract_type\nPrivate contract,NDA\n',
            content_type='text/csv',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(Contract.objects.filter(title='Private contract').exists())

    def test_preview_requires_explicit_dry_run(self):
        self.client.login(username='import-owner', password='testpass123')

        response = self.client.post(
            self.url,
            'title,contract_type\nUncommitted contract,NDA\n',
            content_type='text/csv',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Contract.objects.filter(title='Uncommitted contract').exists())

    def test_api_preview_rejects_invalid_csv_encoding_without_audit_event(self):
        self.client.login(username='import-owner', password='testpass123')

        response = self.client.post(
            f'{self.url}?dry_run=true',
            b'title,contract_type\nInvalid \xff,NDA\n',
            content_type='text/csv',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'CSV files must be UTF-8 encoded.')
        self.assertFalse(AuditLog.objects.filter(event_type='contract.import_previewed').exists())

    def test_owner_can_validate_csv_without_creating_contracts(self):
        self.client.login(username='import-owner', password='testpass123')

        response = self.client.post(
            f'{self.url}?dry_run=true',
            'title,counterparty,contract_type,status\nPreview contract,Atlas,NDA,DRAFT\n',
            content_type='text/csv',
        )

        self.assertEqual(response.status_code, 200)
        payload = json.loads(response.content)
        self.assertTrue(payload['dry_run'])
        self.assertEqual(payload['imported_count'], 1)
        self.assertEqual(payload['skipped_count'], 0)
        self.assertFalse(Contract.objects.filter(title='Preview contract').exists())
        self.assertEqual(
            AuditLog.objects.get(event_type='contract.import_previewed').changes,
            {
                'event': 'contract.import_previewed',
                'valid_row_count': 1,
                'invalid_row_count': 0,
            },
        )

    def test_json_preview_uses_the_same_content_minimized_audit_event(self):
        self.client.login(username='import-owner', password='testpass123')

        response = self.client.post(
            f'{self.json_url}?dry_run=true',
            json.dumps([{'title': 'Private JSON contract', 'counterparty': 'Atlas', 'contract_type': 'NDA'}]),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        audit = AuditLog.objects.get(event_type='contract.import_previewed')
        self.assertEqual(audit.organization, self.organization)
        self.assertEqual(audit.changes['valid_row_count'], 1)
        self.assertNotIn('Private JSON contract', str(audit.changes))
        self.assertNotIn('Atlas', str(audit.changes))

    def test_json_preview_reports_non_object_rows_without_mutating(self):
        self.client.login(username='import-owner', password='testpass123')

        response = self.client.post(
            f'{self.json_url}?dry_run=true',
            json.dumps([42]),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['skipped_count'], 1)
        self.assertEqual(response.json()['errors'], [{'row': 1, 'message': 'row must be an object'}])
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    def test_preview_page_reports_validation_without_creating_contracts(self):
        self.client.login(username='import-owner', password='testpass123')
        upload = SimpleUploadedFile(
            'contracts.csv',
            b'title,contract_type\n,NOT_A_TYPE\n',
            content_type='text/csv',
        )

        response = self.client.post(self.page_url, {'csv_file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preview results')
        self.assertContains(response, 'Row 1:')
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    def test_preview_rejects_missing_or_unsupported_csv_columns(self):
        self.client.login(username='import-owner', password='testpass123')
        upload = SimpleUploadedFile(
            'contracts.csv',
            b'counterparty,owner\nAtlas,Robin Visser\n',
            content_type='text/csv',
        )

        response = self.client.post(self.page_url, {'csv_file': upload})

        self.assertContains(response, 'File: missing required column: title')
        self.assertContains(response, 'File: unsupported column: owner')
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    def test_preview_rejects_ambiguous_csv_headers_and_extra_cells(self):
        self.client.login(username='import-owner', password='testpass123')
        duplicate_header_upload = SimpleUploadedFile(
            'duplicate-header.csv',
            b'title,title,contract_type\nFirst,Second,NDA\n',
            content_type='text/csv',
        )

        duplicate_header_response = self.client.post(self.page_url, {'csv_file': duplicate_header_upload})
        self.assertContains(duplicate_header_response, 'File: duplicate column: title')

        extra_value_upload = SimpleUploadedFile(
            'extra-value.csv',
            b'title,contract_type\nAgreement,NDA,ignored\n',
            content_type='text/csv',
        )
        extra_value_response = self.client.post(self.page_url, {'csv_file': extra_value_upload})
        self.assertContains(extra_value_response, 'Row 1: row contains more values than the CSV header')
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    def test_preview_validates_active_owner_and_key_date_mapping(self):
        self.client.login(username='import-owner', password='testpass123')
        upload = SimpleUploadedFile(
            'contracts.csv',
            (
                b'title,contract_type,owner_email,start_date,end_date,renewal_date,notice_period_days,termination_notice_date\n'
                b'Preview agreement,NDA,import-owner@example.test,2026-01-01,2027-01-01,2026-12-01,60,2026-11-02\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(self.page_url, {'csv_file': upload})

        self.assertContains(response, '1 valid row')
        self.assertFalse(Contract.objects.filter(organization=self.organization).exists())

    def test_preview_records_content_minimized_tenant_audit_evidence(self):
        other_organization = Organization.objects.create(name='Other Audit Org', slug='other-audit-org')
        self.client.login(username='import-owner', password='testpass123')
        upload = SimpleUploadedFile(
            'contracts.csv',
            b'title,counterparty,contract_type\nPreview contract,Atlas,NDA\n',
            content_type='text/csv',
        )

        self.client.post(self.page_url, {'csv_file': upload})

        audit = AuditLog.objects.get(event_type='contract.import_previewed')
        self.assertEqual(audit.organization, self.organization)
        self.assertEqual(audit.action, AuditLog.Action.VIEW)
        self.assertEqual(audit.changes, {
            'event': 'contract.import_previewed',
            'valid_row_count': 1,
            'invalid_row_count': 0,
        })
        self.assertNotIn('Preview contract', str(audit.changes))
        self.assertNotIn('Atlas', str(audit.changes))
        self.assertFalse(AuditLog.objects.filter(organization=other_organization).exists())

    def test_preview_flags_same_workspace_and_in_file_duplicates_only(self):
        Contract.objects.create(
            organization=self.organization,
            title='Existing agreement',
            counterparty='Atlas',
            created_by=self.owner,
        )
        other_organization = Organization.objects.create(name='Other Import Org', slug='other-import-org')
        Contract.objects.create(
            organization=other_organization,
            title='Other workspace agreement',
            counterparty='Atlas',
            created_by=self.owner,
        )
        self.client.login(username='import-owner', password='testpass123')
        upload = SimpleUploadedFile(
            'contracts.csv',
            (
                b'title,counterparty,contract_type\n'
                b'Existing agreement,Atlas,NDA\n'
                b'New agreement,Atlas,NDA\n'
                b'new agreement,atlas,NDA\n'
                b'Other workspace agreement,Atlas,NDA\n'
            ),
            content_type='text/csv',
        )

        response = self.client.post(self.page_url, {'csv_file': upload})

        self.assertContains(response, '2 valid rows')
        self.assertContains(response, '2 rows needing attention')
        self.assertContains(response, 'same title and counterparty already exists in this workspace')
        self.assertContains(response, 'another CSV row has the same title and counterparty')
        self.assertFalse(Contract.objects.filter(organization=self.organization, title='New agreement').exists())
