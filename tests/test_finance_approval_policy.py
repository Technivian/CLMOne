from decimal import Decimal

from django.test import TestCase, override_settings

from contracts.services.finance_approval_policy import (
    DEFAULT_FINANCE_APPROVAL_THRESHOLD,
    finance_threshold_from_field_values,
    requires_finance_approval,
)


class FinanceApprovalPolicyTests(TestCase):
    def test_below_threshold_does_not_require_finance(self):
        required, reason, audit = requires_finance_approval(value=99_999)
        self.assertFalse(required)
        self.assertIn('below', reason.lower())
        self.assertEqual(audit['finance_routing_reason'], 'value_below_threshold')

    def test_equal_to_threshold_requires_finance(self):
        required, reason, audit = requires_finance_approval(value=100_000)
        self.assertTrue(required)
        self.assertIn('100,000', reason)
        self.assertEqual(audit['finance_routing_reason'], 'value_at_or_above_threshold')

    def test_above_threshold_requires_finance(self):
        required, _, audit = requires_finance_approval(value=150_000)
        self.assertTrue(required)
        self.assertEqual(audit['finance_routing_reason'], 'value_at_or_above_threshold')

    def test_unknown_value_does_not_trigger_finance(self):
        required, reason, audit = requires_finance_approval(value=None)
        self.assertFalse(required)
        self.assertIn('unknown', reason.lower())
        self.assertEqual(audit['finance_routing_reason'], 'value_unknown')

    def test_confirmed_above_threshold_requires_finance_without_value(self):
        required, reason, audit = requires_finance_approval(
            value=None,
            confirmed_above_threshold=True,
        )
        self.assertTrue(required)
        self.assertIn('confirmed', reason.lower())
        self.assertEqual(audit['finance_routing_reason'], 'operator_confirmed_above_threshold')

    def test_total_contract_value_preferred_over_headline_value(self):
        required, _, audit = requires_finance_approval(value=50_000, total_contract_value=120_000)
        self.assertTrue(required)
        self.assertEqual(audit['finance_value_compared'], '120000')

    def test_field_values_helper_matches_policy(self):
        required, reason, audit = finance_threshold_from_field_values({'value': 100_000, 'currency': 'EUR'})
        self.assertTrue(required)
        self.assertIn('100,000', reason)
        self.assertEqual(audit['finance_approval_threshold'], str(DEFAULT_FINANCE_APPROVAL_THRESHOLD))

    @override_settings(FINANCE_APPROVAL_THRESHOLD=Decimal('75000'))
    def test_settings_override_is_respected(self):
        required, _, audit = requires_finance_approval(value=80_000)
        self.assertTrue(required)
        self.assertEqual(audit['finance_approval_threshold'], '75000')
