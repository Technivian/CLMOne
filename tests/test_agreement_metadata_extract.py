"""Unit tests for Upload & Review agreement metadata extraction."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from contracts.models import Contract
from contracts.services.agreement_metadata_extract import (
    extract_agreement_metadata,
    extract_text_from_upload,
)


SAMPLE_TEXT = """
MASTER SERVICES AGREEMENT
between Acme Legal BV and Northwind Supplies Ltd.

This Agreement is effective as of 15 January 2026 and expires on 15 January 2028.
The contract value is EUR 125,000.00.
This Agreement shall be governed by the laws of the Netherlands.
Personal data processing and GDPR controller-processor obligations apply, including subprocessors.
"""


class AgreementMetadataExtractTests(TestCase):
    def test_extracts_core_fields_with_confidence(self):
        result = extract_agreement_metadata(SAMPLE_TEXT, filename='msa-northwind.pdf')
        self.assertTrue(result.text_available)
        self.assertEqual(result.contract_type.value, Contract.ContractType.MSA)
        self.assertIn(result.contract_type.confidence, {'high', 'medium'})
        self.assertTrue(result.counterparty.value)
        self.assertEqual(result.start_date.value, '2026-01-15')
        self.assertEqual(result.end_date.value, '2028-01-15')
        self.assertIn('Netherlands', result.governing_law.value)
        self.assertEqual(result.value.value, '125000.00')
        self.assertEqual(result.currency.value, 'EUR')
        self.assertEqual(result.possible_dpa.value, 'true')

    def test_filename_fallback_for_title_when_text_thin(self):
        result = extract_agreement_metadata('Short.', filename='Supplier_Agreement_Q1.txt')
        self.assertEqual(result.title.value, 'Supplier Agreement Q1')
        self.assertEqual(result.title.confidence, 'low')

    def test_image_pdf_message_when_no_text(self):
        result = extract_agreement_metadata('', filename='scan.pdf', extraction_source='manual-review-image-pdf')
        self.assertFalse(result.text_available)
        self.assertIn('scanned', result.message.lower())

    def test_extract_text_from_plain_upload(self):
        upload = SimpleUploadedFile('nda.txt', b'Non-Disclosure Agreement between A and B.', content_type='text/plain')
        text, source = extract_text_from_upload(upload, 'nda.txt')
        self.assertIn('Non-Disclosure', text)
        self.assertEqual(source, 'text-extraction')
