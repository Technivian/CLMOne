"""PAR-EXC-001 controlled-pilot monitoring coverage."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from contracts.models import ExceptionDecision, ExceptionRequest, Organization
from contracts.services.pilot_monitoring import build_pilot_daily_health


User = get_user_model()


@override_settings(
    EXCEPTION_DUAL_WRITE_ENABLED=True,
    EXCEPTION_DUAL_WRITE_ORG_ALLOWLIST='controlled-pilot-org',
)
class ExceptionPilotMonitoringTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Controlled Pilot',
            slug='controlled-pilot-org',
        )
        self.owner = User.objects.create_user(
            username='exception-monitor-owner',
            password='pass12345',
        )
        self.now = timezone.now()

    def _request(self, *, source='KEEP_EXCEPTION', correlation_id='corr-1', status='ACTIVE', expires=True):
        return ExceptionRequest.objects.create(
            organization=self.org,
            category=ExceptionRequest.ExceptionCategory.POLICY,
            title='Monitored exception',
            reason='Operational monitoring fixture',
            scope_type=ExceptionRequest.ScopeType.OTHER,
            scope_object_model='Fixture',
            scope_object_id=1,
            requester=self.owner,
            owner=self.owner,
            designated_approver=self.owner,
            authority_basis=ExceptionRequest.AuthorityBasis.PRODUCT_GOVERNANCE,
            compensating_controls='Legacy remains authoritative.',
            starts_at=self.now,
            expires_at=self.now + timedelta(days=30) if expires else None,
            status=status,
            legacy_source=source,
            correlation_id=correlation_id,
        )

    def _decision(self, request):
        return ExceptionDecision.objects.create(
            organization=self.org,
            exception_request=request,
            outcome=ExceptionDecision.Outcome.APPROVED,
            decided_by=self.owner,
            authority_basis='product_governance',
            authority_holder_id=self.owner.pk,
            starts_at=request.starts_at,
            expires_at=request.expires_at,
            decided_at=self.now,
        )

    def test_daily_health_reports_exception_dual_write_counts(self):
        approved = self._request()
        self._decision(approved)
        self._request(
            source='AI_EXCEPTION',
            correlation_id='ai-1',
            status=ExceptionRequest.Status.SUBMITTED,
        )

        summary = build_pilot_daily_health(organization=self.org)
        health = summary['exception_dual_write']

        self.assertTrue(summary['feature_flags']['EXCEPTION_DUAL_WRITE_ENABLED'])
        self.assertEqual(
            summary['feature_flags']['EXCEPTION_DUAL_WRITE_ORG_ALLOWLIST'],
            'controlled-pilot-org',
        )
        self.assertEqual(health['actions_by_source']['KEEP_EXCEPTION'], 1)
        self.assertEqual(health['actions_by_source']['AI_EXCEPTION'], 1)
        self.assertEqual(health['canonical_requests_created'], 2)
        self.assertEqual(health['canonical_decisions_created'], 1)
        self.assertEqual(health['submitted_without_decision'], 1)
        self.assertFalse(health['stop_required'])

    def test_daily_health_raises_stop_indicators_for_invalid_parity(self):
        first = self._request(correlation_id='duplicate')
        second = self._request(correlation_id='duplicate')
        self._decision(first)
        self._decision(first)
        second.expires_at = None
        second.save(update_fields=['expires_at'])

        health = build_pilot_daily_health(organization=self.org)['exception_dual_write']

        self.assertEqual(health['duplicate_correlation_groups'], 1)
        self.assertEqual(health['requests_with_multiple_decisions'], 1)
        self.assertEqual(health['active_missing_owner_or_expiry'], 1)
        self.assertTrue(health['stop_required'])
        self.assertIn('duplicate_correlation', health['stop_reasons'])
        self.assertIn('duplicate_canonical_decision', health['stop_reasons'])
        self.assertIn('active_missing_owner_or_expiry', health['stop_reasons'])
