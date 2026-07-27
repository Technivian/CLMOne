"""Regression coverage for the synthetic PayrollMinds presenter route."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from contracts.models import (
    ApprovalRequest,
    Contract,
    Deadline,
    DPAReviewPack,
    Organization,
    OrgPolicy,
    SignatureRequest,
)
from contracts.services.payrollminds_demo import is_payrollminds_presenter_workspace


User = get_user_model()


class PayrollmindsPresenterReadOnlyTests(TestCase):
    def setUp(self):
        call_command('seed_payrollminds_demo', reset=True, verbosity=0)
        self.organization = Organization.objects.get(slug='payrollminds-demo')
        self.sow = Contract.objects.get(
            organization=self.organization,
            title__startswith='Global Payroll Transformation Engagement',
        )
        self.finance_approval = ApprovalRequest.objects.filter(
            organization=self.organization,
            approval_step__icontains='Finance',
            status=ApprovalRequest.Status.PENDING,
        ).first()
        self.dpa_review = DPAReviewPack.objects.get(organization=self.organization)
        self.signature_request = SignatureRequest.objects.get(
            organization=self.organization,
            contract=self.sow,
        )
        self.deadline = Deadline.objects.for_organization(self.organization).filter(
            is_completed=False,
        ).first()

    def _client_for(self, username):
        client = Client()
        client.force_login(User.objects.get(username=username))
        return client

    def test_presenter_guard_requires_the_seeded_workspace_and_disabled_ai_policy(self):
        self.assertTrue(is_payrollminds_presenter_workspace(self.organization))
        other_organization = Organization.objects.create(name='Other workspace', slug='other-workspace')
        OrgPolicy.objects.create(organization=other_organization, ai_features_enabled=False)
        self.assertFalse(is_payrollminds_presenter_workspace(other_organization))
        OrgPolicy.objects.filter(organization=self.organization).update(ai_features_enabled=True)
        self.assertFalse(is_payrollminds_presenter_workspace(self.organization))

    def test_dashboard_hides_the_global_audit_signal(self):
        response = self._client_for('payrollminds_admin').get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Audit infrastructure')
        self.assertNotContains(response, reverse('contracts:audit_log_list'))

    def test_contract_overview_hides_live_approval_decision(self):
        response = self._client_for('payrollminds_admin').get(
            reverse('contracts:contract_detail', kwargs={'pk': self.sow.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Record review decision')

    def test_contract_activity_keeps_scope_and_hides_global_audit_actions(self):
        response = self._client_for('payrollminds_admin').get(
            f"{reverse('contracts:contract_detail', kwargs={'pk': self.sow.pk})}?tab=activity",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Audit trail')
        self.assertNotContains(response, 'Full audit log')
        self.assertNotContains(response, 'Add note')

    def test_approval_controls_and_every_decision_endpoint_are_read_only(self):
        client = self._client_for('payrollminds_finance')
        list_response = client.get(reverse('contracts:approval_request_list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertNotContains(list_response, 'data-approval-action="approve"')
        self.assertNotContains(list_response, 'data-approval-action="reject"')
        self.assertNotContains(list_response, 'data-approval-action="return"')

        for name in (
            'approval_approve_api',
            'approval_reject_api',
            'approval_request_changes_api',
        ):
            response = client.post(
                reverse(f'contracts:{name}', kwargs={'approval_id': self.finance_approval.pk}),
                '{}',
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 403)
            self.assertFalse(response.json()['ok'] if 'ok' in response.json() else False)

        response = client.post(
            reverse('contracts:contract_approval_decision', kwargs={
                'pk': self.sow.pk,
                'approval_id': self.finance_approval.pk,
                'decision': 'approve',
            }),
        )
        self.assertEqual(response.status_code, 403)

    def test_privacy_decision_is_hidden_and_server_side_blocked(self):
        client = self._client_for('payrollminds_privacy')
        response = client.get(reverse('contracts:dpa_review_pack_detail', kwargs={'pk': self.dpa_review.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Submit decision')

        response = client.post(
            reverse('contracts:dpa_review_set_approval_status', kwargs={'pk': self.dpa_review.pk}),
            '{}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

        response = client.post(
            reverse('contracts:dpa_review_run_analysis', kwargs={'pk': self.dpa_review.pk}),
        )
        self.assertEqual(response.status_code, 403)

    def test_signature_preparation_is_read_only_and_server_side_blocked(self):
        client = self._client_for('payrollminds_admin')
        response = client.get(
            reverse('contracts:signature_request_detail', kwargs={'pk': self.signature_request.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Send for signature')
        self.assertNotContains(response, 'Mark as Sent')
        self.assertNotContains(response, 'Mark as Cancelled')
        self.assertNotContains(response, 'Packet Workspace')
        self.assertNotContains(response, '>Edit</a>')

        self.assertEqual(client.get(reverse('contracts:signature_request_create')).status_code, 403)
        self.assertEqual(
            client.get(reverse('contracts:signature_request_update', kwargs={'pk': self.signature_request.pk})).status_code,
            403,
        )
        for endpoint, kwargs in (
            ('signature_request_send', {'pk': self.signature_request.pk}),
            ('signature_request_refresh', {'pk': self.signature_request.pk}),
            ('signature_request_send_reminder', {'pk': self.signature_request.pk}),
            ('signature_request_transition', {'pk': self.signature_request.pk, 'new_status': 'SENT'}),
            ('signature_packet_resend', {'contract_pk': self.sow.pk}),
            ('signature_packet_cancel', {'contract_pk': self.sow.pk}),
            ('signature_packet_retry', {'contract_pk': self.sow.pk}),
        ):
            response = client.post(reverse(f'contracts:{endpoint}', kwargs=kwargs))
            self.assertEqual(response.status_code, 403)
        self.signature_request.refresh_from_db()
        self.assertEqual(self.signature_request.status, SignatureRequest.Status.PENDING)

    def test_obligation_complete_controls_and_endpoint_are_read_only(self):
        client = self._client_for('payrollminds_admin')
        response = client.get(reverse('contracts:obligations_workspace'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, '>Complete</button>')
        self.assertNotContains(response, 'Mark complete')
        self.assertNotContains(response, 'Add obligation')
        self.assertNotContains(response, reverse('contracts:deadline_update', kwargs={'pk': self.deadline.pk}))

        self.assertEqual(
            client.get(reverse('contracts:deadline_create')).status_code,
            403,
        )
        self.assertEqual(
            client.get(reverse('contracts:deadline_update', kwargs={'pk': self.deadline.pk})).status_code,
            403,
        )
        for endpoint in ('deadline_complete', 'deadline_defer', 'deadline_escalate', 'deadline_delete'):
            response = client.post(reverse(f'contracts:{endpoint}', kwargs={'pk': self.deadline.pk}))
            self.assertEqual(response.status_code, 403)
        self.deadline.refresh_from_db()
        self.assertFalse(self.deadline.is_completed)
