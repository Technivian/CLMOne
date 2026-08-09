"""No-leak coverage for the bounded PAR-SEC-002 repository enforcement slice."""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    Client,
    Contract,
    EthicalWall,
    Matter,
    Organization,
    OrganizationMembership,
)


User = get_user_model()

REPOSITORY_ENFORCEMENT = {
    'DJANGO_ENV': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': True,
    'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': False,
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENVIRONMENTS': 'test',
    'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': 'secure-repository-org',
}


class ParSec002RepositoryEnforcementTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name='Secure Repository Org',
            slug='secure-repository-org',
        )
        self.owner = User.objects.create_user(
            username='repository-owner',
            password='testpass123',
        )
        self.member = User.objects.create_user(
            username='repository-member',
            password='testpass123',
        )
        for user, role in (
            (self.owner, OrganizationMembership.Role.OWNER),
            (self.member, OrganizationMembership.Role.ADMIN),
        ):
            OrganizationMembership.objects.create(
                organization=self.organization,
                user=user,
                role=role,
                is_active=True,
            )

        self.protected_client = Client.objects.create(
            organization=self.organization,
            name='Protected Client',
        )
        self.protected_matter = Matter.objects.create(
            organization=self.organization,
            client=self.protected_client,
            matter_number='REP-001',
            title='Protected Matter',
        )
        self.direct_contract = Contract.objects.create(
            organization=self.organization,
            client=self.protected_client,
            title='Direct repository secret',
            counterparty='Restricted Counterparty',
            lifecycle_stage=Contract.LifecycleStage.DRAFTING,
            created_by=self.owner,
        )
        self.inherited_contract = Contract.objects.create(
            organization=self.organization,
            matter=self.protected_matter,
            title='Inherited repository secret',
            counterparty='Restricted Counterparty',
            lifecycle_stage=Contract.LifecycleStage.DRAFTING,
            created_by=self.owner,
        )
        self.eligible_contract = Contract.objects.create(
            organization=self.organization,
            title='Ordinary repository agreement',
            counterparty='Visible Counterparty',
            lifecycle_stage=Contract.LifecycleStage.DRAFTING,
            created_by=self.member,
        )
        other_org = Organization.objects.create(name='Other Org', slug='other-repository-org')
        other_user = User.objects.create_user(username='other-repository-owner')
        OrganizationMembership.objects.create(
            organization=other_org,
            user=other_user,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.other_contract = Contract.objects.create(
            organization=other_org,
            title='Cross workspace secret',
            counterparty='Other Counterparty',
            created_by=other_user,
        )
        self.wall = EthicalWall.objects.create(
            organization=self.organization,
            name='Repository restriction',
            client=self.protected_client,
            created_by=self.owner,
        )
        self.wall.restricted_users.add(self.member)
        self.client.force_login(self.member)

    def _repository_api(self):
        return self.client.get(reverse('contracts:contracts_api'))

    def test_private_policy_is_not_bypassed_when_legacy_flag_is_off(self):
        response = self._repository_api()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['total_count'], 1)
        self.assertNotIn(
            self.other_contract.title,
            {row['title'] for row in response.json()['contracts']},
        )

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_rows_counts_and_filter_metadata_share_the_same_policy_boundary(self):
        page = self.client.get(reverse('contracts:repository'))
        api = self._repository_api()

        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context['total_contracts'], 1)
        self.assertEqual(
            list(page.context['repository_counterparties']),
            ['Visible Counterparty'],
        )
        self.assertEqual(api.json()['total_count'], 1)
        self.assertEqual(
            [row['title'] for row in api.json()['contracts']],
            [self.eligible_contract.title],
        )
        payload = page.content.decode() + json.dumps(api.json())
        self.assertNotIn(self.direct_contract.title, payload)
        self.assertNotIn(self.inherited_contract.title, payload)
        self.assertNotIn('Restricted Counterparty', payload)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_detail_and_edit_use_generic_not_found_for_denied_objects(self):
        for route_name in ('contract_detail', 'contract_update'):
            denied = self.client.get(
                reverse(f'contracts:{route_name}', args=[self.direct_contract.pk])
            )
            allowed = self.client.get(
                reverse(f'contracts:{route_name}', args=[self.eligible_contract.pk])
            )
            self.assertEqual(denied.status_code, 404)
            self.assertEqual(allowed.status_code, 200)
            self.assertNotIn(self.direct_contract.title, denied.content.decode())

        denied_api = self.client.get(
            reverse(
                'contracts:contract_detail_api',
                args=[self.direct_contract.pk],
            )
        )
        self.assertEqual(denied_api.status_code, 404)
        self.assertNotIn(self.direct_contract.title, denied_api.content.decode())

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_bulk_action_mutates_only_eligible_contracts(self):
        response = self.client.post(
            reverse('contracts:contracts_bulk_update_api'),
            data=json.dumps({
                'contract_ids': [
                    str(self.direct_contract.pk),
                    str(self.eligible_contract.pk),
                ],
                'updates': {
                    'lifecycle_stage': Contract.LifecycleStage.INTERNAL_REVIEW,
                },
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['updated_count'], 1)
        self.direct_contract.refresh_from_db()
        self.eligible_contract.refresh_from_db()
        self.assertEqual(
            self.direct_contract.lifecycle_stage,
            Contract.LifecycleStage.DRAFTING,
        )
        self.assertEqual(
            self.eligible_contract.lifecycle_stage,
            Contract.LifecycleStage.INTERNAL_REVIEW,
        )

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_malformed_policy_and_inactive_membership_fail_closed(self):
        self.wall.client = None
        self.wall.save(update_fields=['client'])

        malformed_page = self.client.get(reverse('contracts:repository'))
        malformed_api = self._repository_api()
        self.assertEqual(malformed_page.status_code, 200)
        self.assertEqual(malformed_page.context['total_contracts'], 0)
        self.assertEqual(malformed_api.json()['total_count'], 0)
        self.assertEqual(malformed_api.json()['contracts'], [])
        self.assertEqual(
            self.client.get(
                reverse('contracts:contract_detail', args=[self.eligible_contract.pk])
            ).status_code,
            404,
        )

        self.wall.delete()
        membership = OrganizationMembership.objects.get(
            organization=self.organization,
            user=self.member,
        )
        membership.is_active = False
        membership.save(update_fields=['is_active'])
        self.assertEqual(self._repository_api().json()['total_count'], 0)

    @override_settings(
        **{
            **REPOSITORY_ENFORCEMENT,
            'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ENABLED': False,
            'PAR_SEC_002_REPOSITORY_ABORT_FAIL_CLOSED': True,
        }
    )
    def test_abort_switch_cannot_restore_an_unfiltered_repository(self):
        response = self._repository_api()

        self.assertEqual(response.json()['total_count'], 1)
        self.assertEqual([row['title'] for row in response.json()['contracts']], [self.eligible_contract.title])

    @override_settings(
        **{
            **REPOSITORY_ENFORCEMENT,
            'PAR_SEC_002_REPOSITORY_ENFORCEMENT_ORG_ALLOWLIST': 'another-org',
        }
    )
    def test_workspace_outside_allowlist_keeps_private_policy(self):
        self.assertEqual(self._repository_api().json()['total_count'], 1)

    @override_settings(**REPOSITORY_ENFORCEMENT)
    def test_policy_error_is_content_free_and_fails_closed(self):
        protected_detail = 'synthetic policy detail that must not be logged'
        with self.assertLogs('contracts.services.repository', level='ERROR') as logs:
            with patch(
                'contracts.services.repository.filter_contract_queryset',
                side_effect=RuntimeError(protected_detail),
            ):
                response = self._repository_api()

        self.assertEqual(response.json()['total_count'], 0)
        self.assertNotIn(protected_detail, ''.join(logs.output))

    @override_settings(
        **{
            **REPOSITORY_ENFORCEMENT,
            'DJANGO_ENV': 'production',
        }
    )
    def test_production_configuration_keeps_private_policy(self):
        self.assertEqual(self._repository_api().json()['total_count'], 1)
