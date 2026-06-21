"""Regression tests for the clause-search blocker (A2).

The clause search API used to 500 on any non-empty query because
`rank_clause_templates_semantic` was called with reversed arguments and the
list it returns was then treated as a queryset. A second latent 500 came from
filtering ClauseTemplate on a non-existent `jurisdiction` field.

These tests exercise the real service and the real HTTP API (no GEMINI key, so
the deterministic keyword ranker runs) against the seeded starter clause
templates, plus empty / no-result / malformed inputs.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from contracts.models import ClauseTemplate, Organization, OrganizationMembership
from contracts.services.search_api import ClauseSearchAPIService
from contracts.services.semantic_search import rank_clause_templates_semantic
from contracts.services.starter_content import ensure_org_starter_content

User = get_user_model()


class ClauseSearchServiceRegressionTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Test City', slug='test-city')
        # Seed the same starter clause templates a real pilot tenant receives.
        ensure_org_starter_content(self.org)
        self.svc = ClauseSearchAPIService()
        self.seeded_count = ClauseTemplate.objects.filter(organization=self.org).count()
        self.assertGreater(self.seeded_count, 0, 'starter content should seed clauses')

    def test_ordinary_query_against_seeded_clauses_does_not_500(self):
        # This is the exact path that used to raise AttributeError/TypeError.
        result = self.svc.search_clauses(self.org, q='confidentiality')
        self.assertIsInstance(result.results, list)
        # Keyword ranker should surface at least the confidentiality/NDA clause.
        self.assertGreaterEqual(result.total, 1)
        for row in result.results:
            self.assertIn('id', row)
            self.assertIn('jurisdiction', row)  # mapped from jurisdiction_scope

    def test_empty_query_returns_all_seeded_clauses(self):
        result = self.svc.search_clauses(self.org, q='')
        self.assertEqual(result.total, self.seeded_count)

    def test_query_with_no_matches_returns_empty_not_error(self):
        result = self.svc.search_clauses(self.org, q='zzzzz-nonexistent-term-qqq')
        self.assertEqual(result.total, 0)
        self.assertEqual(result.results, [])

    def test_malformed_query_none_does_not_500(self):
        # The API can pass None; the ranker tokenizes with .lower().
        result = self.svc.search_clauses(self.org, q=None)  # type: ignore[arg-type]
        self.assertEqual(result.total, self.seeded_count)

    def test_jurisdiction_filter_does_not_500(self):
        # Previously raised FieldError because the field is `jurisdiction_scope`.
        result = self.svc.search_clauses(
            self.org, q='', filters={'jurisdiction': 'GLOBAL'}
        )
        self.assertIsInstance(result.results, list)

    def test_pagination_is_consistent(self):
        page1 = self.svc.search_clauses(self.org, q='', page=1, page_size=2)
        self.assertEqual(page1.page_size, 2)
        self.assertEqual(page1.total, self.seeded_count)
        self.assertLessEqual(len(page1.results), 2)

    def test_tenant_scoping_preserved(self):
        other = Organization.objects.create(name='Other City', slug='other-city')
        ensure_org_starter_content(other)
        # A query in our org must never surface another org's clauses.
        result = self.svc.search_clauses(self.org, q='confidentiality')
        our_ids = set(
            ClauseTemplate.objects.filter(organization=self.org).values_list('id', flat=True)
        )
        for row in result.results:
            self.assertIn(row['id'], our_ids)


class RankClauseTemplatesContractTests(TestCase):
    """The ranking function's documented return-type contract."""

    def setUp(self):
        self.org = Organization.objects.create(name='Rank Org', slug='rank-org')
        ensure_org_starter_content(self.org)
        self.qs = ClauseTemplate.objects.filter(organization=self.org)

    def test_returns_list_not_queryset(self):
        result = rank_clause_templates_semantic(self.qs, 'confidentiality')
        self.assertIsInstance(result, list)

    def test_empty_query_returns_empty_list(self):
        self.assertEqual(rank_clause_templates_semantic(self.qs, ''), [])
        self.assertEqual(rank_clause_templates_semantic(self.qs, '   '), [])

    def test_empty_candidates_returns_empty_list(self):
        self.assertEqual(rank_clause_templates_semantic([], 'anything'), [])


class ClauseSearchAPIEndpointTests(TestCase):
    """The real authenticated HTTP journey returns 200, not 500."""

    def setUp(self):
        self.org = Organization.objects.create(name='API City', slug='api-city')
        ensure_org_starter_content(self.org)
        self.user = User.objects.create_user(username='apiuser', password='pw12345!')
        OrganizationMembership.objects.create(
            user=self.user,
            organization=self.org,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.client = Client()
        self.client.force_login(self.user)

    def _url(self):
        # Resolve by view name if available; fall back to the known path.
        return reverse('contracts:api_clause_search')

    def test_clause_search_endpoint_returns_200_with_query(self):
        resp = self.client.get(self._url(), {'q': 'confidentiality'})
        self.assertEqual(resp.status_code, 200, resp.content[:500])
        data = resp.json()
        self.assertIn('results', data)
        self.assertIn('total', data)

    def test_clause_search_endpoint_empty_query_200(self):
        resp = self.client.get(self._url(), {'q': ''})
        self.assertEqual(resp.status_code, 200)
