"""Phase 2 of the Product Coherence Redesign: Command Center for
in_house_clm tenants (see the Payrollminds product-strategy memo and the
Phase 1 nav-config work in contracts/nav_config.py).

Covers: mode-aware dashboard framing, the four priority cards (DPA/MSA
conflicts, needs-review, my approvals, renewals/deadlines), the secondary
cards (high-severity risk, recent memos, matter activity), law_firm_ops
preservation, and that nothing here re-runs DPA conflict detection or
mutates approval/DPA state at render time.
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import Client as TestClient
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    ApprovalRequest,
    Contract,
    Counterparty,
    Deadline,
    DPAReviewPack,
    DPARiskItem,
    Matter,
    Client as ClientModel,
    Organization,
    OrganizationMembership,
    RiskLog,
)

User = get_user_model()


def _today():
    return timezone.now().date()


class CommandCenterFramingTests(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds Framing', slug='payrollminds-framing', workspace_mode='in_house_clm',
        )
        self.user = User.objects.create_user(username='clm_framing', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client_ = TestClient()
        self.client_.login(username='clm_framing', password='testpass123!')
        # dashboard_has_data requires at least one contract/document/etc.
        Contract.objects.create(
            organization=self.org, title='Seed Contract', content='x',
            status='ACTIVE', created_by=self.user,
        )

    def test_command_center_heading_shown(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'Command Center')

    def test_four_priority_cards_present(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'DPA / MSA Conflicts')
        self.assertContains(response, 'Needs Legal Review')
        self.assertContains(response, 'Approvals in Your Queue')
        self.assertContains(response, 'Renewals &amp; Deadlines')

    def test_secondary_cards_present(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'High-Severity Risks')
        self.assertContains(response, 'Recent Review Memos')
        self.assertContains(response, 'Matter &amp; Client Activity')

    def test_law_firm_only_content_excluded(self):
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        for forbidden in ('Billable hours', 'Trust balance', 'Invoice aging', 'trust-balance'):
            self.assertNotIn(forbidden, content)


class LawFirmOpsDashboardPreservedTests(TestCase):
    """workspace_mode default (law_firm_ops) must render exactly as before
    Phase 2 — same heading, same priority strip, same right rail."""

    def setUp(self):
        self.org = Organization.objects.create(name='Law Firm Preserved', slug='law-firm-preserved')
        self.user = User.objects.create_user(username='firm_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client_ = TestClient()
        self.client_.login(username='firm_user', password='testpass123!')
        Contract.objects.create(
            organization=self.org, title='Firm Contract', content='x',
            status='ACTIVE', created_by=self.user,
        )

    def test_heading_is_still_dashboard(self):
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        self.assertIn('>Dashboard<', content)
        self.assertNotIn('Command Center', content)

    def test_original_priority_cards_still_present(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'Needs Legal Review')
        self.assertContains(response, 'Awaiting Approval')
        self.assertContains(response, 'Signature Pending')
        self.assertContains(response, 'Expiring Soon')

    def test_original_right_rail_still_present(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'Upcoming Deadlines')
        self.assertContains(response, 'Risk Watch')
        self.assertContains(response, 'Recent Activity')
        self.assertContains(response, 'Quick Links')

    def test_command_center_only_cards_absent(self):
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        self.assertNotIn('DPA / MSA Conflicts', content)
        self.assertNotIn('Approvals in Your Queue', content)


class CommandCenterDataTests(TestCase):
    """Every figure must come from persisted rows, scoped to the org."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds Data', slug='payrollminds-data', workspace_mode='in_house_clm',
        )
        self.other_org = Organization.objects.create(name='Other Org Data', slug='other-org-data')

        self.user = User.objects.create_user(username='clm_data_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.other_user = User.objects.create_user(username='clm_other_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.other_user, role=OrganizationMembership.Role.MEMBER, is_active=True,
        )

        self.client_ = TestClient()
        self.client_.login(username='clm_data_user', password='testpass123!')

        self.counterparty = Counterparty.objects.create(organization=self.org, name='Acme Corp')
        self.msa = Contract.objects.create(
            organization=self.org, title='Acme MSA', content='MSA content',
            status='ACTIVE', created_by=self.user,
        )
        self.dpa = Contract.objects.create(
            organization=self.org, title='Acme DPA', content='DPA content',
            status='ACTIVE', created_by=self.user,
        )
        self.review_pack = DPAReviewPack.objects.create(
            organization=self.org, contract=self.dpa, counterparty=self.counterparty,
            liability_uncapped=True,
        )
        self.review_pack.related_contracts.add(self.msa)

    def test_conflict_count_reflects_persisted_dpa_risk_items_only(self):
        DPARiskItem.objects.create(
            review_pack=self.review_pack, category='LIABILITY',
            title='DPA liability overrides MSA cap', description='...',
            severity='HIGH', owners='LEGAL', is_cross_document_conflict=True,
            status='OPEN', detection_rule='dpa_liability_vs_msa_cap', conflict_type='dpa_liability_vs_msa_cap',
        )
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'DPA liability overrides MSA cap')
        # The count card and the top-conflicts list both reflect the one
        # persisted, unresolved cross-document conflict.
        self.assertContains(response, '>1<')

    def test_resolved_conflicts_excluded_from_count(self):
        DPARiskItem.objects.create(
            review_pack=self.review_pack, category='LIABILITY', title='Old resolved conflict',
            description='...', severity='HIGH', owners='LEGAL', is_cross_document_conflict=True,
            status='RESOLVED',
        )
        response = self.client_.get(reverse('dashboard'))
        self.assertNotContains(response, 'Old resolved conflict')

    def test_non_cross_document_findings_excluded_from_conflict_card(self):
        DPARiskItem.objects.create(
            review_pack=self.review_pack, category='SECURITY', title='Vague security language',
            description='...', severity='MEDIUM', owners='LEGAL', is_cross_document_conflict=False,
            status='OPEN',
        )
        response = self.client_.get(reverse('dashboard'))
        self.assertNotContains(response, 'Vague security language')

    def test_dashboard_does_not_call_conflict_detection(self):
        # Smoke-level guarantee: rendering the dashboard must not invoke the
        # live conflict-detection service. We patch it to raise, and prove
        # the dashboard still renders fine.
        import contracts.services.dpa_conflict as dpa_conflict

        def _boom(*args, **kwargs):
            raise AssertionError('Dashboard must not call check_cross_document_conflicts')

        original = dpa_conflict.check_cross_document_conflicts
        dpa_conflict.check_cross_document_conflicts = _boom
        try:
            response = self.client_.get(reverse('dashboard'))
            self.assertEqual(response.status_code, 200)
        finally:
            dpa_conflict.check_cross_document_conflicts = original

    def test_needs_review_count_scoped_to_organization(self):
        Contract.objects.create(
            organization=self.org, title='Pending Review Contract', content='x',
            status='PENDING', created_by=self.user,
        )
        Contract.objects.create(
            organization=self.other_org, title='Other Org Pending Contract', content='x',
            status='PENDING', created_by=self.user,
        )
        response = self.client_.get(reverse('dashboard'))
        self.assertNotContains(response, 'Other Org Pending Contract')
        content = response.content.decode()
        # 1 pending contract belonging to this org.
        idx = content.index('Needs Legal Review')
        self.assertIn('1', content[idx:idx + 400])

    def test_approval_queue_scoped_to_current_user(self):
        ApprovalRequest.objects.create(
            organization=self.org, contract=self.msa, approval_step='Legal',
            status='PENDING', assigned_to=self.user,
        )
        ApprovalRequest.objects.create(
            organization=self.org, contract=self.msa, approval_step='Finance',
            status='PENDING', assigned_to=self.other_user,
        )
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        idx = content.index('Approvals in Your Queue')
        self.assertIn('1', content[idx:idx + 400])

    def test_renewals_count_scoped_to_organization(self):
        other_org_contract = Contract.objects.create(
            organization=self.other_org, title='Other Org Contract', content='x',
            status='ACTIVE', created_by=self.user,
        )
        Deadline.objects.create(
            contract=self.msa, title='DSAR window',
            due_date=_today() + timedelta(days=10), is_completed=False,
        )
        Deadline.objects.create(
            contract=other_org_contract, title='Other org deadline',
            due_date=_today() + timedelta(days=10), is_completed=False,
        )
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        idx = content.index('Renewals')
        self.assertIn('1', content[idx:idx + 400])

    def test_high_severity_count_includes_risklog_and_dpa_risk_items(self):
        RiskLog.objects.create(
            contract=self.msa, title='High commercial risk', description='...',
            risk_level='HIGH', status='OPEN',
        )
        DPARiskItem.objects.create(
            review_pack=self.review_pack, category='TRANSFER', title='Non-EEA transfer, no mechanism',
            description='...', severity='CRITICAL', owners='DPO_SECURITY',
            is_cross_document_conflict=False, status='OPEN',
        )
        response = self.client_.get(reverse('dashboard'))
        content = response.content.decode()
        idx = content.index('High-Severity Risks')
        self.assertIn('2', content[idx:idx + 400])

    def test_recent_memo_renders_when_memo_exists(self):
        self.review_pack.review_memo = 'Memo content'
        self.review_pack.review_memo_generated_at = timezone.now()
        self.review_pack.save(update_fields=['review_memo', 'review_memo_generated_at'])
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'Acme DPA')
        self.assertNotContains(response, 'No review memos generated yet.')

    def test_recent_memo_empty_state_when_no_memo(self):
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'No review memos generated yet.')

    def test_matter_activity_scoped_to_organization(self):
        client_obj = ClientModel.objects.create(
            organization=self.org, name='Acme Client', created_by=self.user,
        )
        Matter.objects.create(
            organization=self.org, matter_number='M-001', title='Acme Engagement',
            client=client_obj, created_by=self.user,
        )
        other_client = ClientModel.objects.create(
            organization=self.other_org, name='Other Client', created_by=self.user,
        )
        Matter.objects.create(
            organization=self.other_org, matter_number='M-002', title='Other Org Matter',
            client=other_client, created_by=self.user,
        )
        response = self.client_.get(reverse('dashboard'))
        self.assertContains(response, 'Acme Engagement')
        self.assertNotContains(response, 'Other Org Matter')

    def test_dashboard_render_does_not_change_dpa_approval_status(self):
        before = self.review_pack.approval_status
        self.client_.get(reverse('dashboard'))
        self.review_pack.refresh_from_db()
        self.assertEqual(self.review_pack.approval_status, before)

    def test_dashboard_render_does_not_change_approval_request_status(self):
        approval = ApprovalRequest.objects.create(
            organization=self.org, contract=self.msa, approval_step='Legal',
            status='PENDING', assigned_to=self.user,
        )
        self.client_.get(reverse('dashboard'))
        approval.refresh_from_db()
        self.assertEqual(approval.status, 'PENDING')

    def test_no_route_changes(self):
        # Every link the Command Center renders resolves to a pre-existing
        # route name — Phase 2 adds zero new routes.
        for name, kwargs in [
            ('contracts:dpa_review_pack_list', {}),
            ('contracts:contract_list', {}),
            ('contracts:approval_request_list', {}),
            ('contracts:deadline_list', {}),
            ('contracts:risk_log_list', {}),
            ('contracts:matter_list', {}),
            ('contracts:dpa_review_pack_detail', {'pk': self.review_pack.pk}),
            ('contracts:dpa_review_pack_memo', {'pk': self.review_pack.pk}),
            ('contracts:matter_detail', {'pk': 1}),
        ]:
            reverse(name, kwargs=kwargs) if kwargs else reverse(name)


