"""Emit one harmless, data-free ERROR event for provider delivery verification."""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


logger = logging.getLogger("clmone.operational.synthetic_test")


class Command(BaseCommand):
    help = "Emit a harmless synthetic ERROR event to verify operational email alert delivery."

    def handle(self, *args, **options):
        if not settings.OPERATIONAL_ERROR_ALERTS_ENABLED:
            raise CommandError("Operational error alerts are disabled.")
        if not settings.OPERATOR_ALERT_EMAIL:
            raise CommandError("OPERATOR_ALERT_EMAIL is not configured.")

        logger.error(
            "synthetic operational alert test",
            extra={
                "operational_event_id": "synthetic-error-alert-test",
                "operational_error_class": "SyntheticOperationalAlert",
            },
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic operational ERROR emitted; verify delivery at the configured operator destination."
            )
        )
