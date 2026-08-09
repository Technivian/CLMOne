"""Regression coverage for the approved PAR-SEC-002 read boundary."""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from contracts.models import (
    Client as ContractClient,
    Contract,
    EthicalWall,
    Organization,
    OrganizationMembership,
    SearchTelemetryEvent,
)
from contracts.permissions import ContractAction, can_access_contract_action
from contracts.services.par_sec_002_observation import (
    observation_counters,
    observe_request,
    reset_observation_counters,
)


User = get_user_model()


class ParSec002AuthorizationCharacterizationTests(TestCase):
    """Exercise the canonical private-by-default boundary."""

    def setUp(self):
        self.owner = User.objects.create_user(username='par-sec-owner', password='pass12345')
        self.member = User.objects.create_user(username='par-sec-member', password='pass12345')
        self.outsider = User.objects.create_user(username='par-sec-outsider', password='pass12345')
        self.organization = Organization.objects.create(name='PAR SEC Org', slug='par-sec-org')
        self.other_organization = Organization.objects.create(name='PAR SEC Other', slug='par-sec-other')
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.owner,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.organization,
            user=self.member,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        OrganizationMembership.objects.create(
            organization=self.other_organization,
            user=self.outsider,
            role=OrganizationMembership.Role.OWNER,
            is_active=True,
        )
        self.client_record = ContractClient.objects.create(
            organization=self.organization,
            name='PAR SEC Client',
        )
        self.contract = Contract.objects.create(
            organization=self.organization,
            client=self.client_record,
            title='Visible PAR SEC Contract',
            created_by=self.owner,
        )
        self.other_contract = Contract.objects.create(
            organization=self.other_organization,
            title='Other Organization Contract',
            created_by=self.outsider,
        )
        self.http = Client()

    def test_unauthenticated_search_analytics_and_ai_routes_redirect(self):
        routes = (
            (reverse('contracts:api_contract_search'), 'get'),
            (reverse('contracts:executive_analytics_api'), 'get'),
            (reverse('contracts:contract_ai_assistant', kwargs={'pk': self.contract.pk}), 'post'),
        )
        for url, method in routes:
            response = getattr(self.http, method)(url)
            self.assertEqual(response.status_code, 302, url)

    def test_search_is_tenant_scoped_and_private_by_default(self):
        search_url = reverse('contracts:api_contract_search')
        for user, should_see_contract in ((self.owner, True), (self.member, False)):
            self.http.force_login(user)
            payload = self.http.get(search_url, {'q': 'Contract'}).json()
            ids = {row['id'] for row in payload['results']}
            if should_see_contract:
                self.assertIn(self.contract.id, ids)
            else:
                self.assertNotIn(self.contract.id, ids)
            self.assertNotIn(self.other_contract.id, ids)
            self.http.logout()

    def test_executive_analytics_currently_allows_active_member_reads(self):
        self.http.force_login(self.member)
        response = self.http.get(reverse('contracts:executive_analytics_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['organization']['slug'], self.organization.slug)

    def test_ai_assistant_cross_tenant_lookup_is_denied(self):
        self.http.force_login(self.outsider)
        response = self.http.post(
            reverse('contracts:contract_ai_assistant', kwargs={'pk': self.contract.pk}),
            data=json.dumps({'prompt': 'Summarize the contract'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)

    def test_ethical_wall_fails_closed_for_contract_read_and_ai(self):
        wall = EthicalWall.objects.create(
            organization=self.organization,
            name='Characterization wall',
            client=self.client_record,
            is_active=True,
            created_by=self.owner,
        )
        wall.restricted_users.add(self.member)

        self.assertFalse(can_access_contract_action(self.member, self.contract, ContractAction.VIEW))
        self.assertFalse(can_access_contract_action(self.member, self.contract, ContractAction.AI))

    def test_telemetry_inventory_exposes_same_organization_raw_query_to_member(self):
        SearchTelemetryEvent.objects.create(
            organization=self.organization,
            query='supplier renewal review',
            result_count=1,
            performed_by=self.owner,
            search_type='contract',
        )
        self.http.force_login(self.member)
        response = self.http.get(reverse('contracts:api_search_telemetry'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('supplier renewal review', {row['query'] for row in response.json()['events']})


class ParSec002ObservationTests(TestCase):
    def tearDown(self):
        reset_observation_counters()

    def test_observation_is_strictly_off_by_default(self):
        reset_observation_counters()
        observe_request('search.contract_api', user=None, organization=None)
        self.assertEqual(observation_counters(), {})

    @override_settings(PAR_SEC_002_OBSERVATION_ENABLED=True)
    def test_enabled_observation_only_tracks_content_free_surface_and_actor_class(self):
        reset_observation_counters()
        observe_request('search.contract_api', user=None, organization=None)
        self.assertEqual(
            observation_counters(),
            {('search.contract_api', 'no_workspace'): 1},
        )
