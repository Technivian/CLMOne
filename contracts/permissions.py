from django.contrib.auth import get_user_model

from .models import OrganizationMembership

User = get_user_model()


class ContractAction:
    VIEW = 'view'
    COMMENT = 'comment'
    AI = 'ai'
    EDIT = 'edit'


# Backward-compatible aliases for legacy care workflow call sites.
CaseAction = ContractAction


def get_active_org_membership(user, organization):
    if not user or not getattr(user, 'is_authenticated', False) or organization is None:
        return None
    return (
        OrganizationMembership.objects
        .filter(
            user=user,
            organization=organization,
            is_active=True,
            organization__is_active=True,
        )
        .first()
    )


def can_manage_organization(user, organization):
    membership = get_active_org_membership(user, organization)
    if membership is None:
        return False
    return membership.role in [OrganizationMembership.Role.OWNER, OrganizationMembership.Role.ADMIN]


def is_organization_owner(user, organization):
    membership = get_active_org_membership(user, organization)
    return bool(membership and membership.role == OrganizationMembership.Role.OWNER)


_ROLE_RANK = {
    OrganizationMembership.Role.MEMBER: 1,
    OrganizationMembership.Role.ADMIN: 2,
    OrganizationMembership.Role.OWNER: 3,
}


def organization_role_rank(role: str) -> int:
    return _ROLE_RANK.get(role, 0)


def can_assign_organization_role(actor_role: str, target_role: str) -> bool:
    """Actors may only grant roles at or below their own authority."""
    return organization_role_rank(actor_role) >= organization_role_rank(target_role) > 0


def assignable_organization_roles(actor_role: str) -> list[tuple[str, str]]:
    return [
        choice
        for choice in OrganizationMembership.Role.choices
        if can_assign_organization_role(actor_role, choice[0])
    ]


def can_access_contract_action(user, contract, action=ContractAction.VIEW):
    if contract is None:
        return False

    membership = get_active_org_membership(user, contract.organization)
    if membership is None:
        return False

    from contracts.models import Contract
    from contracts.services.object_read_policy import (
        ObjectReadPolicyUnavailable,
        filter_contract_security_queryset,
        filter_contract_queryset,
        is_workspace_privileged_editor,
    )

    try:
        visible = filter_contract_queryset(
            Contract.objects.filter(pk=contract.pk),
            organization=contract.organization,
            user=user,
            surface=f'contract_action_{action}',
        ).exists()
    except ObjectReadPolicyUnavailable:
        return False

    if action in [ContractAction.VIEW, ContractAction.COMMENT, ContractAction.AI]:
        # COMMENT and AI must never exceed the source contract read boundary.
        return visible

    if action == ContractAction.EDIT:
        # Preserve the existing all-record OWNER/ADMIN edit authority. For
        # ordinary members, either accountable principal may edit; do not let
        # a populated owner silently override a distinct creator.
        if is_workspace_privileged_editor(
            organization=contract.organization,
            user=user,
        ):
            # Privileged editors retain the approved edit-only authority.
            # The security query deliberately preserves Ethical-Wall and
            # active-membership enforcement; it does not grant read discovery.
            try:
                return filter_contract_security_queryset(
                    Contract.objects.filter(pk=contract.pk),
                    organization=contract.organization,
                    user=user,
                    surface='contract_action_edit',
                ).exists()
            except ObjectReadPolicyUnavailable:
                return False
        return visible and user.id in {contract.owner_id, contract.created_by_id}

    return False


def can_access_case_action(user, case, action=CaseAction.VIEW):
    return can_access_contract_action(user, case, action)
