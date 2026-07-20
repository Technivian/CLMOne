from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.middleware import log_action
from contracts.models import AIExtractionSpan, AuditLog, CommandCenterWorkItem, Contract, Document, Organization, OrganizationMembership, RiskLog
from contracts.services.ai_contract_review import ContractReviewResult, review_uploaded_contract


User = get_user_model()


@override_settings(GEMINI_AI_ENABLED=True, GEMINI_API_KEY='test-provider-key')
class UploadedContractAIReviewTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name='Legacy review workspace', slug='legacy-review-workspace')
        self.user = User.objects.create_user(username='legacy_reviewer', password='testpass123')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.contract = Contract.objects.create(
            organization=self.organization,
            title='Legacy supplier agreement',
            contract_type=Contract.ContractType.VENDOR,
            owner=self.user,
            created_by=self.user,
        )
        self.document = Document.objects.create(
            organization=self.organization,
            contract=self.contract,
            title='Legacy supplier agreement.txt',
            document_type=Document.DocType.CONTRACT,
            uploaded_by=self.user,
        )

    def test_review_creates_only_evidence_backed_open_flags(self):
        review_span = AIExtractionSpan(
            document=self.document,
            organization=self.organization,
            label='liability_cap',
            span_text='Supplier liability is unlimited.',
            start_char=0,
            end_char=31,
            confidence=Decimal('0.9300'),
            risk_level=AIExtractionSpan.RiskLevel.RISK,
            rationale='Unlimited liability needs legal approval.',
        )
        clear_span = AIExtractionSpan(
            document=self.document,
            organization=self.organization,
            label='governing_law',
            span_text='This agreement is governed by Dutch law.',
            start_char=32,
            end_char=73,
            confidence=Decimal('0.9800'),
            risk_level=AIExtractionSpan.RiskLevel.CLEAR,
        )

        with patch('contracts.services.ai_contract_review.extract_clause_spans', return_value=[review_span, clear_span]):
            result = review_uploaded_contract(
                document=self.document,
                organization=self.organization,
                text='Supplier liability is unlimited. This agreement is governed by Dutch law.',
                user=self.user,
            )

        self.assertEqual(result.spans_reviewed, 2)
        self.assertEqual(result.flags_created, 1)
        flag = RiskLog.objects.get(contract=self.contract)
        self.assertEqual(flag.risk_level, RiskLog.RiskLevel.HIGH)
        self.assertEqual(flag.status, RiskLog.Status.OPEN)
        self.assertIn('Supplier liability is unlimited.', flag.description)
        self.assertEqual(flag.assigned_to, self.user)
        queue_item = CommandCenterWorkItem.objects.get(risk_log=flag)
        self.assertEqual(queue_item.source_type, CommandCenterWorkItem.SourceType.RISK)
        self.assertEqual(queue_item.action_label, 'Review flag')

    def test_upload_review_result_shape_is_stable(self):
        result = ContractReviewResult(spans_reviewed=4, flags_created=2, model='gemini-test')
        self.assertEqual(result.flags_created, 2)

    def test_contract_documents_tab_shows_a_completed_clear_upload_review(self):
        log_action(
            self.user,
            AuditLog.Action.CREATE,
            'Document',
            self.document.pk,
            str(self.document),
            organization=self.organization,
            event_type='ai.uploaded_contract_review',
            outcome=AuditLog.Outcome.SUCCESS,
            changes={
                'event': 'ai.uploaded_contract_review',
                'review_status': 'completed',
                'finding_count': 0,
                'citation_count': 0,
                'review_message': 'No potential issues were found in the clauses reviewed. Human review is still required.',
                'document_id': self.document.pk,
            },
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('contracts:contract_detail', args=[self.contract.pk]))

        self.assertContains(response, 'Latest upload review')
        self.assertContains(response, 'No potential issues were found in the clauses reviewed. Human review is still required.')
        self.assertNotContains(response, 'Extraction has not run')

    def test_needs_input_review_exposes_classifying_current_step(self):
        """Progress must stop on Classifying when metadata confirmation is still required."""
        from contracts.api.documents_ai import _run_uploaded_contract_review
        from contracts.models import DocumentOCRReview, DocumentReviewRun, OrgPolicy

        OrgPolicy.objects.create(organization=self.organization, ai_features_enabled=True)
        DocumentOCRReview.objects.create(
            organization=self.organization,
            document=self.document,
            status=DocumentOCRReview.Status.VERIFIED,
            extracted_text='This agreement is governed by Dutch law.',
            confidence_score='99.00',
            source='text-extraction',
        )
        review_run = DocumentReviewRun.objects.create(
            organization=self.organization,
            contract=self.contract,
            document=self.document,
            status=DocumentReviewRun.Status.UPLOADED,
            current_step='Uploaded',
        )
        self.client.force_login(self.user)
        request = self.client.request().wsgi_request
        request.user = self.user

        review = _run_uploaded_contract_review(
            request=request,
            organization=self.organization,
            document=self.document,
            review_run=review_run,
        )

        self.assertEqual(review['status'], 'needs-input')
        self.assertEqual(review['current_step'], 'Classifying')
        self.assertIn('Counterparty', review['pending_confirmations'])
        review_run.refresh_from_db()
        self.assertEqual(review_run.current_step, 'Classifying')
        self.assertEqual(review_run.status, DocumentReviewRun.Status.CLASSIFICATION_REQUIRED)

    def test_upload_confirmation_metadata_treats_form_values_as_confirmed(self):
        from contracts.api.documents_ai import _classification_pending_labels, _seed_upload_confirmation_metadata
        from contracts.models import DocumentOCRReview

        self.contract.counterparty = 'Acme Corp'
        self.contract.contract_type = Contract.ContractType.MSA
        self.contract.governing_law = 'Netherlands'
        self.contract.value = Decimal('12000.00')
        self.contract.save()
        DocumentOCRReview.objects.create(
            organization=self.organization,
            document=self.document,
            status=DocumentOCRReview.Status.VERIFIED,
            extracted_text='Payment is due within 30 days of invoice. This agreement is governed by Dutch law.',
            confidence_score='99.00',
            source='text-extraction',
        )

        metadata = _seed_upload_confirmation_metadata(self.contract, self.document)

        self.assertTrue(metadata.get('governing_law_confirmed'))
        self.assertTrue(metadata.get('value_confirmed'))
        self.assertTrue(metadata.get('payment_terms_confirmed'))
        self.assertTrue((metadata.get('payment_terms') or '').strip())
        self.assertEqual(_classification_pending_labels(self.contract, metadata), [])
