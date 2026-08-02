"""Content-free quarantine retention and reconciliation evidence."""

from __future__ import annotations

import json
from datetime import timedelta

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from contracts.models import DocumentIngestionAttempt, Organization
from contracts.services.document_ingestion import (
    DocumentReleaseDenied,
    get_document_ingestion_service,
)


class Command(BaseCommand):
    help = 'Dry-run or explicitly execute tenant-scoped quarantine retention.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', required=True)
        parser.add_argument('--execute', action='store_true', default=False)
        parser.add_argument('--limit', type=int, default=500)

    def handle(self, *args, **options):
        try:
            organization = Organization.objects.get(slug=options['organization_slug'])
        except Organization.DoesNotExist as exc:
            raise CommandError('Workspace not found.') from exc
        execute = bool(options['execute'])
        limit = max(1, int(options['limit']))
        retention_days = int(getattr(settings, 'DOCUMENT_QUARANTINE_RETENTION_DAYS', 0) or 0)
        cutoff = timezone.now() - timedelta(days=retention_days) if retention_days > 0 else None
        queryset = DocumentIngestionAttempt.objects.filter(
            organization=organization,
        ).exclude(
            status__in=[
                DocumentIngestionAttempt.Status.RELEASED,
                DocumentIngestionAttempt.Status.EXPIRED,
            ],
        ).order_by('received_at')
        if cutoff is not None:
            queryset = queryset.filter(received_at__lte=cutoff)
        else:
            queryset = queryset.none()

        service = get_document_ingestion_service()
        storage = storages[service.storage_alias]
        summary = {
            'captured_at': timezone.now().isoformat(),
            'organization_id': organization.pk,
            'execute': execute,
            'retention_configured': retention_days > 0,
            'purge_enabled': bool(getattr(settings, 'DOCUMENT_QUARANTINE_PURGE_ENABLED', False)),
            'candidates': 0,
            'held': 0,
            'missing_quarantine_objects': 0,
            'expired': 0,
            'blocked': 0,
        }
        for attempt in queryset.select_related('contract')[:limit]:
            summary['candidates'] += 1
            if attempt.quarantine_object_key and not storage.exists(attempt.quarantine_object_key):
                summary['missing_quarantine_objects'] += 1
            if service.is_held(attempt):
                summary['held'] += 1
                continue
            if not execute:
                continue
            try:
                service.expire(attempt=attempt, system=True)
            except DocumentReleaseDenied:
                summary['blocked'] += 1
            else:
                summary['expired'] += 1
        self.stdout.write(json.dumps(summary, indent=2, sort_keys=True))
