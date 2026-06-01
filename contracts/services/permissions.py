"""Permission transparency service — who can access what and why."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from contracts.models import Contract, Organization, OrganizationMembership

_MembershipDoesNotExist = OrganizationMembership.DoesNotExist


# Capability matrix per role
_ROLE_CAPABILITIES: dict[str, list[str]] = {
    'OWNER': [
        'view_contracts', 'create_contracts', 'edit_contracts', 'delete_contracts',
        'approve_contracts', 'manage_members', 'manage_policy', 'manage_integrations',
        'view_audit', 'export_data', 'manage_billing', 'manage_api_tokens',
    ],
    'ADMIN': [
        'view_contracts', 'create_contracts', 'edit_contracts', 'delete_contracts',
        'approve_contracts', 'manage_members', 'manage_policy',
        'view_audit', 'export_data', 'manage_api_tokens',
    ],
    'MEMBER': [
        'view_contracts', 'create_contracts', 'edit_contracts',
    ],
}


@dataclass
class UserAccess:
    user_id: int
    username: str
    role: str
    capabilities: list[str]
    is_active: bool


@dataclass
class ContractAccessEntry:
    contract_id: int
    contract_title: str
    users_with_access: list[UserAccess] = field(default_factory=list)


@dataclass
class OrgPermissionMatrix:
    org_id: int
    org_name: str
    users: list[UserAccess] = field(default_factory=list)


class PermissionTransparencyService:
    def get_record_access(self, contract_id: int, org: Organization) -> ContractAccessEntry:
        contract = Contract.objects.get(pk=contract_id, organization=org)
        memberships = OrganizationMembership.objects.filter(
            organization=org, is_active=True
        ).select_related('user')
        users = [_membership_to_access(m) for m in memberships]
        return ContractAccessEntry(
            contract_id=contract_id,
            contract_title=contract.title,
            users_with_access=users,
        )

    def get_user_permissions(self, user_id: int, org: Organization) -> Optional[UserAccess]:
        try:
            m = OrganizationMembership.objects.get(user_id=user_id, organization=org)
            return _membership_to_access(m)
        except _MembershipDoesNotExist:
            return None

    def get_org_permission_matrix(self, org: Organization) -> OrgPermissionMatrix:
        memberships = OrganizationMembership.objects.filter(
            organization=org
        ).select_related('user').order_by('role', 'user__username')
        return OrgPermissionMatrix(
            org_id=org.pk,
            org_name=org.name,
            users=[_membership_to_access(m) for m in memberships],
        )


def _membership_to_access(m: OrganizationMembership) -> UserAccess:
    caps = _ROLE_CAPABILITIES.get(m.role, _ROLE_CAPABILITIES['MEMBER'])
    return UserAccess(
        user_id=m.user_id,
        username=m.user.username,
        role=m.role,
        capabilities=caps,
        is_active=m.is_active,
    )


def get_permission_service() -> PermissionTransparencyService:
    return PermissionTransparencyService()
