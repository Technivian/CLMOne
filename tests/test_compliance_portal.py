"""Tests for compliance portal service."""
import unittest
from unittest.mock import MagicMock, patch


def _make_policy(mfa=True, data_transfer=True, ai=True, public=False, retention=2555):
    p = MagicMock()
    p.mfa_required = mfa
    p.data_transfer_review_required = data_transfer
    p.ai_features_enabled = ai
    p.allow_public_sharing = public
    p.retention_period_days = retention
    return p


class TestCompliancePortalService(unittest.TestCase):
    def setUp(self):
        from contracts.services.compliance_portal import CompliancePortalService
        self.svc = CompliancePortalService()
        self.org = MagicMock()
        self.org.pk = 5
        self.org.name = 'Acme Corp'

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_generate_trust_report(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 5
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 3
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 2
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 20
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 2
        MockAudit.objects.filter.return_value.count.return_value = 100
        MockMem.objects.filter.return_value.values_list.return_value = [1, 2]
        report = self.svc.generate_trust_report(self.org)
        self.assertEqual(report.org_id, 5)
        self.assertEqual(report.org_name, 'Acme Corp')
        self.assertIn('mfa_required', report.policy_summary)
        self.assertIsNotNone(report.generated_at)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_export_compliance_bundle(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 5
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 10
        MockMem.objects.filter.return_value.values_list.return_value = [1]
        MockMem.objects.filter.return_value.count.return_value = 1
        bundle = self.svc.export_compliance_bundle(self.org)
        self.assertEqual(bundle['export_version'], '1.0')
        self.assertIn('policy_summary', bundle)
        self.assertIn('dsar_stats', bundle)
        self.assertIn('ai_governance', bundle)
        self.assertIn('member_count', bundle)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_ai_governance_fields(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 0
        MockMem.objects.filter.return_value.values_list.return_value = []
        report = self.svc.generate_trust_report(self.org)
        self.assertTrue(report.ai_governance['audit_trail'])
        self.assertIn('extraction_model', report.ai_governance)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_retention_config(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(retention=730), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 0
        MockMem.objects.filter.return_value.values_list.return_value = []
        report = self.svc.generate_trust_report(self.org)
        self.assertEqual(report.retention_config['retention_period_days'], 730)
        self.assertAlmostEqual(report.retention_config['retention_period_years'], 2.0, places=0)

    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_get_policy_creates_if_missing(self, MockPolicy):
        policy = _make_policy()
        MockPolicy.objects.get_or_create.return_value = (policy, True)
        result = self.svc._get_policy(self.org)
        self.assertEqual(result, policy)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_dsar_stats_completion_rate(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 10
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 8
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 2
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 0
        MockMem.objects.filter.return_value.values_list.return_value = []
        report = self.svc.generate_trust_report(self.org)
        self.assertEqual(report.dsar_stats['total'], 10)
        self.assertEqual(report.dsar_stats['completion_rate_pct'], 80.0)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_dsar_stats_zero_division(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 0
        MockMem.objects.filter.return_value.values_list.return_value = []
        report = self.svc.generate_trust_report(self.org)
        self.assertEqual(report.dsar_stats['completion_rate_pct'], 0)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_contract_stats_in_report(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 15
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 2
        MockAudit.objects.filter.return_value.count.return_value = 50
        MockMem.objects.filter.return_value.values_list.return_value = [1, 2]
        report = self.svc.generate_trust_report(self.org)
        self.assertEqual(report.contract_stats['total'], 15)
        self.assertIn('by_status', report.contract_stats)

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_audit_counts_by_action(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 200
        MockMem.objects.filter.return_value.values_list.return_value = [1]
        report = self.svc.generate_trust_report(self.org)
        self.assertIn('by_action', report.audit_counts)
        self.assertIn('create', report.audit_counts['by_action'])

    @patch('contracts.services.compliance_portal.AuditLog')
    @patch('contracts.services.compliance_portal.Contract')
    @patch('contracts.services.compliance_portal.DSARRequest')
    @patch('contracts.services.compliance_portal.OrganizationMembership')
    @patch('contracts.services.compliance_portal.OrgPolicy')
    def test_bundle_has_export_version(self, MockPolicy, MockMem, MockDSAR, MockContract, MockAudit):
        MockPolicy.objects.get_or_create.return_value = (_make_policy(), False)
        MockDSAR.objects.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.count.return_value = 0
        MockDSAR.objects.filter.return_value.exclude.return_value.__iter__ = MagicMock(return_value=iter([]))
        MockContract.objects.filter.return_value.count.return_value = 0
        MockContract.objects.filter.return_value.filter.return_value.count.return_value = 0
        MockAudit.objects.filter.return_value.count.return_value = 0
        MockMem.objects.filter.return_value.values_list.return_value = []
        MockMem.objects.filter.return_value.count.return_value = 0
        bundle = self.svc.export_compliance_bundle(self.org)
        self.assertEqual(bundle['export_version'], '1.0')
        self.assertIn('organization', bundle)
        self.assertEqual(bundle['organization']['name'], 'Acme Corp')


if __name__ == '__main__':
    unittest.main()
