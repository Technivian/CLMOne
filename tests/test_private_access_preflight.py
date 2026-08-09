"""Read-only preflight evidence for the PDR-0008 accountability gate."""

import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from contracts.models import Contract, Organization, OrganizationMembership


User = get_user_model()


class PrivateAccessPreflightTests(TestCase):
    def test_reports_opaque_remediation_categories_without_writing(self):
        organization = Organization.objects.create(name='Preflight', slug='preflight')
        actor = User.objects.create_user(username='preflight-actor', password='testpass123')
        OrganizationMembership.objects.create(
            organization=organization,
            user=actor,
            role=OrganizationMembership.Role.MEMBER,
            is_active=True,
        )
        safe = Contract.objects.create(
            organization=organization,
            title='Safe',
            owner=actor,
            created_by=actor,
        )
        missing_owner = Contract.objects.create(
            organization=organization,
            title='Needs owner',
            created_by=actor,
        )
        missing_both = Contract.objects.create(organization=organization, title='Needs review')

        output = StringIO()
        call_command('private_access_data_preflight', stdout=output)
        payload = json.loads(output.getvalue())

        self.assertTrue(payload['read_only'])
        self.assertEqual(payload['total_contracts'], 3)
        self.assertEqual(payload['classification_record_ids']['safe_under_new_policy'], [safe.pk])
        self.assertEqual(
            payload['classification_record_ids']['requires_owner_assignment'],
            [missing_owner.pk],
        )
        self.assertEqual(
            payload['classification_record_ids']['requires_explicit_access_review'],
            [missing_both.pk],
        )
        self.assertNotIn('Safe', output.getvalue())
        self.assertNotIn('Needs owner', output.getvalue())
