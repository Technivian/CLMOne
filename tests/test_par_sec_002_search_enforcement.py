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
    EthicalWall,
    Matter,
    Organization,
    OrganizationMembership,
)
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
        self.direct_client_contract = Contract.objects.create(
            organization=self.organization,
            client=self.client_record,
            title='Direct client secret',
            status=Contract.Status.ACTIVE,
            contract_type=Contract.ContractType.MSA,
            jurisdiction='NL',
            created_by=self.owner,
        )
        self.matter_contract = Contract.objects.create(
            organization=self.organization,
            matter=self.matter,
            title='Matter secret',
            status=Contract.Status.ACTIVE,
            contract_type=Contract.ContractType.SOW,
            jurisdiction='NL',
            created_by=self.owner,
        )
        self.public_contract = Contract.objects.create(
            organization=self.organization,
            title='Ordinary agreement',
            status=Contract.Status.IN_PROGRESS,
            contract_type=Contract.ContractType.NDA,
            jurisdiction='BE',
            created_by=self.owner,
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
    def test_flag_off_preserves_legacy_results_and_facets(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)

        result = self.service.search_contracts(self.organization, user=self.member)
        facets = self.service.get_contract_facets(self.organization, user=self.member)

        self.assertEqual(result.total, 3)
        self.assertEqual({row['id'] for row in result.results}, {
            self.direct_client_contract.pk,
            self.matter_contract.pk,
            self.public_contract.pk,
        })
        self.assertEqual(
            sum(row['count'] for row in facets['statuses']),
            3,
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
        self.assertEqual(owner_result.total, 3)
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
        self.assertLessEqual(len(queries), 5)

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
    def test_allowlisted_workspace_still_fails_closed_in_production(self):
        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 0)

    @override_settings(
        **{
            **ENFORCEMENT,
            'PAR_SEC_002_SEARCH_ENFORCEMENT_ENABLED': False,
            'PAR_SEC_002_SEARCH_ABORT_FAIL_CLOSED': True,
        }
    )
    def test_abort_switch_fails_closed_instead_of_restoring_legacy_results(self):
        with self.assertLogs(
            'contracts.services.search_api',
            level='WARNING',
        ) as logs:
            result = self.service.search_contracts(
                self.organization,
                user=self.member,
            )
        facets = self.service.get_contract_facets(
            self.organization,
            user=self.member,
        )

        self.assertEqual(result.total, 0)
        self.assertEqual(result.results, [])
        self.assertTrue(all(not values for values in facets.values()))
        self.assertIn('outcome=rollback_fail_closed', logs.output[0])

    @override_settings(
        **{
            **ENFORCEMENT,
            'PAR_SEC_002_SEARCH_ENFORCEMENT_ORG_ALLOWLIST': 'another-org',
        }
    )
    def test_workspace_outside_explicit_allowlist_keeps_legacy_path(self):
        self.add_wall(client=self.client_record, restricted_user=self.member)
        result = self.service.search_contracts(self.organization, user=self.member)
        self.assertEqual(result.total, 3)

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
