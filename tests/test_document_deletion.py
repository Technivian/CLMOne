"""Phase 4E — document deletion authorization + retention (soft delete)."""
from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from contracts.models import (
    AuditLog,
    Document,
    LegalHold,
    Matter,
    Organization,
    OrganizationMembership,
)
from contracts.services.document_deletion import (
    DocumentDeletionBlocked,
    DocumentDeletionForbidden,
    soft_delete_document,
)

User = get_user_model()
PW = 'StrongPw!123'


def _org(name, slug):
    return Organization.objects.create(name=name, slug=slug)


def _member(org, username, role):
    u = User.objects.create_user(username=username, password=PW, email=f'{username}@ex.com')
    OrganizationMembership.objects.create(user=u, organization=org, role=role, is_active=True)
    return u


def _doc(org, uploaded_by=None, matter=None):
    return Document.objects.create(organization=org, title='Doc', uploaded_by=uploaded_by, matter=matter)


class DeletionAuthorizationTests(TestCase):
    def setUp(self):
        self.org = _org('Del Org', 'del-org')
        self.owner = _member(self.org, 'owner', OrganizationMembership.Role.OWNER)
        self.admin = _member(self.org, 'admin', OrganizationMembership.Role.ADMIN)
        self.member = _member(self.org, 'member', OrganizationMembership.Role.MEMBER)
        self.other_member = _member(self.org, 'other', OrganizationMembership.Role.MEMBER)

    def test_owner_can_delete_any(self):
        d = _doc(self.org, uploaded_by=self.member)
        soft_delete_document(self.owner, d)
        d.refresh_from_db()
        self.assertTrue(d.is_deleted)

    def test_admin_can_delete_any(self):
        d = _doc(self.org, uploaded_by=self.member)
        soft_delete_document(self.admin, d)
        d.refresh_from_db()
        self.assertTrue(d.is_deleted)

    def test_member_cannot_delete_others_document(self):
        d = _doc(self.org, uploaded_by=self.other_member)
        with self.assertRaises(DocumentDeletionForbidden):
            soft_delete_document(self.member, d)
        d.refresh_from_db()
        self.assertFalse(d.is_deleted)

    def test_member_can_delete_own_upload(self):
        d = _doc(self.org, uploaded_by=self.member)
        soft_delete_document(self.member, d)
        d.refresh_from_db()
        self.assertTrue(d.is_deleted)


class DeletionRetentionTests(TestCase):
    def setUp(self):
        self.org = _org('Ret Org', 'ret-org')
        self.owner = _member(self.org, 'owner', OrganizationMembership.Role.OWNER)

    def test_legal_hold_blocks_deletion(self):
        from contracts.models import Client as ClientModel
        client = ClientModel.objects.create(organization=self.org, name='Acme')
        matter = Matter.objects.create(organization=self.org, title='M', client=client)
        LegalHold.objects.create(
            organization=self.org, title='Hold', description='x', matter=matter,
            status=LegalHold.Status.ACTIVE, hold_start_date=date(2026, 1, 1),
        )
        d = _doc(self.org, uploaded_by=self.owner, matter=matter)
        with self.assertRaises(DocumentDeletionBlocked):
            soft_delete_document(self.owner, d)
        d.refresh_from_db()
        self.assertFalse(d.is_deleted)

    def test_soft_delete_preserves_row_and_audits(self):
        d = _doc(self.org, uploaded_by=self.owner)
        soft_delete_document(self.owner, d)
        # Row preserved (tombstone), not hard-deleted.
        self.assertTrue(Document.objects.filter(pk=d.pk).exists())
        d.refresh_from_db()
        self.assertTrue(d.is_deleted)
        self.assertIsNotNone(d.deleted_at)
        self.assertEqual(d.deleted_by_id, self.owner.id)
        audit = AuditLog.objects.filter(event_type='document.deleted', object_id=d.pk).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.organization_id, self.org.id)

    def test_idempotent_repeat(self):
        d = _doc(self.org, uploaded_by=self.owner)
        soft_delete_document(self.owner, d)
        before = AuditLog.objects.filter(event_type='document.deleted').count()
        soft_delete_document(self.owner, d)  # no error, no second audit
        after = AuditLog.objects.filter(event_type='document.deleted').count()
        self.assertEqual(before, after)


class DeletionVisibilityTests(TestCase):
    def setUp(self):
        self.org = _org('Vis Org', 'vis-org')
        self.owner = _member(self.org, 'owner', OrganizationMembership.Role.OWNER)
        self.client = Client()
        self.client.force_login(self.owner)

    def test_deleted_excluded_from_list(self):
        d = _doc(self.org, uploaded_by=self.owner)
        soft_delete_document(self.owner, d)
        resp = self.client.get(reverse('contracts:document_list'))
        self.assertNotIn(d, list(resp.context['documents']))

    def test_deleted_detail_returns_404(self):
        d = _doc(self.org, uploaded_by=self.owner)
        soft_delete_document(self.owner, d)
        resp = self.client.get(reverse('contracts:document_detail', args=[d.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_member_cross_role_via_delete_view(self):
        member = _member(self.org, 'm2', OrganizationMembership.Role.MEMBER)
        d = _doc(self.org, uploaded_by=self.owner)  # not member's upload
        c = Client()
        c.force_login(member)
        c.post(reverse('contracts:document_delete', args=[d.pk]))
        d.refresh_from_db()
        self.assertFalse(d.is_deleted)  # blocked by role check
