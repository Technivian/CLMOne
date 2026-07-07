"""Tests for the Legal Task create/edit form fix-up.

Root cause covered here: legal_task_form.html referenced form fields that
did not exist on LegalTaskForm (task_type, subject, status, is_recurring),
so Django silently rendered them as nothing, and the real required field
(description) was never rendered at all — every submission failed
validation. This file locks in that the visible form now matches the real
LegalTaskForm fields, that create/edit succeed, that the Tasks queue and
audit log reflect a successful create, and that copy stays clean.
"""
import re
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from contracts.models import AuditLog, Contract, LegalTask, Organization, OrganizationMembership

ISO_TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}')


class TasksFormRenderingTests(TestCase):
    """The create form must show real, human-labeled fields — no fields
    that silently resolve to nothing because they don't exist on the form."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Form Firm', slug='tasks-form-firm')
        self.user = User.objects.create_user(username='form_user', password='testpass123', email='form@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='form_user', password='testpass123')

    def test_create_form_renders_real_required_fields(self):
        response = self.client.get(reverse('contracts:legal_task_create'))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for field_name in ('title', 'description', 'priority', 'due_date', 'assigned_to', 'contract', 'matter'):
            self.assertIn(f'name="{field_name}"', html, f'form field "{field_name}" is not rendered')

    def test_create_form_does_not_reference_nonexistent_fields(self):
        """task_type/subject/status/is_recurring never existed on
        LegalTaskForm — the old template referenced them anyway and Django
        silently rendered nothing. Confirms they're gone, not just hidden."""
        response = self.client.get(reverse('contracts:legal_task_create'))
        html = response.content.decode()
        self.assertNotIn('form.task_type', html)
        self.assertNotIn('form.subject', html)
        self.assertNotIn('name="task_type"', html)
        self.assertNotIn('name="subject"', html)
        self.assertNotIn('name="is_recurring"', html)

    def test_priority_choices_render_human_labels_not_raw_enum(self):
        response = self.client.get(reverse('contracts:legal_task_create'))
        html = response.content.decode()
        self.assertIn('>Low<', html)
        self.assertIn('>Medium<', html)
        self.assertIn('>High<', html)
        self.assertIn('>Urgent<', html)
        # The select's own raw values (LOW/HIGH/...) are expected as option
        # value="" attributes — only assert the visible label text doesn't
        # leak the enum as its own display text.
        self.assertNotIn('>LOW<', html)
        self.assertNotIn('>URGENT<', html)

    def test_form_labels_are_human_readable(self):
        response = self.client.get(reverse('contracts:legal_task_create'))
        html = response.content.decode()
        self.assertIn('Title', html)
        self.assertIn('Description', html)
        self.assertIn('Priority', html)
        self.assertIn('Due Date', html)
        self.assertIn('Assigned To', html)

    def test_create_form_explains_the_contract_or_matter_requirement(self):
        """Contract/Matter are no longer labeled "(optional)" — at least one
        is required, so the form must say so up front rather than only on
        a failed submission."""
        response = self.client.get(reverse('contracts:legal_task_create'))
        html = response.content.decode()
        self.assertIn('Select a contract or a matter', html)
        self.assertNotIn('Contract <span class="c-muted">(optional)</span>', html)


