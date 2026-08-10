"""Canonical controlled-pilot contract-type activation policy.

The ContractType catalogue describes valid governed classifications.  It does
not itself grant a type permission to enter the controlled PayrollMinds pilot.
This service is the single server-side launch eligibility boundary for that
pilot.  It deliberately does not participate in object-level read access:
PDR-0008 remains the authority once a Contract Record exists.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError


DEFAULT_CONTROLLED_PILOT_TYPES = frozenset({'MSA', 'NDA', 'DPA'})


class ContractTypeActivationError(ValidationError):
    """Raised when an inactive type is submitted to controlled-pilot intake."""


def normalize_contract_type(code: str | None) -> str:
    return (code or '').strip().upper()


def _valid_contract_type_codes() -> frozenset[str]:
    from contracts.models import Contract

    return frozenset(value for value, _label in Contract.ContractType.choices)


def controlled_pilot_activation_enabled() -> bool:
    return bool(getattr(settings, 'CONTROLLED_PILOT_ENABLED', False))


def configured_controlled_pilot_types() -> frozenset[str]:
    """Return the explicit, valid controlled-pilot launch cohort.

    The setting is intentionally an allowlist. Unknown values fail closed and
    a catalogue row becoming active never activates a launch path by itself.
    """
    configured = getattr(
        settings,
        'PAYROLLMINDS_ENABLED_CONTRACT_TYPES',
        DEFAULT_CONTROLLED_PILOT_TYPES,
    )
    if isinstance(configured, str):
        configured = configured.split(',')
    requested = {normalize_contract_type(value) for value in configured}
    return frozenset(requested.intersection(_valid_contract_type_codes()))


def active_contract_type_codes() -> frozenset[str]:
    """Return types eligible for creation in the current execution mode."""
    if not controlled_pilot_activation_enabled():
        return _valid_contract_type_codes()
    return configured_controlled_pilot_types()


def is_contract_type_activated(code: str | None) -> bool:
    return normalize_contract_type(code) in active_contract_type_codes()


def creation_form_choices(*, include_blank: bool = True) -> list[tuple[str, str]]:
    """Return catalogue choices filtered through the canonical launch policy."""
    from contracts.services.contract_type_catalogue import form_choices

    return [
        (code, label)
        for code, label in form_choices(include_blank=include_blank)
        if not code or code in active_contract_type_codes()
    ]


def require_contract_type_activation(code: str | None) -> str:
    """Return the normalized code or reject an inactive controlled-pilot type."""
    normalized = normalize_contract_type(code)
    if not normalized or not is_contract_type_activated(normalized):
        raise ContractTypeActivationError('This contract type is not enabled for controlled-pilot intake.')
    return normalized