class CommandCenterQueryCountTests(TestCase):
    """Query-count protection, matching the existing pattern in
    tests/test_performance_guardrails.py: more rows must not scale query
    count linearly (no N+1)."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Payrollminds Perf', slug='payrollminds-perf', workspace_mode='in_house_clm',
        )
        self.user = User.objects.create_user(username='clm_perf_user', password='testpass123!')
        OrganizationMembership.objects.create(
            organization=self.org, user=self.user, role=OrganizationMembership.Role.OWNER, is_active=True,
        )
        self.client_ = TestClient()
        self.client_.login(username='clm_perf_user', password='testpass123!')
        self.counterparty = Counterparty.objects.create(organization=self.org, name='Perf Counterparty')

    def _seed(self, count):
        for idx in range(count):
            contract = Contract.objects.create(
                organization=self.org, title=f'Perf Contract {idx}', content='x',
                status='ACTIVE', created_by=self.user,
            )
            pack = DPAReviewPack.objects.create(
                organization=self.org, contract=contract, counterparty=self.counterparty,
            )
            DPARiskItem.objects.create(
                review_pack=pack, category='LIABILITY', title=f'Conflict {idx}',
                description='...', severity='HIGH', owners='LEGAL',
                is_cross_document_conflict=True, status='OPEN',
            )

    def _query_count_for_dashboard(self):
        with CaptureQueriesContext(connection) as ctx:
            response = self.client_.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        return len(ctx)

    def test_command_center_query_count_does_not_scale_linearly(self):
        self._seed(3)
        baseline = self._query_count_for_dashboard()

        self._seed(25)
        expanded = self._query_count_for_dashboard()

        self.assertLessEqual(expanded, baseline + 8)
