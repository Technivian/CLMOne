"""Stripe billing integration — checkout, customer portal, and webhook handling."""

from __future__ import annotations

import datetime
import logging
from datetime import timezone as dt_timezone
from typing import TYPE_CHECKING

import stripe
from django.conf import settings
from django.utils import timezone

from contracts.models import BillingPlan, Organization, OrgBillingSubscription, OrganizationMembership

logger = logging.getLogger(__name__)


def _price_id_to_tier() -> dict[str, str]:
    """Return a mapping of configured Stripe Price IDs to BillingPlan tier names."""
    mapping: dict[str, str] = {}
    for tier in ('STARTER', 'PROFESSIONAL'):
        price_id = getattr(settings, f'STRIPE_PRICE_{tier}', '')
        if price_id:
            mapping[price_id] = tier
    return mapping


class StripeService:
    def __init__(self) -> None:
        stripe.api_key = settings.STRIPE_SECRET_KEY

    # ------------------------------------------------------------------
    # Customer management
    # ------------------------------------------------------------------

    def get_or_create_customer(
        self,
        org: Organization,
        sub: OrgBillingSubscription,
    ) -> stripe.Customer:
        if sub.stripe_customer_id:
            return stripe.Customer.retrieve(sub.stripe_customer_id)

        # Fetch an admin email for the Stripe customer record
        admin_mem = (
            OrganizationMembership.objects.filter(organization=org, is_active=True)
            .select_related('user')
            .order_by('id')
            .first()
        )
        email = admin_mem.user.email if admin_mem else ''

        customer = stripe.Customer.create(
            email=email,
            name=org.name,
            metadata={'org_id': str(org.pk), 'org_slug': org.slug},
        )
        sub.stripe_customer_id = customer.id
        sub.save(update_fields=['stripe_customer_id', 'updated_at'])
        return customer

    # ------------------------------------------------------------------
    # Checkout
    # ------------------------------------------------------------------

    def create_checkout_session(
        self,
        org: Organization,
        sub: OrgBillingSubscription,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> stripe.checkout.Session:
        customer = self.get_or_create_customer(org, sub)
        return stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            metadata={'org_id': str(org.pk), 'price_id': price_id},
        )

    # ------------------------------------------------------------------
    # Customer portal (self-service plan changes / cancellation)
    # ------------------------------------------------------------------

    def create_portal_session(
        self,
        org: Organization,
        sub: OrgBillingSubscription,
        return_url: str,
    ) -> stripe.billing_portal.Session:
        if not sub.stripe_customer_id:
            raise ValueError(f'No Stripe customer for org {org.pk}')
        return stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=return_url,
        )

    # ------------------------------------------------------------------
    # Webhook handling
    # ------------------------------------------------------------------

    def construct_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        return stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )

    def handle_webhook_event(self, event: stripe.Event) -> None:
        handlers = {
            'checkout.session.completed': self._on_checkout_completed,
            'customer.subscription.updated': self._on_subscription_changed,
            'customer.subscription.deleted': self._on_subscription_changed,
            'invoice.payment_succeeded': self._on_invoice_paid,
            'invoice.payment_failed': self._on_invoice_failed,
        }
        handler = handlers.get(event.type)
        if handler:
            handler(event.data.object)
        else:
            logger.debug('stripe_webhook: unhandled event type %s', event.type)

    def _on_checkout_completed(self, session: stripe.checkout.Session) -> None:
        org_id = (session.metadata or {}).get('org_id')
        price_id = (session.metadata or {}).get('price_id', '')
        if not org_id:
            logger.warning('stripe_webhook: checkout.session.completed missing org_id')
            return

        sub = OrgBillingSubscription.objects.filter(organization_id=org_id).first()
        if not sub:
            logger.warning('stripe_webhook: no subscription row for org_id %s', org_id)
            return

        # Map price → plan tier and upgrade the local plan
        tier = _price_id_to_tier().get(price_id)
        if tier:
            new_plan = BillingPlan.objects.filter(name=tier).first()
            if new_plan:
                sub.plan = new_plan

        sub.stripe_customer_id = session.customer or sub.stripe_customer_id
        sub.stripe_subscription_id = session.subscription or ''
        sub.stripe_price_id = price_id
        sub.subscription_status = 'active'
        sub.save(update_fields=[
            'plan', 'stripe_customer_id', 'stripe_subscription_id',
            'stripe_price_id', 'subscription_status', 'updated_at',
        ])
        logger.info('stripe_webhook: activated subscription for org_id %s (tier=%s)', org_id, tier)

    def _on_subscription_changed(self, stripe_sub: stripe.Subscription) -> None:
        sub = OrgBillingSubscription.objects.filter(
            stripe_subscription_id=stripe_sub.id
        ).first()
        if not sub:
            return

        sub.subscription_status = stripe_sub.status
        if stripe_sub.current_period_end:
            sub.current_period_end = datetime.datetime.fromtimestamp(
                stripe_sub.current_period_end, tz=dt_timezone.utc
            )

        # Sync plan if price changed (e.g. upgrade/downgrade via portal)
        items = stripe_sub.get('items', {}).get('data', [])
        if items:
            price_id = items[0].get('price', {}).get('id', '')
            tier = _price_id_to_tier().get(price_id)
            if tier:
                new_plan = BillingPlan.objects.filter(name=tier).first()
                if new_plan:
                    sub.plan = new_plan
            sub.stripe_price_id = price_id

        save_fields = ['subscription_status', 'current_period_end', 'stripe_price_id', 'plan', 'updated_at']
        sub.save(update_fields=save_fields)

    def _on_invoice_paid(self, invoice: stripe.Invoice) -> None:
        sub = OrgBillingSubscription.objects.filter(
            stripe_subscription_id=invoice.subscription
        ).first()
        if sub and sub.subscription_status != 'active':
            sub.subscription_status = 'active'
            sub.save(update_fields=['subscription_status', 'updated_at'])

    def _on_invoice_failed(self, invoice: stripe.Invoice) -> None:
        sub = OrgBillingSubscription.objects.filter(
            stripe_subscription_id=invoice.subscription
        ).first()
        if sub:
            sub.subscription_status = 'past_due'
            sub.save(update_fields=['subscription_status', 'updated_at'])


def get_stripe_service() -> StripeService:
    return StripeService()
