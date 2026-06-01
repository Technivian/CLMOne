"""Tests for permission transparency service."""
import unittest
from unittest.mock import MagicMock, patch

from contracts.services.permissions import PermissionTransparencyService, _ROLE_CAPABILITIES


def _make_membership(user_id=1, username='alice', role='MEMBER', is_active=True):
    m = MagicMock()
    m.user_id = user_id
    m.user.username = username
    m.role = role
    m.is_active = is_active
    return m


class TestPermissionTransparencyService(unittest.TestCase):
    def setUp(self):
        self.svc = PermissionTransparencyService()
        self.org = MagicMock()
        self.org.pk = 10
        self.org.name = 'Acme'

    @patch('contracts.services.permissions.OrganizationMembership')
    @patch('contracts.services.permissions.Contract')
    def test_get_record_access_returns_entry(self, MockContract, MockMembership):
        m = _make_membership(role='ADMIN')
        MockContract.objects.get.return_value = MagicMock(pk=5, title='Test')
        MockMembership.objects.filter.return_value.select_related.return_value = [m]
        entry = self.svc.get_record_access(5, self.org)
        self.assertEqual(entry.contract_id, 5)
        self.assertEqual(entry.contract_title, 'Test')
        self.assertEqual(len(entry.users_with_access), 1)

    @patch('contracts.services.permissions.OrganizationMembership')
    @patch('contracts.services.permissions.Contract')
    def test_record_access_capabilities_for_role(self, MockContract, MockMembership):
        m = _make_membership(role='OWNER')
        MockContract.objects.get.return_value = MagicMock(pk=1, title='T')
        MockMembership.objects.filter.return_value.select_related.return_value = [m]
        entry = self.svc.get_record_access(1, self.org)
        caps = entry.users_with_access[0].capabilities
        self.assertIn('manage_billing', caps)
        self.assertIn('delete_contracts', caps)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_get_user_permissions_found(self, MockMembership):
        m = _make_membership(user_id=7, role='ADMIN')
        MockMembership.objects.get.return_value = m
        access = self.svc.get_user_permissions(7, self.org)
        self.assertIsNotNone(access)
        self.assertEqual(access.role, 'ADMIN')
        self.assertIn('manage_policy', access.capabilities)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_get_user_permissions_not_found(self, MockMembership):
        from contracts.models import OrganizationMembership
        MockMembership.objects.get.side_effect = OrganizationMembership.DoesNotExist()
        access = self.svc.get_user_permissions(999, self.org)
        self.assertIsNone(access)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_get_org_permission_matrix(self, MockMembership):
        members = [
            _make_membership(1, 'alice', 'OWNER'),
            _make_membership(2, 'bob', 'MEMBER'),
        ]
        MockMembership.objects.filter.return_value.select_related.return_value.order_by.return_value = members
        matrix = self.svc.get_org_permission_matrix(self.org)
        self.assertEqual(matrix.org_id, 10)
        self.assertEqual(len(matrix.users), 2)

    def test_role_capabilities_member_no_admin(self):
        caps = _ROLE_CAPABILITIES['MEMBER']
        self.assertNotIn('manage_members', caps)
        self.assertNotIn('manage_billing', caps)

    def test_role_capabilities_owner_has_all(self):
        caps = _ROLE_CAPABILITIES['OWNER']
        self.assertIn('manage_billing', caps)
        self.assertIn('manage_integrations', caps)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_member_capabilities_correct(self, MockMembership):
        m = _make_membership(role='MEMBER')
        MockMembership.objects.get.return_value = m
        access = self.svc.get_user_permissions(1, self.org)
        self.assertIn('view_contracts', access.capabilities)
        self.assertNotIn('delete_contracts', access.capabilities)

    @patch('contracts.services.permissions.OrganizationMembership')
    @patch('contracts.services.permissions.Contract')
    def test_record_access_inactive_member_included(self, MockContract, MockMembership):
        m = _make_membership(is_active=False)
        MockContract.objects.get.return_value = MagicMock(pk=1, title='X')
        MockMembership.objects.filter.return_value.select_related.return_value = [m]
        entry = self.svc.get_record_access(1, self.org)
        self.assertFalse(entry.users_with_access[0].is_active)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_admin_no_billing(self, MockMembership):
        m = _make_membership(role='ADMIN')
        MockMembership.objects.get.return_value = m
        access = self.svc.get_user_permissions(1, self.org)
        self.assertNotIn('manage_billing', access.capabilities)
        self.assertIn('view_audit', access.capabilities)

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_matrix_username_included(self, MockMembership):
        m = _make_membership(1, 'carol', 'OWNER')
        MockMembership.objects.filter.return_value.select_related.return_value.order_by.return_value = [m]
        matrix = self.svc.get_org_permission_matrix(self.org)
        self.assertEqual(matrix.users[0].username, 'carol')

    @patch('contracts.services.permissions.OrganizationMembership')
    def test_matrix_empty_org(self, MockMembership):
        MockMembership.objects.filter.return_value.select_related.return_value.order_by.return_value = []
        matrix = self.svc.get_org_permission_matrix(self.org)
        self.assertEqual(matrix.users, [])


if __name__ == '__main__':
    unittest.main()
