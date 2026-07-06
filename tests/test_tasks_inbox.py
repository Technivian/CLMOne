"""Tests for the Tasks Queue conversion (WorkQueue foundation block).

Covers: role-gated rendering, per-tab filtering correctness, the reusable
StageDots/AssigneeChip/ActivityLine components on task rows, a real Complete
action reusing existing contract/matter authorization, safety against
repeated invalid transitions, cross-tenant isolation, audit logging (both
creation and completion), and copy free of raw enums/ISO timestamps/model
names.
"""
import json
import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import (
    AuditLog,
    Client,
    Contract,
    LegalTask,
    Matter,
    Organization,
    OrganizationMembership,
)

ISO_TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}')


def tasks_body(html):
    """The main Tasks content region only — excludes both the sidebar nav
    and Django Debug Toolbar's panels (DEBUG=True dumps the full template
    context, so raw values can appear there even when the real page body
    never renders them). Anchored on the stable `id="tasks-root"` marker."""
    start = html.find('id="tasks-root"')
    end = html.find('id="djDebug"')
    if start == -1:
        return html
    return html[start:end] if end != -1 else html[start:]


class TasksRoleRenderingTests(TestCase):
    """Any active org member can load the Tasks queue; no extra role gate."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Role Firm', slug='tasks-role-firm')

    def _client_for_role(self, role, username):
        user = User.objects.create_user(username=username, password='testpass123', email=f'{username}@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=user, role=role, is_active=True)
        client = TestClient()
        client.login(username=username, password='testpass123')
        return client

    def test_tasks_renders_for_owner(self):
        client = self._client_for_role(OrganizationMembership.Role.OWNER, 'tasks_owner')
        response = client.get(reverse('contracts:legal_task_kanban'))
        self.assertEqual(response.status_code, 200)

    def test_tasks_renders_for_admin(self):
        client = self._client_for_role(OrganizationMembership.Role.ADMIN, 'tasks_admin')
        response = client.get(reverse('contracts:legal_task_kanban'))
        self.assertEqual(response.status_code, 200)

    def test_tasks_renders_for_member(self):
        client = self._client_for_role(OrganizationMembership.Role.MEMBER, 'tasks_member')
        response = client.get(reverse('contracts:legal_task_kanban'))
        self.assertEqual(response.status_code, 200)


class TasksQueueTabFilteringTests(TestCase):
    """Each saved-view tab must contain exactly the rows its label promises."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Tab Firm', slug='tasks-tab-firm')
        self.creator = User.objects.create_user(username='tab_creator', password='testpass123', email='creator@example.com')
        self.assignee = User.objects.create_user(username='tab_assignee', password='testpass123', email='assignee@example.com')
        self.other = User.objects.create_user(username='tab_other', password='testpass123', email='other@example.com')
        for u in (self.creator, self.assignee, self.other):
            OrganizationMembership.objects.create(organization=self.organization, user=u, role=OrganizationMembership.Role.MEMBER, is_active=True)

        self.contract = Contract.objects.create(
            organization=self.organization, title='Tab Contract', content='Seed', status='ACTIVE',
            created_by=self.creator,
        )
        today = timezone.localdate()

        self.assigned = LegalTask.objects.create(
            title='Assigned task', description='Seed', contract=self.contract,
            assigned_to=self.assignee, due_date=today + timedelta(days=3), status=LegalTask.Status.PENDING,
        )
        self.due_soon = LegalTask.objects.create(
            title='Due soon task', description='Seed', contract=self.contract,
            assigned_to=self.other, due_date=today + timedelta(days=2), status=LegalTask.Status.IN_PROGRESS,
        )
        self.overdue = LegalTask.objects.create(
            title='Overdue task', description='Seed', contract=self.contract,
            assigned_to=self.other, due_date=today - timedelta(days=1), status=LegalTask.Status.PENDING,
        )
        self.completed = LegalTask.objects.create(
            title='Completed task', description='Seed', contract=self.contract,
            assigned_to=self.assignee, due_date=today - timedelta(days=5), status=LegalTask.Status.COMPLETED,
        )
        self.cancelled = LegalTask.objects.create(
            title='Cancelled task', description='Seed', contract=self.contract,
            assigned_to=self.assignee, due_date=today, status=LegalTask.Status.CANCELLED,
        )

        self.client = TestClient()
        self.client.login(username='tab_assignee', password='testpass123')

    def _tab(self, response, key):
        tabs = response.context['queue_tabs']
        return next(t for t in tabs if t['key'] == key)

    def test_assigned_to_me_only_shows_open_tasks_assigned_to_current_user(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'assigned_to_me')['rows']]
        self.assertIn(self.assigned.id, ids)
        self.assertNotIn(self.due_soon.id, ids)
        self.assertNotIn(self.overdue.id, ids)
        self.assertNotIn(self.completed.id, ids)
        self.assertNotIn(self.cancelled.id, ids)

    def test_due_soon_shows_open_tasks_due_within_a_week(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'due_soon')['rows']]
        self.assertIn(self.assigned.id, ids)
        self.assertIn(self.due_soon.id, ids)
        self.assertNotIn(self.overdue.id, ids)
        self.assertNotIn(self.completed.id, ids)

    def test_overdue_shows_only_past_due_open_tasks(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'overdue')['rows']]
        self.assertEqual(ids, [self.overdue.id])

    def test_completed_shows_only_completed(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'completed')['rows']]
        self.assertEqual(ids, [self.completed.id])

    def test_all_open_excludes_completed_and_cancelled(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'all_open')['rows']]
        self.assertIn(self.assigned.id, ids)
        self.assertIn(self.due_soon.id, ids)
        self.assertIn(self.overdue.id, ids)
        self.assertNotIn(self.completed.id, ids)
        self.assertNotIn(self.cancelled.id, ids)

    def test_created_by_me_uses_creation_audit_log_not_assignment(self):
        """LegalTask has no created_by field — attribution comes from the
        CREATE audit entry written by LegalTaskCreateView. A task created
        through the ORM directly (as this fixture does) has no such entry,
        so it must NOT show under anyone's 'Created by Me' tab — proving the
        tab reflects real creation events rather than guessing from
        assignment."""
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in self._tab(response, 'created_by_me')['rows']]
        self.assertEqual(ids, [])

    def test_created_by_me_shows_tasks_created_through_the_create_view(self):
        client = TestClient()
        client.login(username='tab_creator', password='testpass123')
        client.post(reverse('contracts:legal_task_create'), data={
            'title': 'Creator-made task', 'description': 'Seed', 'priority': LegalTask.Priority.MEDIUM,
            'due_date': timezone.localdate() + timedelta(days=1), 'contract': self.contract.pk,
        })
        created_task = LegalTask.objects.get(title='Creator-made task')

        response = client.get(reverse('contracts:legal_task_kanban'))
        ids = [r['id'] for r in response.context['queue_tabs'][1]['rows']]
        self.assertIn(created_task.id, ids)

        other_response = self.client.get(reverse('contracts:legal_task_kanban'))
        other_ids = [r['id'] for r in other_response.context['queue_tabs'][1]['rows']]
        self.assertNotIn(created_task.id, other_ids)


