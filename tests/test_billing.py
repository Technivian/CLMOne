"""Tests for billing service and Stripe integration."""
import json
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch, PropertyMock

from contracts.services.billing import BillingService


def _make_plan(name='PROFESSIONAL', max_users=20, max_contracts=200, max_api=10000, price='49.00'):
    p = MagicMock()
    p.name = name
    p.max_users = max_users
    p.max_contracts = max_contracts
    p.max_api_calls_per_month = max_api
    p.price_monthly = Decimal(price)
    return p


# ---------------------------------------------------------------------------
# BillingService (existing tests — unchanged behaviour)
# ---------------------------------------------------------------------------

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
        self.assertFalse(usage.overage_users)

    @patch('contracts.services.billing.OrganizationAPIToken')
    @patch('contracts.services.billing.Contract')
    @patch('contracts.services.billing.OrganizationMembership')
    @patch('contracts.services.billing.OrgBillingSubscription')
    def test_overage_users_detected(self, MockSub, MockMem, MockContract, MockToken):
        MockSub.objects.filter.return_value.select_related.return_value.first.return_value = None
        MockMem.objects.filter.return_value.count.return_value = 10
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
        MockContract.objects.filter.return_value.count.return_value = 100
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
        self.svc.record_usage(self.org)
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


# ---------------------------------------------------------------------------
# StripeService — webhook event handling
# ---------------------------------------------------------------------------

class TestStripeService(unittest.TestCase):
    """Test StripeService webhook handlers with mocked Stripe SDK and DB."""

    def _make_service(self):
        with patch('stripe.api_key', ''):
            from contracts.services.stripe_service import StripeService
            svc = StripeService.__new__(StripeService)
            return svc

    def test_on_checkout_completed_activates_subscription(self):
        svc = self._make_service()
        session = MagicMock()
        session.metadata = {'org_id': '42', 'price_id': 'price_starter_123'}
        session.customer = 'cus_abc'
        session.subscription = 'sub_abc'

        mock_sub = MagicMock()
        mock_sub.plan = MagicMock()

        with patch('contracts.services.stripe_service._price_id_to_tier', return_value={'price_starter_123': 'STARTER'}):
            with patch('contracts.services.stripe_service.BillingPlan') as MockPlan:
                with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
                    MockOBS.objects.filter.return_value.first.return_value = mock_sub
                    MockPlan.objects.filter.return_value.first.return_value = MagicMock(name='STARTER')
                    svc._on_checkout_completed(session)

        mock_sub.save.assert_called_once()
        self.assertEqual(mock_sub.subscription_status, 'active')
        self.assertEqual(mock_sub.stripe_customer_id, 'cus_abc')
        self.assertEqual(mock_sub.stripe_subscription_id, 'sub_abc')

    def test_on_checkout_completed_missing_org_id_is_noop(self):
        svc = self._make_service()
        session = MagicMock()
        session.metadata = {}

        with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
            svc._on_checkout_completed(session)
            MockOBS.objects.filter.assert_not_called()

    def test_on_subscription_changed_updates_status(self):
        svc = self._make_service()
        stripe_sub = MagicMock()
        stripe_sub.id = 'sub_abc'
        stripe_sub.status = 'past_due'
        stripe_sub.current_period_end = 1_700_000_000
        stripe_sub.get.return_value = {'data': []}

        mock_sub = MagicMock()

        with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
            MockOBS.objects.filter.return_value.first.return_value = mock_sub
            with patch('contracts.services.stripe_service._price_id_to_tier', return_value={}):
                svc._on_subscription_changed(stripe_sub)

        self.assertEqual(mock_sub.subscription_status, 'past_due')
        mock_sub.save.assert_called_once()

    def test_on_subscription_changed_no_match_is_noop(self):
        svc = self._make_service()
        stripe_sub = MagicMock()
        stripe_sub.id = 'sub_unknown'
        stripe_sub.status = 'canceled'
        stripe_sub.current_period_end = None
        stripe_sub.get.return_value = {'data': []}

        with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
            MockOBS.objects.filter.return_value.first.return_value = None
            with patch('contracts.services.stripe_service._price_id_to_tier', return_value={}):
                svc._on_subscription_changed(stripe_sub)

        # Should not raise

    def test_on_invoice_paid_sets_active(self):
        svc = self._make_service()
        invoice = MagicMock()
        invoice.subscription = 'sub_abc'
        mock_sub = MagicMock()
        mock_sub.subscription_status = 'past_due'

        with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
            MockOBS.objects.filter.return_value.first.return_value = mock_sub
            svc._on_invoice_paid(invoice)

        self.assertEqual(mock_sub.subscription_status, 'active')
        mock_sub.save.assert_called_once()

    def test_on_invoice_failed_sets_past_due(self):
        svc = self._make_service()
        invoice = MagicMock()
        invoice.subscription = 'sub_abc'
        mock_sub = MagicMock()
        mock_sub.subscription_status = 'active'

        with patch('contracts.services.stripe_service.OrgBillingSubscription') as MockOBS:
            MockOBS.objects.filter.return_value.first.return_value = mock_sub
            svc._on_invoice_failed(invoice)

        self.assertEqual(mock_sub.subscription_status, 'past_due')
        mock_sub.save.assert_called_once()

    def test_handle_webhook_event_dispatches_checkout(self):
        svc = self._make_service()
        event = MagicMock()
        event.type = 'checkout.session.completed'
        event.data.object = MagicMock()
        event.data.object.metadata = {}

        with patch.object(svc, '_on_checkout_completed') as mock_handler:
            svc.handle_webhook_event(event)
            mock_handler.assert_called_once_with(event.data.object)

    def test_handle_webhook_event_unknown_type_is_noop(self):
        svc = self._make_service()
        event = MagicMock()
        event.type = 'some.unknown.event'
        svc.handle_webhook_event(event)  # should not raise