class TasksFormSubmissionTests(TestCase):
    """Create must actually succeed for an eligible user, invalid submissions
    must show clear errors, and a successful create must be reflected in the
    Tasks queue and the audit log."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Submit Firm', slug='tasks-submit-firm')
        self.user = User.objects.create_user(username='submit_user', password='testpass123', email='submit@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.contract = Contract.objects.create(
            organization=self.organization, title='Form Contract', content='Seed', status='ACTIVE',
            created_by=self.user,
        )
        self.client = TestClient()
        self.client.login(username='submit_user', password='testpass123')

    def _valid_payload(self, **overrides):
        payload = {
            'title': 'Draft the license amendment',
            'description': 'Coordinate with the counterparty on renewal terms.',
            'priority': LegalTask.Priority.HIGH,
            'due_date': (timezone.localdate() + timedelta(days=5)).isoformat(),
            'assigned_to': self.user.pk,
            'contract': self.contract.pk,
            'matter': '',
        }
        payload.update(overrides)
        return payload

    def test_valid_create_succeeds_and_redirects_to_tasks_queue(self):
        response = self.client.post(reverse('contracts:legal_task_create'), data=self._valid_payload())
        self.assertRedirects(response, reverse('contracts:legal_task_kanban'))
        self.assertTrue(LegalTask.objects.filter(title='Draft the license amendment').exists())

    def test_invalid_submission_shows_clear_errors_not_a_silent_failure(self):
        response = self.client.post(reverse('contracts:legal_task_create'), data=self._valid_payload(title='', description=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LegalTask.objects.filter(description='').exists())
        html = response.content.decode()
        self.assertIn('This field is required', html)

    def test_created_task_appears_in_the_tasks_queue(self):
        self.client.post(reverse('contracts:legal_task_create'), data=self._valid_payload())
        task = LegalTask.objects.get(title='Draft the license amendment')
        response = self.client.get(reverse('contracts:legal_task_kanban'))
        tabs = response.context['queue_tabs']
        all_open = next(t for t in tabs if t['key'] == 'all_open')
        ids = [r['id'] for r in all_open['rows']]
        self.assertIn(task.id, ids)

    def test_create_logs_the_create_audit_event(self):
        self.client.post(reverse('contracts:legal_task_create'), data=self._valid_payload())
        task = LegalTask.objects.get(title='Draft the license amendment')
        entry = AuditLog.objects.filter(model_name='LegalTask', object_id=task.pk, action=AuditLog.Action.CREATE).first()
        self.assertIsNotNone(entry)
        self.assertEqual((entry.changes or {}).get('event'), 'legal_task_created')

    def test_create_without_a_linked_contract_or_matter_is_rejected_with_a_clear_error(self):
        """LegalTask carries no organization of its own — the Tasks queue
        can only find a task through contract__organization or
        matter__organization. Without either link the task would save
        successfully and then be permanently invisible in every tab, so the
        form must reject this combination instead of silently losing data."""
        response = self.client.post(reverse('contracts:legal_task_create'), data=self._valid_payload(contract='', matter=''))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(LegalTask.objects.filter(title='Draft the license amendment').exists())
        html = response.content.decode()
        self.assertIn('Select a contract or a matter', html)


class TasksFormUpdateTests(TestCase):
    """Edit must continue to work through the same fixed template, and
    stay behind the same contract/matter authorization as before."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Update Firm', slug='tasks-update-firm')
        self.editor = User.objects.create_user(username='update_editor', password='testpass123', email='updeditor@example.com')
        self.bystander = User.objects.create_user(username='update_bystander', password='testpass123', email='updbystander@example.com')
        for u in (self.editor, self.bystander):
            OrganizationMembership.objects.create(organization=self.organization, user=u, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.contract = Contract.objects.create(
            organization=self.organization, title='Update Contract', content='Seed', status='ACTIVE',
            created_by=self.editor,
        )
        self.task = LegalTask.objects.create(
            title='Existing Task', description='Seed', contract=self.contract,
            assigned_to=self.editor, due_date=timezone.localdate() + timedelta(days=1),
            priority=LegalTask.Priority.MEDIUM, status=LegalTask.Status.PENDING,
        )

    def test_update_form_renders_with_existing_values(self):
        client = TestClient()
        client.login(username='update_editor', password='testpass123')
        response = client.get(reverse('contracts:legal_task_update', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Existing Task', response.content.decode())

    def test_update_succeeds_and_redirects_to_tasks_queue(self):
        client = TestClient()
        client.login(username='update_editor', password='testpass123')
        response = client.post(reverse('contracts:legal_task_update', kwargs={'pk': self.task.pk}), data={
            'title': 'Updated Task Title', 'description': 'Updated body', 'priority': LegalTask.Priority.LOW,
            'due_date': (timezone.localdate() + timedelta(days=2)).isoformat(),
            'assigned_to': self.editor.pk, 'contract': self.contract.pk, 'matter': '',
        })
        self.assertRedirects(response, reverse('contracts:legal_task_kanban'))
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task Title')

    def test_update_clearing_both_contract_and_matter_is_rejected(self):
        """Same rule applies on edit — clearing the last remaining link
        would orphan an already-visible task just as much as never setting
        one on create."""
        client = TestClient()
        client.login(username='update_editor', password='testpass123')
        response = client.post(reverse('contracts:legal_task_update', kwargs={'pk': self.task.pk}), data={
            'title': 'Existing Task', 'description': 'Seed', 'priority': LegalTask.Priority.MEDIUM,
            'due_date': (timezone.localdate() + timedelta(days=1)).isoformat(),
            'assigned_to': self.editor.pk, 'contract': '', 'matter': '',
        })
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.contract_id, self.contract.id)
        self.assertIn('Select a contract or a matter', response.content.decode())

    def test_cross_tenant_update_returns_404(self):
        other_org = Organization.objects.create(name='Other Update Firm', slug='tasks-update-other-firm')
        other_user = User.objects.create_user(username='update_other_org', password='testpass123', email='updother@example.com')
        OrganizationMembership.objects.create(organization=other_org, user=other_user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        client = TestClient()
        client.login(username='update_other_org', password='testpass123')
        response = client.get(reverse('contracts:legal_task_update', kwargs={'pk': self.task.pk}))
        self.assertEqual(response.status_code, 404)


class TasksFormCopyQualityTests(TestCase):
    """No raw enums, ISO timestamps, model names, or mixed-language chrome."""

    def setUp(self):
        self.organization = Organization.objects.create(name='Form Copy Firm', slug='tasks-form-copy-firm')
        self.user = User.objects.create_user(username='form_copy_user', password='testpass123', email='formcopy@example.com')
        OrganizationMembership.objects.create(organization=self.organization, user=self.user, role=OrganizationMembership.Role.MEMBER, is_active=True)
        self.client = TestClient()
        self.client.login(username='form_copy_user', password='testpass123')

    def test_no_raw_internals_in_create_form(self):
        response = self.client.get(reverse('contracts:legal_task_create'))
        html = response.content.decode()
        self.assertNotIn('LegalTask', html)
        self.assertIsNone(ISO_TIMESTAMP_RE.search(html), 'Found a raw ISO timestamp in the task form')

    def test_no_raw_internals_in_edit_form(self):
        contract = Contract.objects.create(
            organization=self.organization, title='Copy Form Contract', content='Seed',
            status='ACTIVE', created_by=self.user,
        )
        task = LegalTask.objects.create(
            title='Copy Form Task', description='Seed', contract=contract, assigned_to=self.user,
            priority=LegalTask.Priority.URGENT, due_date=timezone.localdate(), status=LegalTask.Status.IN_PROGRESS,
        )
        response = self.client.get(reverse('contracts:legal_task_update', kwargs={'pk': task.pk}))
        html = response.content.decode()
        self.assertNotIn('LegalTask', html)
        self.assertIsNone(ISO_TIMESTAMP_RE.search(html), 'Found a raw ISO timestamp in the task edit form')
