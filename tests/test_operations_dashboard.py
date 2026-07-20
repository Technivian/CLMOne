from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from contracts.models import BackgroundJob, Organization, OrganizationMembership
from contracts.services.operations_dashboard import (
    build_incidents,
    build_metric_cards,
    build_queue_health,
    serialize_job_row,
)


User = get_user_model()


class OperationsDashboardHelpersTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(name='Ops Org', slug='ops-org', require_mfa=False)
        self.user = User.objects.create_user(username='ops-owner', password='testpass123')
        OrganizationMembership.objects.create(
            organization=self.org,
            user=self.user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )

    def test_metric_cards_include_threshold_trend_and_health(self):
        cards = build_metric_cards(
            scheduler={'status': 'healthy', 'seconds_since_success': 30, 'stale_after_seconds': 7200},
            database={'status': 'healthy', 'latency_ms': 12, 'warn_ms': 250, 'fail_ms': 1500},
            alerts={
                'alert_status': 'OK',
                'five_xx_rate_pct': 0.1,
                'inputs': {'slo_thresholds': {'five_xx_warn_pct': 0.8, 'five_xx_fail_pct': 2.0}},
            },
            request_metrics={'total_requests': 10, 'avg_latency_ms': 20},
        )
        self.assertEqual(len(cards), 4)
        for card in cards:
            self.assertIn('time_range', card)
            self.assertIn('threshold', card)
            self.assertIn('trend', card)
            self.assertIn('health', card)

    def test_incidents_include_recommended_action(self):
        incidents = build_incidents(
            alerts={'p1_alerts': ['OBS-P1-SCHEDULER-STALLED'], 'p2_alerts': []},
            failed_job_runs_24h=2,
        )
        self.assertGreaterEqual(len(incidents), 2)
        self.assertTrue(all(item.get('recommended_action') for item in incidents))

    def test_queue_health_compact_summary(self):
        health = build_queue_health({'pending': 1, 'running': 0, 'completed': 4, 'failed': 2})
        self.assertEqual(health['health'], 'critical')
        self.assertEqual(health['badge_tone'], 'danger')
        self.assertIn('failed', health['summary'])

    def test_serialize_job_row_supports_retry(self):
        job = BackgroundJob.objects.create(
            organization=self.org,
            job_type='send_contract_reminders',
            status=BackgroundJob.Status.FAILED,
            payload={'trigger': 'scheduler'},
            attempt_count=2,
            max_attempts=3,
            error_message='failed',
        )
        row = serialize_job_row(job)
        self.assertTrue(row['can_retry'])
        self.assertEqual(row['trigger'], 'Scheduler')
        self.assertEqual(row['attempts'], '2/3')