class TasksRowComponentTests(TestCase):
    """Task rows reuse StageDots/AssigneeChip/ActivityLine, not bespoke markup."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Row Firm', slug='tasks-row-firm')
        self.user = User.objects.create_user(username='row_user', password='testpass123', email='row@example.com', first_name='Rowan')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='row_user', password='testpass123')

    def test_row_renders_stage_dots_assignee_chip_and_activity_line(self):
        contract = Contract.objects.create(
            organization=self.organization, title='Component Row Contract', content='Seed',
            status='ACTIVE', lifecycle_stage='NEGOTIATION', created_by=self.user,
        )
        task = LegalTask.objects.create(
            title='Row Component Task', description='Seed', contract=contract,
            assigned_to=self.user, due_date=timezone.localdate() + timedelta(days=1), status=LegalTask.Status.PENDING,
        )
        from contracts.middleware import log_action
        log_action(
            self.user, 'CREATE', 'LegalTask', task.id, str(task),
            changes={'event': 'legal_task_created'}, organization=self.organization,
        )

        response = self.client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())
        self.assertIn('stage-dot-current', body)
        self.assertIn('Negotiation', body)
        self.assertIn('Rowan', body)
        self.assertIn('Row Component Task', body)


class TasksActionEligibilityTests(TestCase):
    """Complete button is eligible-only; the endpoint stays the enforcement boundary."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Action Firm', slug='tasks-action-firm')
        self.editor = User.objects.create_user(username='action_editor', password='testpass123', email='editor@example.com')
        self.bystander = User.objects.create_user(username='action_bystander', password='testpass123', email='bystander2@example.com')
        for u in (self.editor, self.bystander):
            OrganizationMembership.objects.create(organization=self.organization, user=u, role=OrganizationMembership.Role.MEMBER, is_active=True)

        self.contract = Contract.objects.create(
            organization=self.organization, title='Action Contract', content='Seed', status='ACTIVE',
            created_by=self.editor,
        )
        self.task = LegalTask.objects.create(
            title='Action Task', description='Seed', contract=self.contract,
            assigned_to=self.editor, due_date=timezone.localdate(), status=LegalTask.Status.PENDING,
        )

    def test_eligible_editor_sees_complete_button(self):
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        response = client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())
        self.assertIn('data-task-action="complete"', body)

    def test_bystander_without_contract_access_does_not_see_complete_button(self):
        client = TestClient()
        client.login(username='action_bystander', password='testpass123')
        response = client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())
        self.assertNotIn('data-task-action="complete"', body)

    def test_every_row_keeps_an_edit_link_regardless_of_complete_eligibility(self):
        client = TestClient()
        client.login(username='action_bystander', password='testpass123')
        response = client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())
        self.assertIn(reverse('contracts:legal_task_update', kwargs={'pk': self.task.pk}), body)

    def test_eligible_editor_can_complete_via_the_endpoint(self):
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        response = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, LegalTask.Status.COMPLETED)

    def test_unauthorized_bystander_cannot_complete_via_direct_post(self):
        client = TestClient()
        client.login(username='action_bystander', password='testpass123')
        response = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, LegalTask.Status.PENDING)

    def test_repeated_invalid_transition_fails_safely(self):
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        first = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(first.status_code, 200)

        second = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(second.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, LegalTask.Status.COMPLETED)

    def test_already_completed_task_never_shows_complete_button_even_for_eligible_actor(self):
        self.task.status = LegalTask.Status.COMPLETED
        self.task.save(update_fields=['status'])
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        response = client.get(reverse('contracts:legal_task_kanban'))
        tabs = response.context['queue_tabs']
        row = next(r for t in tabs for r in t['rows'] if r['id'] == self.task.id)
        self.assertFalse(row['can_complete'])
        body = tasks_body(response.content.decode())
        self.assertNotIn('data-task-action="complete"', body)

    def test_complete_decision_is_audit_logged(self):
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        entry = AuditLog.objects.filter(model_name='LegalTask', object_id=self.task.pk).order_by('-timestamp').first()
        self.assertIsNotNone(entry)
        self.assertEqual((entry.changes or {}).get('event'), 'legal_task_completed')

    def test_task_creation_is_audit_logged(self):
        client = TestClient()
        client.login(username='action_editor', password='testpass123')
        client.post(reverse('contracts:legal_task_create'), data={
            'title': 'Newly created task', 'description': 'Seed', 'priority': LegalTask.Priority.MEDIUM,
            'due_date': timezone.localdate() + timedelta(days=1), 'contract': self.contract.pk,
        })
        new_task = LegalTask.objects.get(title='Newly created task')
        entry = AuditLog.objects.filter(model_name='LegalTask', object_id=new_task.pk, action=AuditLog.Action.CREATE).first()
        self.assertIsNotNone(entry)
        self.assertEqual((entry.changes or {}).get('event'), 'legal_task_created')