# ---------------------------------------------------------------------------
# Webhook view — signature validation
# ---------------------------------------------------------------------------

class TestStripeWebhookView(unittest.TestCase):

    def _post(self, body=b'{}', sig='test-sig', secret='whsec_test'):
        from django.test import RequestFactory
        rf = RequestFactory()
        req = rf.post(
            '/contracts/billing/webhook/',
            data=body,
            content_type='application/json',
        )
        req.META['HTTP_STRIPE_SIGNATURE'] = sig
        return req

    @patch('contracts.views_domains.subscription.settings')
    def test_no_webhook_secret_returns_400(self, mock_settings):
        mock_settings.STRIPE_WEBHOOK_SECRET = ''
        mock_settings.STRIPE_ENABLED = False
        from contracts.views_domains.subscription import stripe_webhook
        req = self._post()
        resp = stripe_webhook(req)
        self.assertEqual(resp.status_code, 400)

    @patch('contracts.views_domains.subscription.get_stripe_service')
    @patch('contracts.views_domains.subscription.settings')
    def test_invalid_signature_returns_400(self, mock_settings, mock_svc_factory):
        mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        mock_settings.STRIPE_ENABLED = True
        mock_svc = MagicMock()
        mock_svc.construct_event.side_effect = Exception('Bad signature')
        mock_svc_factory.return_value = mock_svc
        from contracts.views_domains.subscription import stripe_webhook
        req = self._post()
        resp = stripe_webhook(req)
        self.assertEqual(resp.status_code, 400)

    @patch('contracts.views_domains.subscription.get_stripe_service')
    @patch('contracts.views_domains.subscription.settings')
    def test_valid_event_returns_200(self, mock_settings, mock_svc_factory):
        mock_settings.STRIPE_WEBHOOK_SECRET = 'whsec_test'
        mock_settings.STRIPE_ENABLED = True
        mock_svc = MagicMock()
        mock_svc.construct_event.return_value = MagicMock(type='checkout.session.completed')
        mock_svc_factory.return_value = mock_svc
        from contracts.views_domains.subscription import stripe_webhook
        req = self._post()
        resp = stripe_webhook(req)
        self.assertEqual(resp.status_code, 200)
        mock_svc.handle_webhook_event.assert_called_once()


if __name__ == '__main__':
    unittest.main()
