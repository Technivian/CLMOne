"""Secret-free boolean preflight for quarantine-first ingestion."""

from __future__ import annotations

import json

from django.conf import settings
from django.core.files.storage import storages
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string

from contracts.models import Organization
from contracts.services.document_ingestion import IngestionState, document_ingestion_state


class Command(BaseCommand):
    help = 'Report content-free readiness booleans for one document-ingestion workspace.'

    def add_arguments(self, parser):
        parser.add_argument('--organization-slug', required=True)

    def handle(self, *args, **options):
        organization = Organization.objects.filter(slug=options['organization_slug']).first()
        scanner_path = str(getattr(settings, 'DOCUMENT_MALWARE_SCANNER_CLASS', '') or '').strip()
        scanner_loadable = False
        if scanner_path:
            try:
                import_string(scanner_path)
            except Exception:
                pass
            else:
                scanner_loadable = True
        storage_configured = False
        try:
            storages['quarantine']
        except Exception:
            pass
        else:
            storage_configured = True
        payload = {
            'workspace_found': organization is not None,
            'workspace_active': bool(organization and organization.is_active),
            'enforcement_active_for_workspace': bool(
                organization and document_ingestion_state(organization) is IngestionState.ENFORCE
            ),
            'abort_fail_closed': bool(
                getattr(settings, 'DOCUMENT_QUARANTINE_ABORT_FAIL_CLOSED', False)
            ),
            'scanner_configured': bool(scanner_path),
            'scanner_loadable': scanner_loadable,
            'quarantine_storage_configured': storage_configured,
            'retention_configured': int(
                getattr(settings, 'DOCUMENT_QUARANTINE_RETENTION_DAYS', 0) or 0
            ) > 0,
            'release_enabled': bool(
                getattr(settings, 'DOCUMENT_QUARANTINE_RELEASE_ENABLED', False)
            ),
            'purge_enabled': bool(
                getattr(settings, 'DOCUMENT_QUARANTINE_PURGE_ENABLED', False)
            ),
        }
        payload['ready_for_bounded_observation'] = all([
            payload['workspace_active'],
            payload['enforcement_active_for_workspace'],
            not payload['abort_fail_closed'],
            payload['scanner_configured'],
            payload['scanner_loadable'],
            payload['quarantine_storage_configured'],
            payload['retention_configured'],
        ])
        self.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
