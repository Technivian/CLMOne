"""Read-only accountability inventory for the PDR-0008 access transition."""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from contracts.models import Contract, Organization, OrganizationMembership


class Command(BaseCommand):
    help = (
        'Report ownership/accountability readiness for private-by-default '
        'contract access. The command never writes data.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--organization-slug',
            help='Limit the read-only inventory to one workspace slug.',
        )

    def handle(self, *args, **options):
        slug = (options.get('organization_slug') or '').strip()
        contracts = Contract.objects.all().select_related('organization', 'owner', 'created_by')
        if slug:
            organization = Organization.objects.filter(slug=slug).first()
            if organization is None:
                raise CommandError(f'No workspace exists for slug {slug!r}.')
            contracts = contracts.filter(organization=organization)

        rows = list(
            contracts.values(
                'id',
                'organization_id',
                'organization__slug',
                'contract_type',
                'owner_id',
                'owner__is_active',
                'created_by_id',
                'created_by__is_active',
            ).order_by('id')
        )
        active_memberships = set(
            OrganizationMembership.objects.filter(
                is_active=True,
                organization__is_active=True,
            ).values_list('organization_id', 'user_id')
        )

        classifications = {
            'safe_under_new_policy': [],
            'requires_owner_assignment': [],
            'requires_created_by_repair': [],
            'requires_explicit_access_review': [],
        }
        by_workspace: dict[str, int] = {}
        by_contract_type: dict[str, int] = {}
        owner_inactive = 0
        creator_inactive = 0
        with_owner = 0
        with_creator = 0
        owner_creator_differ = 0

        for row in rows:
            workspace = row['organization__slug'] or f'unscoped:{row["organization_id"] or "none"}'
            contract_type = row['contract_type'] or 'UNSPECIFIED'
            by_workspace[workspace] = by_workspace.get(workspace, 0) + 1
            by_contract_type[contract_type] = by_contract_type.get(contract_type, 0) + 1

            owner_id = row['owner_id']
            creator_id = row['created_by_id']
            has_active_owner = bool(
                owner_id
                and row['owner__is_active']
                and (row['organization_id'], owner_id) in active_memberships
            )
            has_active_creator = bool(
                creator_id
                and row['created_by__is_active']
                and (row['organization_id'], creator_id) in active_memberships
            )
            if owner_id:
                with_owner += 1
            if creator_id:
                with_creator += 1
            if owner_id and creator_id and owner_id != creator_id:
                owner_creator_differ += 1
            if owner_id and not has_active_owner:
                owner_inactive += 1
            if creator_id and not has_active_creator:
                creator_inactive += 1

            # One exclusive classification per contract makes the remediation
            # queue deterministic. No ownership is inferred or repaired.
            if not row['organization_id'] or (owner_id and not has_active_owner) or (
                creator_id and not has_active_creator
            ) or (not owner_id and not creator_id):
                classifications['requires_explicit_access_review'].append(row['id'])
            elif not owner_id:
                classifications['requires_owner_assignment'].append(row['id'])
            elif not creator_id:
                classifications['requires_created_by_repair'].append(row['id'])
            else:
                classifications['safe_under_new_policy'].append(row['id'])

        payload = {
            'read_only': True,
            'organization_slug': slug or None,
            'total_contracts': len(rows),
            'contracts_with_owner': with_owner,
            'contracts_with_created_by': with_creator,
            'contracts_missing_owner': len(rows) - with_owner,
            'contracts_missing_created_by': len(rows) - with_creator,
            'contracts_owner_creator_differ': owner_creator_differ,
            'contracts_with_inactive_owner_reference': owner_inactive,
            'contracts_with_inactive_created_by_reference': creator_inactive,
            'contracts_by_workspace': by_workspace,
            'contracts_by_contract_type': by_contract_type,
            'classification_record_ids': classifications,
        }
        self.stdout.write(json.dumps(payload, sort_keys=True, indent=2))
