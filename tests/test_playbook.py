"""Tests for playbook service."""
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _make_org(pk=1):
    org = MagicMock()
    org.pk = pk
    return org


def _make_playbook(pk=1, name='Standard NDA Playbook', jurisdiction='GLOBAL', risk_level='LOW'):
    pb = MagicMock()
    pb.pk = pk
    pb.name = name
    pb.description = 'A test playbook'
    pb.jurisdiction_scope = jurisdiction
    pb.risk_level = risk_level
    pb.fallback_position = 'Accept with minor modifications'
    pb.is_active = True
    return pb


def _make_variant(clause_pk=10, clause_title='Indemnity', template_content='Standard indemnity text'):
    template = MagicMock()
    template.pk = clause_pk
    template.title = clause_title
    template.content = template_content
    template.fallback_content = 'We accept limited indemnity'
    template.playbook_notes = 'Negotiate down to 2x fees'
    template.jurisdiction_scope = 'GLOBAL'
    v = MagicMock()
    v.template = template
    v.fallback_content = 'Variant fallback'
    v.playbook_notes = 'Variant notes'
    v.jurisdiction_scope = 'EU'
    return v


class TestPlaybookService(TestCase):
    def _svc(self):
        from contracts.services.playbook import PlaybookService
        return PlaybookService()

    @patch('contracts.services.playbook.ClausePlaybook')
    def test_list_playbooks_no_filter(self, mock_pb):
        org = _make_org()
        pb1 = _make_playbook(pk=1, name='Alpha')
        pb2 = _make_playbook(pk=2, name='Beta')
        mock_pb.objects.filter.return_value.order_by.return_value = [pb1, pb2]
        results = self._svc().list_playbooks(org)
        assert len(results) == 2
        assert results[0].name == 'Alpha'

    @patch('contracts.services.playbook.ClausePlaybook')
    def test_list_playbooks_jurisdiction_filter(self, mock_pb):
        org = _make_org()
        chained_qs = MagicMock()
        chained_qs.filter.return_value = []
        mock_pb.objects.filter.return_value.order_by.return_value = chained_qs
        self._svc().list_playbooks(org, jurisdiction='EU')
        assert mock_pb.objects.filter.called

    @patch('contracts.services.playbook.ClauseVariant')
    @patch('contracts.services.playbook.ClausePlaybook')
    def test_get_playbook_with_clauses(self, mock_pb, mock_variant):
        org = _make_org()
        playbook = _make_playbook(pk=5)
        mock_pb.objects.get.return_value = playbook
        variant = _make_variant()
        qs = MagicMock()
        qs.select_related.return_value.order_by.return_value = [variant]
        mock_variant.objects.filter.return_value = qs
        result = self._svc().get_playbook(5, org)
        assert result.playbook_id == 5
        assert len(result.clauses) == 1
        assert result.clauses[0].clause_id == 10

    @patch('contracts.services.playbook.ClausePlaybook')
    def test_get_playbook_not_found_raises(self, mock_pb):
        from contracts.services.playbook import _ClausePlaybookDoesNotExist
        mock_pb.objects.get.side_effect = _ClausePlaybookDoesNotExist
        org = _make_org()
        with self.assertRaises(_ClausePlaybookDoesNotExist):
            self._svc().get_playbook(999, org)

    @patch('contracts.services.playbook.ClausePlaybook')
    def test_get_playbooks_for_contract_no_org(self, mock_pb):
        contract = MagicMock()
        contract.organization_id = None
        results = self._svc().get_playbooks_for_contract(contract)
        assert results == []

    @patch('contracts.services.playbook.ClausePlaybook')
    def test_get_playbooks_for_contract_jurisdiction_match(self, mock_pb):
        org = _make_org()
        contract = MagicMock()
        contract.organization_id = 1
        contract.organization = org
        contract.jurisdiction = 'EU'
        contract.risk_level = 'HIGH'
        pb_global = _make_playbook(pk=1, name='Global PB', jurisdiction='GLOBAL', risk_level='')
        pb_eu = _make_playbook(pk=2, name='EU PB', jurisdiction='EU', risk_level='HIGH')
        mock_pb.objects.filter.return_value = [pb_global, pb_eu]
        results = self._svc().get_playbooks_for_contract(contract)
        assert len(results) == 2
        # EU playbook should rank higher (score 4) vs global (score 1+risk match 0)
        ids = [r.playbook_id for r in results]
        assert 2 in ids

    @patch('contracts.services.playbook.resolve_clause_variant')
    @patch('contracts.services.playbook.ClauseTemplate')
    def test_resolve_clause_for_playbook(self, mock_ct, mock_resolve):
        from contracts.services.clause_variants import ResolvedClauseVariant
        template = MagicMock()
        template.pk = 10
        template.title = 'Indemnity'
        template.content = 'Standard text'
        template.fallback_content = 'Fallback'
        template.playbook_notes = 'Notes'
        template.jurisdiction_scope = 'GLOBAL'
        mock_ct.objects.get.return_value = template
        resolved = ResolvedClauseVariant(
            variant=None,
            playbook_name='',
            fallback_content='Resolved fallback',
            playbook_notes='Resolved notes',
            score=2,
        )
        mock_resolve.return_value = resolved
        contract = MagicMock()
        result = self._svc().resolve_clause_for_playbook(10, contract)
        assert result.clause_id == 10
        assert result.variant_content == 'Resolved fallback'

    @patch('contracts.services.playbook.ClauseTemplate')
    def test_resolve_clause_not_found_returns_none(self, mock_ct):
        from contracts.services.playbook import _ClauseTemplateDoesNotExist
        mock_ct.objects.get.side_effect = _ClauseTemplateDoesNotExist
        contract = MagicMock()
        result = self._svc().resolve_clause_for_playbook(999, contract)
        assert result is None
