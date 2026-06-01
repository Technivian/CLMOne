"""Tests for billing service."""
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from contracts.services.billing import BillingService


def _make_plan(name='PROFESSIONAL', max_users=20, max_contracts=200, max_api=10000, price='49.00'):
    p = MagicMock()
    p.name = name
    p.max_users = max_users
    p.max_contracts = max_contracts
    p.max_api_calls_per_month = max_api
    p.price_monthly = Decimal(price)
    return p


class TestBillingService(unittest.TestCase):
    def setUp(self):
        self.svc = BillingService()
        self.org = MagicMock()
        self.org.pk = 3

    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_get_plan_from_subscription(self, MockSub):
        plan = _make_plan()
        sub = MagicMock()
        sub.plan = plan
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = sub
        result = self.svc.get_plan(self.org)
        self.assertEqual(result.name, 'PROFESSIONAL')

    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_get_plan_defaults_to_free(self, MockSub):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        plan = self.svc.get_plan(self.org)
        self.assertEqual(plan.name, 'FREE')
        self.assertEqual(plan.max_users, 5)

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_get_current_usage(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 3
        MockContract.objects.filter.return_value.count.return_value = 10
        MockToken.objects.filter.return_value.count.return_value = 2
        usage = self.svc.get_current_usage(self.org)
        self.assertEqual(usage.user_count, 3)
        self.assertEqual(usage.contract_count, 10)
        self.assertFalse(usage.overage_users)  # 3 <= 5

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_overage_users_detected(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 10  # > 5
        MockContract.objects.filter.return_value.count.return_value = 5
        MockToken.objects.filter.return_value.count.return_value = 0
        usage = self.svc.get_current_usage(self.org)
        self.assertTrue(usage.overage_users)
        self.assertTrue(usage.any_overage)

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_check_limits_within(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 1
        MockContract.objects.filter.return_value.count.return_value = 5
        MockToken.objects.filter.return_value.count.return_value = 0
        limits = self.svc.check_limits(self.org)
        self.assertTrue(limits['within_limits'])

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_check_limits_overage(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 1
        MockContract.objects.filter.return_value.count.return_value = 100  # > 50
        MockToken.objects.filter.return_value.count.return_value = 0
        limits = self.svc.check_limits(self.org)
        self.assertFalse(limits['within_limits'])
        self.assertTrue(limits['overage_contracts'])

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    @patch('contracts.services.billing.UsageRecord')
    def test_record_usage_creates_record(self, MockUR, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 2
        MockContract.objects.filter.return_value.count.return_value = 5
        MockToken.objects.filter.return_value.count.return_value = 1
        record = MagicMock()
        MockUR.objects.update_or_create.return_value = (record, True)
        result = self.svc.record_usage(self.org)
        self.assertTrue(MockUR.objects.update_or_create.called)

    def test_free_plan_defaults(self):
        from contracts.services.billing import _FREE_PLAN_DEFAULTS
        self.assertEqual(_FREE_PLAN_DEFAULTS['max_users'], 5)
        self.assertEqual(_FREE_PLAN_DEFAULTS['price_monthly'], 0)

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_usage_period_fields_present(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 1
        MockContract.objects.filter.return_value.count.return_value = 1
        MockToken.objects.filter.return_value.count.return_value = 0
        usage = self.svc.get_current_usage(self.org)
        self.assertIsNotNone(usage.period_start)
        self.assertIsNotNone(usage.period_end)
        self.assertEqual(usage.plan_name, 'FREE')

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_no_overage_when_all_within_limits(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 2
        MockContract.objects.filter.return_value.count.return_value = 10
        MockToken.objects.filter.return_value.count.return_value = 0
        usage = self.svc.get_current_usage(self.org)
        self.assertFalse(usage.any_overage)


if __name__ == '__main__':
    unittest.main()
