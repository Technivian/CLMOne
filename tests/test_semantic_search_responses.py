from unittest import mock

from django.test import TestCase, override_settings

from contracts.models import ClauseTemplate, Organization
from contracts.services import semantic_search
from contracts.services.semantic_search import (
    _extract_ranked_indices,
    _llm_rank,
    _parse_provider_payload,
    rank_clause_templates_semantic,
)


class SemanticSearchResponseParsingTests(TestCase):
    def test_extract_ranked_indices_from_dict(self):
        self.assertEqual(_extract_ranked_indices({'ranked_indices': [2, 0, 1]}), [2, 0, 1])

    def test_extract_ranked_indices_from_list(self):
        self.assertEqual(_extract_ranked_indices([1, 0]), [1, 0])

    def test_extract_ranked_indices_from_object_list(self):
        payload = [{'index': 0}, {'index': 2}]
        self.assertEqual(_extract_ranked_indices(payload), [0, 2])

    def test_extract_ranked_indices_empty_list(self):
        self.assertEqual(_extract_ranked_indices([]), [])

    def test_extract_ranked_indices_malformed_returns_none(self):
        self.assertIsNone(_extract_ranked_indices({'unexpected': 'value'}))
        self.assertIsNone(_extract_ranked_indices('not-json'))

    def test_parse_provider_payload_invalid_json(self):
        self.assertIsNone(_parse_provider_payload('{bad json'))

    @override_settings(GEMINI_AI_ENABLED=True)
    def test_llm_rank_accepts_list_payload_shape(self):
        org = Organization.objects.create(name='Semantic Org', slug='semantic-org')
        clauses = [
            ClauseTemplate.objects.create(
                organization=org,
                title='Alpha confidentiality clause',
                content='Confidential information must remain secret.',
                tags='nda confidentiality',
            ),
            ClauseTemplate.objects.create(
                organization=org,
                title='Beta payment clause',
                content='Invoices are due net thirty.',
                tags='payment',
            ),
        ]

        class _FakeResponse:
            text = '[0, 1]'

        with mock.patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with mock.patch('google.genai.Client') as client_cls:
                client_cls.return_value.models.generate_content.return_value = _FakeResponse()
                ranked = _llm_rank(clauses, 'confidentiality', limit=2)

        self.assertEqual([item.pk for item in ranked], [clauses[0].pk, clauses[1].pk])

    @override_settings(GEMINI_AI_ENABLED=True)
    def test_llm_rank_malformed_payload_uses_keyword_fallback(self):
        org = Organization.objects.create(name='Fallback Org', slug='fallback-org')
        clause = ClauseTemplate.objects.create(
            organization=org,
            title='Termination clause',
            content='Either party may terminate on notice.',
            tags='termination',
        )

        class _FakeResponse:
            text = '{"unexpected": true}'

        with mock.patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with mock.patch('google.genai.Client') as client_cls:
                client_cls.return_value.models.generate_content.return_value = _FakeResponse()
                ranked = _llm_rank([clause], 'termination', limit=1)

        self.assertEqual(ranked[0].pk, clause.pk)

    @override_settings(GEMINI_AI_ENABLED=True)
    def test_provider_error_falls_back_to_keyword_rank(self):
        org = Organization.objects.create(name='Keyword Org', slug='keyword-org')
        clause = ClauseTemplate.objects.create(
            organization=org,
            title='Indemnity clause',
            content='Indemnification for third-party claims.',
            tags='indemnity',
        )

        with mock.patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            with mock.patch.object(semantic_search, '_llm_rank', side_effect=TimeoutError('provider timeout')):
                ranked = rank_clause_templates_semantic([clause], 'indemnity', limit=1)

        self.assertEqual(ranked[0].pk, clause.pk)

    @override_settings(GEMINI_AI_ENABLED=False)
    def test_disabled_provider_uses_keyword_rank(self):
        org = Organization.objects.create(name='Disabled Org', slug='disabled-org')
        clause = ClauseTemplate.objects.create(
            organization=org,
            title='Privacy clause',
            content='Personal data shall be protected.',
            tags='privacy',
        )
        ranked = rank_clause_templates_semantic([clause], 'privacy', limit=1)
        self.assertEqual(ranked[0].pk, clause.pk)
