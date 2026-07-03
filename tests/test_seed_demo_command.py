"""Sub-block D3: the curated demo seed command."""
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from contracts.management.commands.seed_demo import DEMO_EMAIL_DOMAIN, DEMO_ORG_SLUG
from contracts.models import (
    ApprovalRequest,
    Contract,
    Counterparty,
    Deadline,
    Notification,
    Organization,
    OrganizationMembership,
    SignatureRequest,
)

User = get_user_model()


class SeedDemoCommandTests(TestCase):
    def _run(self, *args, **kwargs):
        out = StringIO()
        call_command('seed_demo', *args, stdout=out, **kwargs)
        return out.getvalue()

    def test_refuses_to_run_on_deployed_platform(self):
        with mock.patch('contracts.management.commands.seed_demo.is_running_on_deployed_platform', return_value=True):
            with self.assertRaises(CommandError):
                self._run()
        self.assertFalse(Organization.objects.filter(slug=DEMO_ORG_SLUG).exists())

    def test_creates_one_coherent_demo_organization(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        self.assertEqual(OrganizationMembership.objects.filter(organization=org, is_active=True).count(), 4)

    def test_contract_count_within_specified_range(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        count = Contract.objects.filter(organization=org).count()
        self.assertGreaterEqual(count, 12)
        self.assertLessEqual(count, 20)

    def test_contracts_span_meaningful_lifecycle_states(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        statuses = set(Contract.objects.filter(organization=org).values_list('status', flat=True))
        self.assertTrue({'ACTIVE', 'DRAFT', 'EXPIRED', 'TERMINATED', 'COMPLETED'}.issubset(statuses))

    def test_includes_upcoming_renewals(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        upcoming = Contract.objects.filter(organization=org, auto_renew=True, renewal_date__isnull=False)
        self.assertGreater(upcoming.count(), 0)

    def test_approval_requests_cover_multiple_valid_states(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        statuses = set(ApprovalRequest.objects.filter(organization=org).values_list('status', flat=True))
        self.assertTrue({'PENDING', 'APPROVED', 'REJECTED', 'ESCALATED'}.issubset(statuses))

    def test_signature_activity_created(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        self.assertGreater(SignatureRequest.objects.filter(organization=org).count(), 0)

    def test_deadlines_created_including_overdue_and_completed(self):
        self._run()
        self.assertTrue(Deadline.objects.filter(is_completed=True).exists())
        self.assertTrue(Deadline.objects.filter(is_completed=False).exists())

    def test_counterparties_and_notifications_created(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        self.assertGreaterEqual(Counterparty.objects.filter(organization=org).count(), 5)
        demo_admin = User.objects.get(username='demo_admin')
        self.assertGreater(Notification.objects.filter(recipient=demo_admin).count(), 0)

    def test_no_real_looking_email_domains(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        member_emails = User.objects.filter(
            organization_memberships__organization=org,
        ).values_list('email', flat=True)
        for email in member_emails:
            self.assertTrue(email.endswith(f'@{DEMO_EMAIL_DOMAIN}'), email)
        signer_emails = SignatureRequest.objects.filter(organization=org).values_list('signer_email', flat=True)
        for email in signer_emails:
            self.assertTrue(email.endswith(f'@{DEMO_EMAIL_DOMAIN}'), email)

    def test_rerun_without_reset_is_a_no_op_and_leaves_data_intact(self):
        self._run()
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        count_before = Contract.objects.filter(organization=org).count()

        output = self._run()  # no --reset

        self.assertIn('already exists', output)
        self.assertEqual(Contract.objects.filter(organization=org).count(), count_before)

    def test_reset_recreates_records_without_touching_other_organizations(self):
        self._run()
        other_org = Organization.objects.create(name='Unrelated Firm', slug='unrelated-firm')
        other_user = User.objects.create_user(username='other_user', password='x')
        OrganizationMembership.objects.create(organization=other_org, user=other_user, role='OWNER', is_active=True)
        Contract.objects.create(organization=other_org, title='Unrelated Contract', created_by=other_user)

        self._run('--reset')

        # The unrelated organization and its contract must be completely untouched.
        self.assertTrue(Organization.objects.filter(slug='unrelated-firm').exists())
        self.assertTrue(Contract.objects.filter(organization=other_org, title='Unrelated Contract').exists())
        # The demo org's own data should have been recreated (same deterministic titles).
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        self.assertTrue(Contract.objects.filter(organization=org).exists())

    def test_idempotent_password_and_membership_state_after_two_runs(self):
        self._run()
        self._run('--reset')
        org = Organization.objects.get(slug=DEMO_ORG_SLUG)
        self.assertEqual(User.objects.filter(username='demo_admin').count(), 1)
        self.assertEqual(
            OrganizationMembership.objects.filter(organization=org, user__username='demo_admin').count(), 1,
        )
