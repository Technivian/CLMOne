"""Tests for mandatory clause enforcement service."""
from unittest import TestCase
from unittest.mock import MagicMock, patch


def _make_org(pk=1):
    org = MagicMock()
    org.pk = pk
    return org


def _make_contract(pk=1, title='Test Contract', contract_type='MSA', content='', org=None):
    c = MagicMock()
    c.pk = pk
    c.title = title
    c.contract_type = contract_type
    c.content = content
    c.organization = org or _make_org()
    c.organization_id = c.organization.pk
    return c


def _make_clause(pk=1, title='Indemnity Clause', jurisdiction='GLOBAL', applicable_types='', fallback=''):
    cl = MagicMock()
    cl.pk = pk
    cl.title = title
    cl.jurisdiction_scope = jurisdiction
    cl.applicable_contract_types = applicable_types
    cl.fallback_content = fallback
    return cl


class TestMandatoryClauseEnforcementService(TestCase):
    def _svc(self):
        from contracts.services.mandatory_clauses import MandatoryClauseEnforcementService
        return MandatoryClauseEnforcementService()

    @patch('contracts.services.mandatory_clauses.clause_applies_to_contract', return_value=True)
    @patch('contracts.services.mandatory_clauses.ClauseTemplate')
    def test_compliant_contract_no_missing(self, mock_ct, mock_applies):
        clause = _make_clause(pk=1, title='Indemnity Clause', fallback='We accept')
        mock_ct.objects.filter.return_value.prefetch_related.return_value = [clause]
        contract = _make_contract(content='This agreement includes the Indemnity Clause for all parties.')
        report = self._svc().check_contract_compliance(contract)
        assert report.is_compliant is True
        assert len(report.missing_mandatory_clauses) == 0

    @patch('contracts.services.mandatory_clauses.clause_applies_to_contract', return_value=True)
    @patch('contracts.services.mandatory_clauses.ClauseTemplate')
    def test_non_compliant_contract_has_missing(self, mock_ct, mock_applies):
        clause = _make_clause(pk=2, title='Data Privacy Clause', fallback='Fallback text')
        mock_ct.objects.filter.return_value.prefetch_related.return_value = [clause]
        contract = _make_contract(content='This is a sales agreement.')
        report = self._svc().check_contract_compliance(contract)
        assert report.is_compliant is False
        assert len(report.missing_mandatory_clauses) == 1
        assert report.missing_mandatory_clauses[0].clause_title == 'Data Privacy Clause'

    @patch('contracts.services.mandatory_clauses.clause_applies_to_contract', return_value=True)
    @patch('contracts.services.mandatory_clauses.ClauseTemplate')
    def test_fallback_available_flag(self, mock_ct, mock_applies):
        clause_with_fallback = _make_clause(pk=3, title='Liability Limit', fallback='Company liability capped at $1M')
        clause_no_fallback = _make_clause(pk=4, title='IP Assignment', fallback='')
        mock_ct.objects.filter.return_value.prefetch_related.return_value = [clause_with_fallback, clause_no_fallback]
        contract = _make_contract(content='Standard SaaS terms.')
        report = self._svc().check_contract_compliance(contract)
        missing_by_id = {m.clause_id: m for m in report.missing_mandatory_clauses}
        assert missing_by_id[3].fallback_available is True
        assert missing_by_id[4].fallback_available is False

    def test_no_org_returns_compliant(self):
        contract = _make_contract()
        contract.organization = None
        contract.organization_id = None
        report = self._svc().check_contract_compliance(contract)
        assert report.is_compliant is True

    @patch('contracts.services.mandatory_clauses.clause_applies_to_contract', return_value=False)
    @patch('contracts.services.mandatory_clauses.ClauseTemplate')
    def test_clause_not_applicable_ignored(self, mock_ct, mock_applies):
        clause = _make_clause(pk=5, title='GDPR Clause')
        mock_ct.objects.filter.return_value.prefetch_related.return_value = [clause]
        contract = _make_contract(content='Basic NDA text.')
        report = self._svc().check_contract_compliance(contract)
        assert report.is_compliant is True

    @patch('contracts.services.mandatory_clauses.clause_applies_to_contract', return_value=True)
    @patch('contracts.services.mandatory_clauses.ClauseTemplate')
    def test_get_missing_mandatory_clauses_direct(self, mock_ct, mock_applies):
        clause = _make_clause(pk=6, title='Force Majeure')
        mock_ct.objects.filter.return_value.prefetch_related.return_value = [clause]
        contract = _make_contract(content='This contract has warranty terms only.')
        missing = self._svc().get_missing_mandatory_clauses(contract)
        assert len(missing) == 1
        assert missing[0].clause_id == 6

    @patch('contracts.services.mandatory_clauses.MandatoryClauseEnforcementService.check_contract_compliance')
    @patch('contracts.services.mandatory_clauses.Contract')
    def test_org_compliance_summary_all_compliant(self, mock_contract, mock_check):
        from contracts.services.mandatory_clauses import ContractComplianceReport
        org = _make_org(pk=10)
        contracts = [_make_contract(pk=i, org=org) for i in range(1, 4)]
        mock_qs = MagicMock()
        mock_qs.count.return_value = 3
        mock_qs.__iter__ = lambda s: iter(contracts)
        mock_contract.objects.filter.return_value = mock_qs

        def side_effect(contract):
            return ContractComplianceReport(
                contract_id=contract.pk,
                contract_title=contract.title,
                contract_type=contract.contract_type,
                is_compliant=True,
            )
        mock_check.side_effect = side_effect
        summary = self._svc().get_org_compliance_summary(org)
        assert summary.total_contracts_checked == 3
        assert summary.compliant_contracts == 3
        assert summary.compliance_rate_pct == 100.0

    @patch('contracts.services.mandatory_clauses.Contract')
    def test_org_compliance_summary_empty(self, mock_contract):
        org = _make_org(pk=99)
        qs = MagicMock()
        qs.count.return_value = 0
        mock_contract.objects.filter.return_value = qs
        summary = self._svc().get_org_compliance_summary(org)
        assert summary.total_contracts_checked == 0
        assert summary.compliance_rate_pct == 0
