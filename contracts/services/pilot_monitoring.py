"""Pilot monitoring helpers and daily health summary (no contract content)."""
from __future__ import annotations

import json
from datetime import datetime, time, timedelta
from typing import Any, Dict

from django.conf import settings
from django.db.models import Count, Q
from django.utils import timezone

from contracts.models import AuditLog, Contract, Organization, OrganizationMembership
from contracts.observability import request_metrics_snapshot


def _day_bounds(day=None):
    day = day or timezone.localdate()
    start = timezone.make_aware(datetime.combine(day, time.min))
    end = start + timedelta(days=1)
    return start, end


def pilot_feature_flag_state() -> Dict[str, Any]:
    return {
        'CONTROLLED_PILOT_ENABLED': bool(getattr(settings, 'CONTROLLED_PILOT_ENABLED', False)),
        'GEMINI_AI_ENABLED': bool(getattr(settings, 'GEMINI_AI_ENABLED', False)),
        'BILLING_SELF_SERVE_ENABLED': bool(getattr(settings, 'BILLING_SELF_SERVE_ENABLED', True)),
        'TRUST_ACCOUNTING_ENABLED': bool(getattr(settings, 'TRUST_ACCOUNTING_ENABLED', True)),
        'FINANCE_APPROVAL_THRESHOLD': str(
            getattr(settings, 'FINANCE_APPROVAL_THRESHOLD', None)
            or '100000'
        ),
        'RATELIMIT_ENABLED': bool(getattr(settings, 'RATELIMIT_ENABLED', True)),
        'LOGIN_RATE_LIMIT_REQUESTS': getattr(settings, 'LOGIN_RATE_LIMIT_REQUESTS', None),
    }


def build_pilot_daily_health(organization: Organization | None = None, day=None) -> Dict[str, Any]:
    """Aggregate operational health without contract text or credentials."""
    start, end = _day_bounds(day)
    org = organization
    if org is None:
        org = Organization.objects.filter(slug='controlled-pilot-org').first()

    audits = AuditLog.objects.filter(timestamp__gte=start, timestamp__lt=end)
    contracts = Contract.objects.filter(created_at__gte=start, created_at__lt=end)
    if org is not None:
        audits = audits.filter(organization=org)
        contracts = contracts.filter(organization=org)

    # Event-type heuristics from existing AuditLog payloads (no content fields).
    legal_submits = audits.filter(
        Q(changes__event__icontains='legal')
        | Q(object_repr__icontains='Legal')
        | Q(action__icontains='submit')
    ).filter(Q(changes__approval_step='LEGAL') | Q(changes__event__icontains='msa') | Q(model_name='ApprovalRequest')).count()

    finance_submits = audits.filter(
        Q(changes__approval_step='FINANCE')
        | Q(changes__event__icontains='finance')
    ).count()

    exports = audits.filter(
        Q(changes__event__icontains='export')
        | Q(action__icontains='export')
        | Q(object_repr__icontains='export')
    ).count()

    lifecycle_failures = audits.filter(
        Q(outcome=AuditLog.Outcome.FAILURE)
        & (
            Q(changes__event__icontains='lifecycle')
            | Q(event_type__icontains='lifecycle')
        )
    ).count()

    authz_failures = audits.filter(
        Q(outcome=AuditLog.Outcome.FAILURE)
        & (
            Q(action__icontains='denied')
            | Q(changes__event__icontains='forbidden')
            | Q(changes__event__icontains='unauthorized')
        )
    ).count()

    audit_write_failures = audits.filter(
        Q(changes__event__icontains='audit') & Q(outcome=AuditLog.Outcome.FAILURE)
    ).count()

    ai_denials = audits.filter(
        Q(changes__event__icontains='ai')
        & (
            Q(outcome=AuditLog.Outcome.FAILURE)
            | Q(changes__event__icontains='denied')
            | Q(changes__event__icontains='disabled')
        )
    ).count()

    failed_actions = audits.filter(outcome=AuditLog.Outcome.FAILURE).count()
    login_failures = audits.filter(
        Q(action__icontains='login') & Q(outcome=AuditLog.Outcome.FAILURE)
    ).count()

    active_users = 0
    if org is not None:
        active_users = (
            OrganizationMembership.objects.filter(organization=org, is_active=True)
            .values('user_id')
            .distinct()
            .count()
        )

    metrics = request_metrics_snapshot()
    summary = {
        'date': str(start.date()),
        'organization': org.slug if org else None,
        'feature_flags': pilot_feature_flag_state(),
        'active_users': active_users,
        'contracts_created': contracts.count(),
        'contracts_created_by_type': list(
            contracts.values('contract_type').annotate(count=Count('id')).order_by('contract_type')
        ),
        'workflow_completions_approx': audits.filter(
            Q(changes__event__icontains='completed')
            | Q(action='UPDATE', changes__event__icontains='workflow')
        ).count(),
        'failed_actions': failed_actions,
        'login_failures': login_failures,
        'http_status_counts': metrics.get('status_counts', {}),
        'msa_legal_submissions_approx': legal_submits,
        'msa_finance_submissions_approx': finance_submits,
        'exports_approx': exports,
        'lifecycle_transition_failures': lifecycle_failures,
        'authorization_failures': authz_failures,
        'audit_event_creation_failures': audit_write_failures,
        'ai_usage_and_policy_denials_approx': ai_denials,
        'unresolved_incidents': None,  # operator-maintained in ops log
        'support_requests': None,  # operator-maintained in ops log
        'routing_anomalies': None,  # compare Finance submits vs threshold matrix in review
        'audit_anomalies': audit_write_failures,
        'notes': (
            'Counts are derived from AuditLog metadata and request metrics. '
            'Contract content, credentials, and secrets are never included.'
        ),
    }
    return summary


def format_pilot_daily_health(summary: Dict[str, Any]) -> str:
    return json.dumps(summary, indent=2, sort_keys=True, default=str)