class TasksMatterLinkedAuthorizationTests(TestCase):
    """A task linked to a Matter (not a Contract) is gated by matter
    organization membership rather than contract-edit access."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Matter Firm', slug='tasks-matter-firm')
        self.other_org = Organization.objects.create(name='Other Matter Firm', slug='tasks-other-matter-firm')
        self.member = User.objects.create_user(username='matter_member', password='testpass123', email='matter@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.member, role=OrganizationMembership.Role.MEMBER, is_active=True)

        client_obj = Client.objects.create(organization=self.organization, name='Matter Client')
        self.matter = Matter.objects.create(organization=self.organization, title='Matter Task Matter', client=client_obj)
        self.task = LegalTask.objects.create(
            title='Matter Task', description='Seed', matter=self.matter,
            due_date=timezone.localdate(), status=LegalTask.Status.PENDING,
        )

    def test_same_org_member_can_complete_matter_linked_task(self):
        client = TestClient()
        client.login(username='matter_member', password='testpass123')
        response = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_other_org_member_gets_404_for_matter_linked_task(self):
        other_user = User.objects.create_user(username='other_org_user', password='testpass123', email='otherorg@example.com')
        OrganizationMembership.objects.create(organization=self.other_org, user=other_user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        client = TestClient()
        client.login(username='other_org_user', password='testpass123')
        response = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class TasksCrossTenantIsolationTests(TestCase):
    def setUp(self):
        self.org_a = Organization.objects.create(name='Org A', slug='tasks-org-a')
        self.org_b = Organization.objects.create(name='Org B', slug='tasks-org-b')
        self.user_a = User.objects.create_user(username='tasks_iso_a', password='testpass123', email='a@example.com')
        self.user_b = User.objects.create_user(username='tasks_iso_b', password='testpass123', email='b@example.com')
        OrganizationMembership.objects.create(organization=self.org_a, user=self.user_a, role=OrganizationMembership.Role.MEMBER, is_active=True)
        OrganizationMembership.objects.create(organization=self.org_b, user=self.user_b, role=OrganizationMembership.Role.MEMBER, is_active=True)

        self.contract_a = Contract.objects.create(
            organization=self.org_a, title='Org A Contract', content='Seed', status='ACTIVE', created_by=self.user_a,
        )
        self.task_a = LegalTask.objects.create(
            title='Org A Task', description='Seed', contract=self.contract_a,
            assigned_to=self.user_a, due_date=timezone.localdate(), status=LegalTask.Status.PENDING,
        )

    def test_other_org_member_does_not_see_task_in_any_tab(self):
        client = TestClient()
        client.login(username='tasks_iso_b', password='testpass123')
        response = client.get(reverse('contracts:legal_task_kanban'))
        for tab in response.context['queue_tabs']:
            ids = [r['id'] for r in tab['rows']]
            self.assertNotIn(self.task_a.id, ids)

    def test_other_org_member_cannot_complete_via_direct_post_gets_404(self):
        client = TestClient()
        client.login(username='tasks_iso_b', password='testpass123')
        response = client.post(
            reverse('contracts:legal_task_complete', kwargs={'pk': self.task_a.pk}),
            data=json.dumps({}), content_type='application/json',
        )
        self.assertEqual(response.status_code, 404)


class TasksCopyQualityTests(TestCase):
    """No raw enums, ISO timestamps, ORM names, or placeholder labels leak into the inbox."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Copy Firm', slug='tasks-copy-firm')
        self.user = User.objects.create_user(username='copy_user', password='testpass123', email='copy@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='copy_user', password='testpass123')

    def test_no_raw_internals_leak_into_the_page(self):
        contract = Contract.objects.create(
            organization=self.organization, title='Copy Quality Contract', content='Seed',
            status='ACTIVE', created_by=self.user,
        )
        LegalTask.objects.create(
            title='Copy Task', description='Seed', contract=contract, assigned_to=self.user,
            priority=LegalTask.Priority.URGENT, due_date=timezone.localdate() - timedelta(days=1),
            status=LegalTask.Status.IN_PROGRESS,
        )
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())

        self.assertNotIn('LegalTask', body)
        self.assertNotIn('IN_PROGRESS', body)
        self.assertIn('In Progress', body)
        self.assertNotIn('URGENT', body)
        self.assertIn('Urgent', body)
        self.assertIsNone(ISO_TIMESTAMP_RE.search(body), 'Found a raw ISO timestamp in the Tasks response')

    def test_empty_states_render_exact_specified_copy(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        body = tasks_body(response.content.decode())
        self.assertIn('No tasks assigned to you.', body)
        self.assertIn('No tasks created by you.', body)
        self.assertIn('Nothing due soon.', body)
        self.assertIn('No overdue tasks.', body)
        self.assertIn('No completed tasks yet.', body)
        self.assertIn('No open tasks.', body)


class TasksShellConvergenceTests(TestCase):
    """Tasks must use the shared shell (.page-wrap/.page-wrap-fluid) and
    PageHeader (.arch-header), not a private Kanban-board shell."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Shell Firm', slug='tasks-shell-firm')
        self.user = User.objects.create_user(username='shell_user', password='testpass123', email='shell@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='shell_user', password='testpass123')

    def test_uses_shared_page_wrap_shell(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        html = response.content.decode()
        self.assertIn('page-wrap page-wrap-fluid', html)

    def test_uses_shared_page_header_pattern(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        html = response.content.decode()
        self.assertIn('arch-header', html)
        self.assertIn('arch-title', html)

    def test_no_longer_uses_kanban_board_markup(self):
        """.board-track/.board-col/.board-card remain defined as shared CSS
        in base.html for other kanban-style surfaces — check actual class
        usage on this page's markup, not the global stylesheet."""
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        html = response.content.decode()
        self.assertNotIn('class="board-track"', html)
        self.assertNotIn('class="board-col"', html)
        self.assertNotIn('class="board-card"', html)

    def test_uses_shared_work_queue_table_styling(self):
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        html = response.content.decode()
        self.assertIn('wq-table', html)
        self.assertIn('wq-tabs', html)
