"""Deterministic process-role parity report (PAR-ID-001 Slice 3).

Compares legacy UserProfile.role to org-scoped ProcessRoleAssignment.
Non-authoritative — never used for authorization or runtime routing.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand

from contracts.models import Organization, OrganizationMembership, ProcessRoleAssignment, UserProfile
from contracts.services.process_role_assignment import dual_read_process_roles, resolve_legacy_process_role_code
from contracts.services.process_role_shadow_sync import parity_reporting_enabled
from contracts.services.role_definition import ensure_canonical_role_definitions


CRITICAL_DRIFT = frozenset({
    'legacy_without_canonical',
    'cross_organization_anomaly',
    'unexpected_workspace_as_process',
})


def build_parity_rows(*, organization_id=None):
    orgs = Organization.objects.order_by('id')
    if organization_id:
        orgs = orgs.filter(pk=organization_id)

    rows = []
    for org in orgs:
        ensure_canonical_role_definitions(org)
        memberships = (
            OrganizationMembership.objects.filter(organization=org, is_active=True)
            .select_related('user')
            .order_by('user_id')
        )
        for membership in memberships:
            user = membership.user
            profile = UserProfile.objects.filter(user=user).first()
            legacy_value = profile.role if profile else ''
            expected_code, confidence = (
                resolve_legacy_process_role_code('profile_role', legacy_value)
                if legacy_value else ('', 'UNKNOWN')
            )
            report = dual_read_process_roles(organization=org, user=user)
            canonical_codes = sorted({r['code'] for r in report['canonical_assignments']})
            profile_sourced = [
                r for r in report['canonical_assignments']
                if r.get('legacy_source_field') == 'profile_role'
            ]
            profile_codes = sorted({r['code'] for r in profile_sourced})

            drift = []
            if legacy_value and expected_code and expected_code not in canonical_codes:
                drift.append('legacy_without_canonical')
            if legacy_value and expected_code and expected_code not in profile_codes and expected_code in canonical_codes:
                # Present but not from profile_role source — informational
                drift.append('canonical_present_other_source')
            unexpected = [
                c for c in profile_codes
                if c != expected_code and c not in ('legacy_unknown',)
            ]
            if unexpected and legacy_value:
                drift.append('unexpected_canonical_assignment')
            if confidence == 'AMBIGUOUS':
                drift.append('ambiguous_mapping')
            if any(c.startswith('workspace_') for c in profile_codes):
                drift.append('unexpected_workspace_as_process')
            # Inactive mismatch: expected code exists but only inactive
            if legacy_value and expected_code:
                inactive = ProcessRoleAssignment.objects.filter(
                    organization=org, user=user, role_definition__code=expected_code, is_active=False,
                ).exists()
                active = expected_code in canonical_codes
                if inactive and not active:
                    drift.append('inactive_mismatch')

            critical = sorted(set(drift) & CRITICAL_DRIFT)
            rows.append({
                'organization_id': org.pk,
                'organization_slug': org.slug,
                'user_id': user.pk,
                'username': user.username,
                'membership_role': membership.role,
                'legacy_process_role': legacy_value,
                'expected_canonical_code': expected_code,
                'mapping_confidence': confidence,
                'canonical_assignments': canonical_codes,
                'profile_sourced_assignments': profile_codes,
                'drift_classification': sorted(set(drift)),
                'critical_drift': critical,
                'authoritative_for_runtime': False,
            })
    return rows


class Command(BaseCommand):
    help = (
        'Report parity between UserProfile.role and ProcessRoleAssignment. '
        'Non-authoritative diagnostics only.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--organization-id', type=int, default=None)
        parser.add_argument('--json', action='store_true', help='Emit JSON array')
        parser.add_argument(
            '--require-flag',
            action='store_true',
            help='Exit 2 if PROCESS_ROLE_PARITY_REPORTING_ENABLED is false',
        )

    def handle(self, *args, **options):
        if options['require_flag'] and not parity_reporting_enabled():
            self.stderr.write('PROCESS_ROLE_PARITY_REPORTING_ENABLED is false')
            raise SystemExit(2)

        rows = build_parity_rows(organization_id=options['organization_id'])
        critical_count = sum(1 for r in rows if r['critical_drift'])

        if options['json']:
            self.stdout.write(json.dumps({
                'rows': rows,
                'summary': {
                    'organizations_users': len(rows),
                    'critical_drift_rows': critical_count,
                    'authoritative_for_runtime': False,
                },
            }, sort_keys=True, indent=2))
        else:
            for row in rows:
                drift = ','.join(row['drift_classification']) or 'none'
                self.stdout.write(
                    f"org={row['organization_id']} user={row['username']} "
                    f"legacy={row['legacy_process_role'] or '-'} "
                    f"expected={row['expected_canonical_code'] or '-'} "
                    f"canonical={row['canonical_assignments']} drift={drift}"
                )
            self.stdout.write(f'summary: rows={len(rows)} critical_drift={critical_count}')

        if critical_count:
            raise SystemExit(1)
