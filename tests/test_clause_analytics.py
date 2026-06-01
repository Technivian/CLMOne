"""Tests for clause analytics service."""
from unittest import TestCase
from unittest.mock import MagicMock, patch, PropertyMock


def _make_org(pk=1):
    org = MagicMock()
    org.pk = pk
    return org


def _make_clause(pk=1, title='Liability Cap', jurisdiction='GLOBAL', category=None):
    c = MagicMock()
    c.pk = pk
    c.title = title
    c.jurisdiction_scope = jurisdiction
    c.category_id = None
    c.category = category
    return c


def _make_event(clause, action='ADDED', contract_id=10):
    ev = MagicMock()
    ev.clause_id = clause.pk
    ev.clause = clause
    ev.action = action
    ev.contract_id = contract_id
    return ev


class TestClauseAnalyticsService(TestCase):
    def _svc(self):
        from contracts.services.clause_analytics import ClauseAnalyticsService
        return ClauseAnalyticsService()

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_get_usage_stats_empty(self, mock_model):
        mock_qs = MagicMock()
        mock_model.objects.filter.return_value = mock_qs
        mock_qs.count.return_value = 0
        mock_qs.filter.return_value.count.return_value = 0
        mock_qs.values.return_value.distinct.return_value.count.return_value = 0
        mock_model.Action.values = ['ADDED', 'REMOVED', 'ACCEPTED', 'REJECTED', 'MODIFIED']
        org = _make_org()
        result = self._svc().get_clause_usage_stats(org)
        assert result['total_events'] == 0
        assert result['unique_clauses_used'] == 0

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_get_most_used_clauses_returns_sorted(self, mock_model):
        from contracts.services.clause_analytics import ClauseUsageEvent as RealCUE
        clause1 = _make_clause(pk=1, title='Indemnity')
        clause2 = _make_clause(pk=2, title='Limitation')
        events = [
            _make_event(clause1, action='ADDED'),
            _make_event(clause1, action='ACCEPTED'),
            _make_event(clause1, action='ADDED'),
            _make_event(clause2, action='ADDED'),
        ]
        mock_model.objects.filter.return_value.select_related.return_value = iter(events)
        mock_model.Action.ACCEPTED = 'ACCEPTED'
        mock_model.Action.REJECTED = 'REJECTED'
        mock_model.Action.MODIFIED = 'MODIFIED'
        org = _make_org()
        results = self._svc().get_most_used_clauses(org, limit=10)
        assert len(results) == 2
        assert results[0].clause_id == 1
        assert results[0].total_uses == 3

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_acceptance_rate_calculation(self, mock_model):
        clause1 = _make_clause(pk=1, title='Force Majeure')
        events = [
            _make_event(clause1, action='ACCEPTED'),
            _make_event(clause1, action='ACCEPTED'),
            _make_event(clause1, action='REJECTED'),
            _make_event(clause1, action='ADDED'),
        ]
        mock_model.objects.filter.return_value.select_related.return_value = iter(events)
        mock_model.Action.ACCEPTED = 'ACCEPTED'
        mock_model.Action.REJECTED = 'REJECTED'
        mock_model.Action.MODIFIED = 'MODIFIED'
        org = _make_org()
        results = self._svc().get_most_used_clauses(org, limit=5)
        assert results[0].accepted_count == 2
        assert results[0].rejected_count == 1
        assert results[0].acceptance_rate_pct == 50.0

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_record_usage_creates_event(self, mock_model):
        org = _make_org()
        clause = _make_clause()
        contract = MagicMock()
        mock_model.objects.create.return_value = MagicMock(pk=99, action='ADDED')
        mock_model.Action.ADDED = 'ADDED'
        ev = self._svc().record_usage(org, clause, contract, 'ADDED', note='test')
        assert mock_model.objects.create.called
        assert ev.pk == 99

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_dependency_graph_empty(self, mock_model):
        mock_model.objects.filter.return_value.values.return_value = []
        mock_model.Action.ADDED = 'ADDED'
        org = _make_org()
        nodes = self._svc().get_dependency_graph(org)
        assert nodes == []

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_dependency_graph_co_occurrence(self, mock_model):
        mock_model.Action.ADDED = 'ADDED'
        events_data = [
            {'contract_id': 1, 'clause_id': 10, 'clause__title': 'Indemnity'},
            {'contract_id': 1, 'clause_id': 20, 'clause__title': 'Insurance'},
            {'contract_id': 2, 'clause_id': 10, 'clause__title': 'Indemnity'},
            {'contract_id': 2, 'clause_id': 30, 'clause__title': 'Governing Law'},
        ]
        mock_model.objects.filter.return_value.values.return_value = events_data
        org = _make_org()
        nodes = self._svc().get_dependency_graph(org)
        node_10 = next(n for n in nodes if n.clause_id == 10)
        co_ids = [c['id'] for c in node_10.co_occurring_clauses]
        assert 20 in co_ids
        assert 30 in co_ids

    @patch('contracts.services.clause_analytics.ClauseUsageEvent')
    def test_most_used_clause_with_category(self, mock_model):
        category = MagicMock()
        category.name = 'Risk'
        clause = _make_clause(pk=5, title='Warranty', category=category)
        clause.category_id = 7
        events = [_make_event(clause, action='ADDED')]
        mock_model.objects.filter.return_value.select_related.return_value = iter(events)
        mock_model.Action.ACCEPTED = 'ACCEPTED'
        mock_model.Action.REJECTED = 'REJECTED'
        mock_model.Action.MODIFIED = 'MODIFIED'
        org = _make_org()
        results = self._svc().get_most_used_clauses(org, limit=5)
        assert results[0].category == 'Risk'
