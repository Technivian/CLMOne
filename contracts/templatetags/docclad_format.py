"""Shared human-readable formatting filters.

Consolidates the presentation rules that were previously duplicated (or
missing) in individual templates — currency, ISO datetime strings, enum-style
labels, audit event descriptions, and short durations. New templates should
use these instead of formatting values inline.
"""
import re
from decimal import Decimal, InvalidOperation

from django import template
from django.template.defaultfilters import date as date_filter
from django.utils.dateparse import parse_date, parse_datetime

register = template.Library()

_CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'CHF': 'Fr',
    'CAD': 'C$',
    'AUD': 'A$',
}

# Closed, stable set of model names this app writes to AuditLog.model_name —
# see contracts/middleware.py:log_action. Unknown values fall back to a
# generic PascalCase-to-words split so a new model never renders as raw
# CamelCase, even before this map is updated.
_OBJECT_TYPE_LABELS = {
    'ApprovalRequest': 'approval',
    'ClauseTemplate': 'clause template',
    'Client': 'client',
    'ConflictCheck': 'conflict check',
    'Contract': 'contract',
    'ContractAI': 'AI review',
    'Deadline': 'deadline',
    'Document': 'document',
    'DSARRequest': 'data subject request',
    'ESignEvent': 'signature event',
    'Invoice': 'invoice',
    'Matter': 'matter',
    'NegotiationThread': 'negotiation note',
    'Notification': 'notification',
    'Organization': 'organization',
    'OrganizationInvitation': 'team invitation',
    'OrganizationMembership': 'team membership',
    'OrganizationSCIMGroup': 'SCIM group',
    'RetentionExecution': 'retention run',
    'Session': 'session',
    'SignaturePacket': 'signature packet',
    'SignatureRequest': 'signature request',
    'TimeEntry': 'time entry',
    'TrustAccount': 'trust account',
    'TrustTransaction': 'trust transaction',
    'UserProfile': 'profile',
}

_ACRONYMS = {'ai', 'mfa', 'sso', 'saml', 'scim', 'dsar', 'api', 'id', 'url', 'crm', 'dpa', 'scc', 'ip'}
_PASCAL_SPLIT_RE = re.compile(r'(?<!^)(?=[A-Z])')


@register.filter
def money(value, currency='USD'):
    """125000 -> '$125,000.00'. Unparsable/empty values render as an em dash."""
    if value in (None, ''):
        return '—'
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return value
    symbol = _CURRENCY_SYMBOLS.get(currency, f'{currency} ')
    return f'{symbol}{amount:,.2f}'


@register.filter
def iso_datetime(value, fmt='M d, Y H:i'):
    """Format an ISO-8601 string OR a date/datetime object; passes through on failure."""
    if not value:
        return ''
    parsed = value
    if isinstance(value, str):
        parsed = parse_datetime(value) or parse_date(value)
        if not parsed:
            return value
    return date_filter(parsed, fmt)


@register.filter
def object_type_label(value):
    """'OrganizationMembership' -> 'team membership'; unmapped names get word-split."""
    if not value:
        return ''
    mapped = _OBJECT_TYPE_LABELS.get(value)
    if mapped:
        return mapped
    return _PASCAL_SPLIT_RE.sub(' ', value).lower()


@register.filter
def sort_label(value):
    """'-created_at' -> 'Created at ↓'; 'value' -> 'Value ↑'. Direction-agnostic
    (an arrow, not "newest"/"highest") since the same sort key can be a date,
    a number, or text depending on the field."""
    if not value:
        return ''
    descending = value.startswith('-')
    field = value[1:] if descending else value
    words = field.replace('_', ' ').split()
    label = ' '.join([words[0].capitalize()] + words[1:]) if words else field
    return f'{label} {"↓" if descending else "↑"}'


@register.filter
def event_label(value):
    """'contract_ai_assistant_invoked' -> 'Contract AI Assistant Invoked'."""
    if not value:
        return ''
    words = [w for w in re.split(r'[_.]+', str(value)) if w]
    return ' '.join(w.upper() if w.lower() in _ACRONYMS else w.capitalize() for w in words)


@register.filter
def humanduration(seconds):
    """787296 -> '9d 2h'. Machine-style second counts, made skimmable."""
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return seconds
    if seconds < 60:
        return f'{seconds}s'
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f'{minutes}m'
    hours, mins = divmod(minutes, 60)
    if hours < 24:
        return f'{hours}h {mins}m' if mins else f'{hours}h'
    days, hrs = divmod(hours, 24)
    return f'{days}d {hrs}h' if hrs else f'{days}d'
