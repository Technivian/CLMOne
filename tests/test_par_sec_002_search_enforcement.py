"""No-leak coverage for the bounded PAR-SEC-002 search enforcement slice."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.test import Client as HttpClient
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    Client,
    Contract,
    Document,
    EthicalWall,
    Matter,
    Organization,
    OrganizationMembership,
)
from contracts.services import object_read_policy
from contracts.services.search_api import ContractSearchAPIService


User = get_user_model()

ENFORCEMENT = {
    'DJANGO_ENV': 'test',
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST': 'secure-search-org',
}


class ParSec002SearchFixtureMixin:
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Secure Search Org',
            slug='secure-search-org',
        )
        self.owner = User.objects.create_user(username='search-owner')
        self.member = User.objects.create_user(username='search-member')
        for user, role in (
            (self.owner, OrganizationMembership.Role.OWNER),
            (self.member, OrganizationMembership.Role.MEMBER),
        ):
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=user,
                role=role,
                is_active=True,
            )
        self.client_record = Client.objects.create(
            organization=self.organization,
            name='Protected Client',
        )
        self.matter = Matter.objects.create(
            organization=self.organization,
            client=self.client_record,
            matter_number='SEC-001',
            title='Protected Matter',
        )
        # The ordinary member owns these records so Ethical-Wall coverage can
        # exercise its additive denial independently of private ownership.
        self.direct_client_contract = Contract.objects.create(
            organization=self.organization,
            client=self.client_record,
            title='Direct client secret',
            status=Contract.Status.ACTIVE,
            contract_type=Contract.ContractType.MSA,
            jurisdiction='NL',
            created_by=self.member,
        )
        self.matter_contract = Contract.objects.create(
            organization=self.organization,
            matter=self.matter,
            title='Matter secret',
            status=Contract.Status.ACTIVE,
            contract_type=Contract.ContractType.SOW,
            jurisdiction='NL',
            created_by=self.member,
        )
        self.public_contract = Contract.objects.create(
            organization=self.organization,
            title='Ordinary agreement',
            status=Contract.Status.IN_PROGRESS,
            contract_type=Contract.ContractType.NDA,
            jurisdiction='BE',
            created_by=self.member,
        )
        self.service = ContractSearchAPIService()

    def add_wall(self, *, client=None, matter=None, restricted_user=None, **kwargs):
        wall = EthicalWall.objects.create(
            organization=self.organization,
            name=kwargs.pop('name', 'Search restriction'),
            client=client,
            matter=matter,
            created_by=self.owner,
            **kwargs,
        )
        if restricted_user:
            wall.restricted_users.add(restricted_user)
        return wall


class ParSec002SearchEnforcementTests(ParSec002SearchFixtureMixin, TestCase):
    def test_private_policy_is_not_bypassed_when_legacy_flag_is_off(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)

        result = self.service.search_contracts(self.organization, user=self.member)
        facets = self.service.get_contract_facets(self.organization, user=self.member)

        self.assertEqual(result.total, 1)
        self.assertEqual({row['id'] for row in result.results}, {self.public_contract.pk})
        self.assertEqual(
            sum(row['count'] for row in facets['statuses']),
            1,
        )

    @override_settings(**ENFORCEMENT)
    def test_client_wall_filters_direct_and_inherited_matter_client_before_counts(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)

        with self.assertLogs(
            'contracts.services.object_read_policy',
            level='INFO',
        ) as logs:
            result = self.service.search_contracts(
                self.organization,
                user=self.member,
            )
        facets = self.service.get_contract_facets(self.organization, user=self.member)
        owner_result = self.service.search_contracts(self.organization, user=self.owner)

        self.assertEqual(result.total, 1)
        self.assertEqual(result.results[0]['id'], self.public_contract.pk)
        self.assertEqual(sum(row['count'] for row in facets['statuses']), 1)
        self.assertEqual(owner_result.total, 0)
        self.assertIn('outcome=deny', logs.output[0])
        self.assertNotIn(self.direct_client_contract.title, logs.output[0])
        self.assertNotIn(str(self.direct_client_contract.pk), logs.output[0])

    @override_settings(**ENFORCEMENT)
    def test_policy_query_cost_is_bounded_by_wall_count(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)
        with CaptureQueriesContext(connection) as queries:
            result = self.service.search_contracts(
                self.organization,
                user=self.member,
            )
        self.assertEqual(result.total, 1)
        # Bound is 6, not 5: the private-by-default ownership boundary
        # (docs/pilots/payrollminds/PILOT_PRODUCT_PATH_IMPLEMENTATION.md)
        # adds exactly one additional, necessary membership-role query via
        # _is_workspace_privileged(). The assertion still proves the cost is
        # bounded (independent of wall count), not that it never changes.
        self.assertLessEqual(len(queries), 6)

    @override_settings(**ENFORCEMENT)
    def test_matter_wall_expiry_and_multiple_walls_are_additive(self):
        expired = self.add_wall(
            matter=self.matter,
            restricted_user=self.member,
            expires_at=timezone.now() - timezone.timedelta(seconds=1),
        )
        self.assertEqual(
            self.service.search_contracts(self.organization, user=self.member).total,
            3,
        )
        expired.expires_at = None
        expired.save(update_fields=['expires_at'])
        self.add_wall(
            client=self.client_record,
            restricted_user=self.member,
            name='Second restriction',
        )

        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 1)
        self.assertEqual(result.results[0]['title'], self.public_contract.title)

    @override_settings(**ENFORCEMENT)
    def test_malformed_wall_inactive_membership_and_policy_failure_fail_closed(self):
        self.add_wall(restricted_user=self.member)
        malformed = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(malformed.total, 0)
        self.assertEqual(malformed.results, [])
        self.assertEqual(
            sum(
                row['count']
                for values in self.service.get_contract_facets(
                    self.organization,
                    user=self.member,
                ).values()
                for row in values
            ),
            0,
        )

        EthicalWall.objects.all().delete()
        membership = OrganizationMembership.objects.get(
            organization=self.organization,
            user=self.member,
        )
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        self.assertEqual(
            self.service.search_contracts(self.organization, user=self.member).total,
            0,
        )

        membership.is_active = True
        membership.save(update_fields=['is_active'])
        with self.assertLogs('contracts.services.search_api', level='ERROR') as logs:
            with patch(
                'contracts.services.object_read_policy.filter_contract_queryset',
                side_effect=RuntimeError('protected synthetic detail'),
            ):
                unavailable = self.service.search_contracts(
                    self.organization,
                    user=self.member,
                )
        self.assertEqual(unavailable.total, 0)
        self.assertEqual(unavailable.results, [])
        self.assertIn('outcome=policy_error', logs.output[0])
        self.assertNotIn('protected synthetic detail', logs.output[0])

    @override_settings(**ENFORCEMENT)
    def test_tenant_mismatched_relations_are_never_serialized(self):
        other = Organization.objects.create(name='Other Org', slug='other-org')
        other_client = Client.objects.create(organization=other, name='Other Client')
        mismatched = Contract.objects.create(
            organization=self.organization,
            client=other_client,
            title='Mismatched relation secret',
            created_by=self.owner,
        )

        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertNotIn(mismatched.pk, {row['id'] for row in result.results})
        self.assertNotIn(mismatched.title, {row['title'] for row in result.results})

    @override_settings(
        **{
            **ENFORCEMENT,
            'DJANGO_ENV': 'production',
        }
    )
    def test_production_configuration_keeps_private_policy(self):
        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 3)

    @override_settings(
        **{
            **ENFORCEMENT,
            'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED': False,
            'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED': True,
        }
    )
    def test_abort_switch_cannot_restore_unfiltered_results(self):
        result = self.service.search_contracts(
            self.organization,
            user=self.member,
        )
        facets = self.service.get_contract_facets(
            self.organization,
            user=self.member,
        )

        self.assertEqual(result.total, 3)
        self.assertEqual(sum(row['count'] for row in facets['statuses']), 3)

    @override_settings(
        **{
            **ENFORCEMENT,
            'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST': 'another-org',
        }
    )
    def test_workspace_outside_allowlist_keeps_private_policy(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)
        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 1)

    @override_settings(**ENFORCEMENT)
    def test_http_search_and_facets_receive_requester_policy(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)
        http = HttpClient()
        http.force_login(self.member)

        search = http.get(reverse('contracts:api_contract_search'))
        facets = http.get(reverse('contracts:api_search_facets'))

        self.assertEqual(search.status_code, 200)
        self.assertEqual(search.json()['total'], 1)
        self.assertEqual(
            {row['id'] for row in search.json()['results']},
            {self.public_contract.pk},
        )
        self.assertEqual(
            sum(row['count'] for row in facets.json()['statuses']),
            1,
        )

    # --- Additional PAR-SEC-002 invariant coverage (Prompt 31 Phase 6) ---

    @override_settings(**ENFORCEMENT)
    def test_authorized_owner_finds_accessible_contract_by_query(self):
        """Ordinary eligible access: an owned, unrestricted record is discoverable."""
        result = self.service.search_contracts(
            self.organization,
            q='Ordinary agreement',
            user=self.member,
        )
        self.assertEqual(result.total, 1)
        self.assertEqual(result.results[0]['id'], self.public_contract.pk)

    @override_settings(**ENFORCEMENT)
    def test_private_record_hidden_from_unrelated_member_without_wall(self):
        """Private object: no Ethical Wall is needed to keep an unowned record private."""
        unrelated = User.objects.create_user(username='search-unrelated')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=unrelated,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        result = self.service.search_contracts(self.organization, user=unrelated)
        self.assertEqual(result.total, 0)
        self.assertEqual(result.results, [])

    @override_settings(**ENFORCEMENT)
    def test_cross_workspace_search_never_discovers_other_org_records(self):
        """Cross-workspace: a workspace-B member cannot discover workspace-A records."""
        other_org = Organization.objects.create(name='Other Workspace', slug='other-workspace')
        other_user = User.objects.create_user(username='other-workspace-member')
        OrganizationMembership.objects.create(
            organization=other_org,
            user=other_user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        result = self.service.search_contracts(other_org, user=other_user)
        self.assertEqual(result.total, 0)
        self.assertNotIn(
            self.public_contract.pk,
            {row['id'] for row in result.results},
        )

    @override_settings(**ENFORCEMENT)
    def test_wall_removal_restores_visibility(self):
        """Revocation/restoration: removing the restricted-user grant un-hides the record."""
        wall = self.add_wall(client=self.client_record, restricted_user=self.member)
        self.assertEqual(
            self.service.search_contracts(self.organization, user=self.member).total,
            1,
        )
        wall.restricted_users.remove(self.member)
        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 3)
        self.assertEqual(
            sum(row['count'] for row in self.service.get_contract_facets(
                self.organization, user=self.member,
            )['statuses']),
            3,
        )

    @override_settings(**ENFORCEMENT)
    def test_restricted_title_never_matched_by_query(self):
        """Suggestions/query matching: a walled title is not discoverable by exact query."""
        self.add_wall(client=self.client_record, restricted_user=self.member)
        result = self.service.search_contracts(
            self.organization,
            q='Direct client secret',
            user=self.member,
        )
        self.assertEqual(result.total, 0)
        self.assertEqual(result.results, [])

    @override_settings(**ENFORCEMENT)
    def test_empty_query_totals_exclude_restricted_records(self):
        """Empty/broad search: an unqualified query still respects the object policy."""
        self.add_wall(client=self.client_record, restricted_user=self.member)
        result = self.service.search_contracts(self.organization, q='', user=self.member)
        facets = self.service.get_contract_facets(self.organization, user=self.member)
        self.assertEqual(result.total, 1)
        self.assertEqual(
            sum(row['count'] for row in facets['statuses']),
            1,
        )

    @override_settings(**ENFORCEMENT)
    def test_document_search_inherits_contract_wall_boundary(self):
        """Documents: document eligibility inherits the parent contract's wall/ownership boundary."""
        self.add_wall(client=self.client_record, restricted_user=self.member)
        restricted_document = Document.objects.create(
            organization=self.organization,
            title='Direct client secret exhibit',
            contract=self.direct_client_contract,
            client=self.client_record,
            uploaded_by=self.member,
        )
        eligible_document = Document.objects.create(
            organization=self.organization,
            title='Ordinary agreement exhibit',
            contract=self.public_contract,
            uploaded_by=self.member,
        )
        eligible_ids = set(
            object_read_policy.filter_document_queryset(
                Document.objects.filter(organization=self.organization),
                organization=self.organization,
                user=self.member,
            ).values_list('pk', flat=True)
        )
        self.assertNotIn(restricted_document.pk, eligible_ids)
        self.assertIn(eligible_document.pk, eligible_ids)
