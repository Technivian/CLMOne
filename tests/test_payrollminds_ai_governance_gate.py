"""Fail-closed AI boundaries for the controlled PayrollMinds pilot."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from contracts.models import Contract, Document, DocumentOCRReview, Organization, OrganizationMembership, OrgPolicy


User = get_user_model()


class PayrollMindsAIGovernanceGateTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='PayrollMinds', slug='payrollminds')
        self.owner = User.objects.create_user(username='pilot_owner', password='pass12345')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        OrgPolicy.objects.create(organization=self.organization, ai_features_enabled=True)
        self.contract = Contract.objects.create(
            organization=self.organization,
            title='Synthetic supplier agreement',
            contract_type=Contract.ContractType.VENDOR,
            status=Contract.Status.IN_PROGRESS,
            created_by=self.owner,
            owner=self.owner,
        )
        self.document = Document.objects.create(
            organization=self.organization,
            contract=self.contract,
            title='synthetic.txt',
            document_type=Document.DocType.CONTRACT,
            uploaded_by=self.owner,
        )
        DocumentOCRReview.objects.create(
            organization=self.organization,
            document=self.document,
            status=DocumentOCRReview.Status.IN_REVIEW,
            extracted_text='Synthetic contract text only.',
            source='text-extraction',
        )
        self.client.force_login(self.owner)

    @override_settings(
        CONTROLLED_PILOT_ENABLED=True,
        GEMINI_AI_ENABLED=True,
        GEMINI_API_KEY='configured-but-must-not-be-used',
    )
    def test_controlled_pilot_refuses_ai_provider_even_when_environment_is_configured(self):
        url = reverse('contracts:contract_ai_extract_api', args=[self.contract.pk])
        with patch('contracts.services.ai_extraction._get_client') as provider:
            response = self.client.post(url, data='{}', content_type='application/json')

        # The full request is stopped by controlled-pilot middleware before a
        # provider route is reached, with a content-free manual recovery path.
        self.assertEqual(response.status_code, 403)
        self.assertIn('Enter and verify metadata manually', response.json()['error'])
        provider.assert_not_called()

    @override_settings(CONTROLLED_PILOT_ENABLED=True, GEMINI_AI_ENABLED=True, GEMINI_API_KEY='test-key')
    def test_direct_ai_resolver_fails_closed_without_middleware(self):
        from contracts.api.documents_ai import _resolve_ai_contract

        request = RequestFactory().post('/contracts/api/contracts/unused/ai-extract/')
        request.user = self.owner
        _, _, response = _resolve_ai_contract(request, self.contract.pk, require_provider=True)

        self.assertEqual(response.status_code, 403)
        self.assertIn('Enter and verify metadata manually', response.content.decode())

    @override_settings(CONTROLLED_PILOT_ENABLED=False, GEMINI_AI_ENABLED=True, GEMINI_API_KEY='test-key')
    def test_workspace_administrator_kill_switch_prevents_provider_submission(self):
        self.organization.policy.ai_features_enabled = False
        self.organization.policy.save(update_fields=['ai_features_enabled'])
        url = reverse('contracts:contract_ai_extract_api', args=[self.contract.pk])
        with patch('contracts.services.ai_extraction._get_client') as provider:
            response = self.client.post(url, data='{}', content_type='application/json')

        self.assertEqual(response.status_code, 403)
        self.assertIn('disabled for this workspace', response.json()['error'])
        provider.assert_not_called()

    @override_settings(CONTROLLED_PILOT_ENABLED=True, GEMINI_AI_ENABLED=True, GEMINI_API_KEY='test-key')
    def test_manual_metadata_preview_remains_available_without_provider(self):
        upload = SimpleUploadedFile(
            'supplier.txt',
            b'Master Service Agreement between Acme and Northwind. Effective date: 2026-03-01.',
            content_type='text/plain',
        )
        with patch('contracts.services.ai_extraction._get_client') as provider:
            response = self.client.post(reverse('contracts:document_extract_preview_api'), {'file': upload})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['ok'])
        self.assertEqual(response.json()['extraction']['contract_type']['value'], 'MSA')
        provider.assert_not_called()
