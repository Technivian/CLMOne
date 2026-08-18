"""Tests for redacted, rate-limited operational ERROR email alerts."""
from __future__ import annotations

import logging

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from contracts.operational_alerts import OperationalErrorEmailHandler


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='alerts@clmone.example.com',
)
class OperationalErrorEmailHandlerTests(TestCase):
    def setUp(self):
        cache.clear()

    def _record(self, *, message='synthetic failure', extra=None):
        record = logging.LogRecord(
            name='contracts.services.monitoring',
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg=message,
            args=(),
            exc_info=None,
        )
        record.request_id = 'request-123'
        record.operational_event_id = 'synthetic-error-alert-test'
        record.operational_error_class = 'SyntheticOperationalAlert'
        for key, value in (extra or {}).items():
            setattr(record, key, value)
        return record

    def test_configured_destination_receives_safe_alert(self):
        handler = OperationalErrorEmailHandler(
            recipient='haroon@example.com', environment='production', rate_limit_seconds=900,
        )

        handler.emit(self._record())

        self.assertEqual(len(mail.outbox), 1)
        alert = mail.outbox[0]
        self.assertEqual(alert.to, ['haroon@example.com'])
        self.assertIn('synthetic-error-alert-test', alert.subject)
        self.assertIn('Environment:     production', alert.body)
        self.assertIn('Request ID:      request-123', alert.body)
        self.assertIn('Exception class: SyntheticOperationalAlert', alert.body)

    def test_alert_excludes_message_and_sensitive_request_metadata(self):
        sensitive = (
            'document body=confidential payroll cookie=session-secret '
            'Authorization=Bearer private-token request_body=private-field'
        )
        handler = OperationalErrorEmailHandler(recipient='haroon@example.com')

        handler.emit(self._record(message=sensitive, extra={
            'request_path': '/contracts/secret-document/',
            'request_user_id': '99',
            'request_org_id': '88',
        }))

        body = mail.outbox[0].body
        for forbidden in (
            'confidential payroll', 'session-secret', 'private-token',
            'private-field', '/contracts/secret-document/', 'request_user_id', '99', '88',
        ):
            self.assertNotIn(forbidden, body)

    def test_unconfigured_destination_does_not_send(self):
        handler = OperationalErrorEmailHandler(recipient='')

        handler.emit(self._record())

        self.assertEqual(mail.outbox, [])

    @override_settings(OPERATIONAL_ERROR_ALERTS_ENABLED=False)
    def test_synthetic_command_rejects_disabled_alerting(self):
        with self.assertRaisesMessage(CommandError, 'Operational error alerts are disabled.'):
            call_command('send_operational_error_alert_test')

    @override_settings(
        OPERATIONAL_ERROR_ALERTS_ENABLED=True,
        OPERATOR_ALERT_EMAIL='haroon@example.com',
    )
    def test_synthetic_command_emits_a_data_free_error_event(self):
        command_logger = logging.getLogger('clmone.operational.synthetic_test')
        handler = OperationalErrorEmailHandler(
            recipient='haroon@example.com', environment='production', rate_limit_seconds=900,
        )
        command_logger.addHandler(handler)
        try:
            call_command('send_operational_error_alert_test')
        finally:
            command_logger.removeHandler(handler)

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('synthetic-error-alert-test', mail.outbox[0].body)
        self.assertNotIn('contract', mail.outbox[0].body.lower())

    def test_repeated_event_is_rate_limited(self):
        handler = OperationalErrorEmailHandler(
            recipient='haroon@example.com', rate_limit_seconds=900,
        )

        handler.emit(self._record())
        handler.emit(self._record())

        self.assertEqual(len(mail.outbox), 1)
