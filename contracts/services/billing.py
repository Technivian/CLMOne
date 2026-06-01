"""Billing service — usage tracking, plan limits, and overage detection."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from contracts.models import (
    BillingPlan,
    Contract,
    Organization,
    OrganizationAPIToken,
    OrganizationMembership,
    OrgBillingSubscription,
    UsageRecord,
)

_FREE_PLAN_DEFAULTS = {
    'max_users': 5,
    'max_contracts': 50,
    'max_api_calls_per_month': 1000,
    'price_monthly': 0,
}


@dataclass
class UsageSummary:
    org_id: int
    plan_name: str
    period_start: str
    period_end: str
    user_count: int
    contract_count: int
    api_call_count: int
    max_users: int
    max_contracts: int
    max_api_calls_per_month: int
    overage_users: bool
    overage_contracts: bool
    overage_api_calls: bool

    @property
    def any_overage(self) -> bool:
        return self.overage_users or self.overage_contracts or self.overage_api_calls


class BillingService:
    def get_plan(self, org: Organization) -> BillingPlan:
        sub = OrgBillingSubscription.objects.filter(organization=org).select_related('plan').first()
        if sub:
            return sub.plan
        # Return a virtual free plan without hitting DB
        plan = BillingPlan(
            name='FREE',
            max_users=_FREE_PLAN_DEFAULTS['max_users'],
            max_contracts=_FREE_PLAN_DEFAULTS['max_contracts'],
            max_api_calls_per_month=_FREE_PLAN_DEFAULTS['max_api_calls_per_month'],
            price_monthly=_FREE_PLAN_DEFAULTS['price_monthly'],
        )
        return plan

    def get_current_usage(self, org: Organization) -> UsageSummary:
        today = date.today()
        period_start = today.replace(day=1)
        import calendar
        last_day = calendar.monthrange(today.year, today.month)[1]
        period_end = today.replace(day=last_day)

        plan = self.get_plan(org)
        user_count = OrganizationMembership.objects.filter(organization=org, is_active=True).count()
        contract_count = Contract.objects.filter(organization=org).count()
        # API call count: count active tokens as proxy (real counter would come from a request log)
        api_call_count = OrganizationAPIToken.objects.filter(organization=org, is_active=True).count() * 10

        overage_users = user_count > plan.max_users
        overage_contracts = contract_count > plan.max_contracts
        overage_api = api_call_count > plan.max_api_calls_per_month

        return UsageSummary(
            org_id=org.pk,
            plan_name=plan.name,
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            user_count=user_count,
            contract_count=contract_count,
            api_call_count=api_call_count,
            max_users=plan.max_users,
            max_contracts=plan.max_contracts,
            max_api_calls_per_month=plan.max_api_calls_per_month,
            overage_users=overage_users,
            overage_contracts=overage_contracts,
            overage_api_calls=overage_api,
        )

    def record_usage(self, org: Organization) -> UsageRecord:
        summary = self.get_current_usage(org)
        period_start = date.fromisoformat(summary.period_start)
        record, _ = UsageRecord.objects.update_or_create(
            organization=org,
            period_start=period_start,
            defaults={
                'period_end': date.fromisoformat(summary.period_end),
                'user_count': summary.user_count,
                'contract_count': summary.contract_count,
                'api_call_count': summary.api_call_count,
                'overage_users': summary.overage_users,
                'overage_contracts': summary.overage_contracts,
                'overage_api_calls': summary.overage_api_calls,
            },
        )
        return record

    def check_limits(self, org: Organization) -> dict:
        summary = self.get_current_usage(org)
        return {
            'within_limits': not summary.any_overage,
            'overage_users': summary.overage_users,
            'overage_contracts': summary.overage_contracts,
            'overage_api_calls': summary.overage_api_calls,
        }


def get_billing_service() -> BillingService:
    return BillingService()
