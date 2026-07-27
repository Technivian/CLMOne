"""Server-side safeguards for the local, synthetic PayrollMinds presenter workspace."""

from contracts.models import OrgPolicy


PAYROLLMINDS_DEMO_WORKSPACE_SLUG = 'payrollminds-demo'
PRESENTER_READ_ONLY_MESSAGE = (
    'This synthetic PayrollMinds demo workspace is read-only during presentation.'
)


def is_payrollminds_presenter_workspace(organization) -> bool:
    """Return true only for the seeded demo workspace with AI explicitly disabled.

    The slug makes this an opt-in local demo guard; the policy check prevents an
    accidentally reconfigured workspace from receiving presentation-only limits.
    """
    if organization is None or organization.slug != PAYROLLMINDS_DEMO_WORKSPACE_SLUG:
        return False
    return OrgPolicy.objects.filter(
        organization=organization,
        ai_features_enabled=False,
    ).exists()
