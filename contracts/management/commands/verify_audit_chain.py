"""Verify the integrity of the per-organization audit hash chain.

Read-only. Exits non-zero if any chain fails verification, so it can gate CI or
an operator check.

    python manage.py verify_audit_chain                 # all org chains
    python manage.py verify_audit_chain --organization demo-muni
    python manage.py verify_audit_chain --since 2026-06-01 --until 2026-06-22

Output reports seq / event_type / reason for the first broken entry only — never
sensitive `changes` content.
"""
from __future__ import annotations

import json
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from contracts.models import AuditLog, Organization
from contracts.services.audit import (
    VERDICT_EMPTY,
    VERDICT_VALID,
    organization_ids_with_chains,
    verify_chain,
)


def _parse_date(value, label):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise CommandError(f'Invalid {label} date: {value!r} (use ISO format, e.g. 2026-06-01)')
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    return dt


class Command(BaseCommand):
    help = 'Verify the tamper-evident audit hash chain for one or all organizations.'

    def add_arguments(self, parser):
        parser.add_argument('--organization', default='', help='Organization slug (default: all chains).')
        parser.add_argument('--since', default='', help='ISO date/datetime lower bound (inclusive).')
        parser.add_argument('--until', default='', help='ISO date/datetime upper bound (exclusive).')
        parser.add_argument('--json', action='store_true', help='Emit machine-readable JSON.')

    def handle(self, *args, **options):
        since = _parse_date(options['since'], 'since')
        until = _parse_date(options['until'], 'until')
        slug = (options['organization'] or '').strip()

        if slug:
            org = Organization.objects.filter(slug=slug).first()
            if not org:
                raise CommandError(f'Organization with slug {slug!r} not found.')
            org_ids = [org.id]
        else:
            org_ids = organization_ids_with_chains()

        results = []
        failed = False
        for org_id in org_ids:
            res = verify_chain(org_id, since=since, until=until)
            results.append(res)
            if res['status'] not in (VERDICT_VALID, VERDICT_EMPTY):
                failed = True

        if options['json']:
            self.stdout.write(json.dumps({'failed': failed, 'results': results}, default=str, indent=2))
        else:
            for res in results:
                scope = res['organization_id'] if res['organization_id'] is not None else 'system(global)'
                if res['status'] in (VERDICT_VALID, VERDICT_EMPTY):
                    self.stdout.write(self.style.SUCCESS(
                        f'[OK] org={scope} status={res["status"]} checked={res["checked"]}'
                    ))
                else:
                    fb = res.get('first_broken', {})
                    self.stdout.write(self.style.ERROR(
                        f'[FAIL] org={scope} status={res["status"]} checked={res["checked"]} '
                        f'first_broken_seq={fb.get("seq")} event={fb.get("event_type")}'
                    ))

        if failed:
            raise CommandError('Audit chain verification FAILED for one or more organizations.')
        self.stdout.write(self.style.SUCCESS(f'Audit chain verification passed for {len(results)} chain(s).'))
