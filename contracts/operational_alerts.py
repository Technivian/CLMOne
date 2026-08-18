"""Safe, rate-limited email alerts for application ERROR/CRITICAL events.

This module deliberately does not send log messages, request paths, request
bodies, headers, cookies, document content, database values, or exception
messages.  Operational email is limited to bounded metadata that helps the
named operator correlate an alert with the provider logs.
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timezone

from django.core.cache import cache
from django.core.mail import send_mail


_SAFE_IDENTIFIER = re.compile(r"[^A-Za-z0-9_.:-]")
_DEFAULT_RATE_LIMIT_SECONDS = 900


def _safe_identifier(value: object, *, fallback: str, limit: int = 120) -> str:
    """Return a bounded identifier without copying arbitrary log content."""
    candidate = str(value or "").strip()
    if not candidate:
        return fallback
    sanitized = _SAFE_IDENTIFIER.sub("_", candidate)[:limit]
    return sanitized or fallback


class OperationalErrorEmailHandler(logging.Handler):
    """Deliver one content-free operational email per event fingerprint/window."""

    def __init__(
        self,
        recipient: str = "",
        environment: str = "development",
        rate_limit_seconds: int = _DEFAULT_RATE_LIMIT_SECONDS,
    ) -> None:
        super().__init__(level=logging.ERROR)
        self.recipient = recipient.strip()
        self.environment = _safe_identifier(environment, fallback="unknown")
        self.rate_limit_seconds = max(1, int(rate_limit_seconds))

    def emit(self, record: logging.LogRecord) -> None:
        if not self.recipient or record.levelno < logging.ERROR:
            return

        logger_name = _safe_identifier(record.name, fallback="unknown.logger")
        event_id = _safe_identifier(
            getattr(record, "operational_event_id", ""),
            fallback="application-error",
        )
        exception_class = self._exception_class(record)
        fingerprint = f"{self.environment}:{logger_name}:{event_id}:{exception_class}:{record.levelname}"
        cache_key = "operational-error-alert:" + hashlib.sha256(
            fingerprint.encode("utf-8")
        ).hexdigest()

        try:
            # Fail closed when the cache cannot provide the rate-limit guard:
            # an alert storm must never become an application failure mode.
            if not cache.add(cache_key, True, timeout=self.rate_limit_seconds):
                return
        except Exception:  # noqa: BLE001 - logging must never affect requests
            return

        request_id = _safe_identifier(
            getattr(record, "request_id", ""), fallback="unavailable"
        )
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        subject = f"[CLM One] {record.levelname} application event: {event_id}"
        body = (
            "CLM One recorded an application ERROR/CRITICAL event.\n\n"
            f"Timestamp:       {timestamp}\n"
            f"Environment:     {self.environment}\n"
            f"Level:           {record.levelname}\n"
            f"Logger:          {logger_name}\n"
            f"Event:           {event_id}\n"
            f"Exception class: {exception_class}\n"
            f"Request ID:      {request_id}\n\n"
            "This notification intentionally excludes log messages, exception "
            "messages, request paths and bodies, document content, credentials, "
            "cookies, authorization headers, and application field values.\n\n"
            f"Duplicate events with this fingerprint are suppressed for {self.rate_limit_seconds} seconds."
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[self.recipient],
                fail_silently=False,
            )
        except Exception:  # noqa: BLE001 - avoid recursive logging from a handler
            return

    @staticmethod
    def _exception_class(record: logging.LogRecord) -> str:
        configured = getattr(record, "operational_error_class", "")
        if configured:
            return _safe_identifier(configured, fallback="UnknownError")
        if record.exc_info and record.exc_info[0]:
            return _safe_identifier(
                getattr(record.exc_info[0], "__name__", ""), fallback="UnknownError"
            )
        return "UnknownError"
