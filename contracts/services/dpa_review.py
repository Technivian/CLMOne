"""Heuristic DPA analysis for the DPA Review Pack module.

This is a deterministic keyword/regex scanner over `contract.content` — not
an LLM call (see contracts/services/ai_extraction.py for the one real LLM
integration in this codebase, which extracts generic clause spans and
would need a live GEMINI_API_KEY; this module intentionally does not
depend on that, so DPA analysis works offline and is unit-testable).

`run_dpa_analysis()` populates the DPAReviewPack's checklist fields from
whatever it can detect in the DPA text and returns a list of suggested
DPARiskItem specs (dicts) for anything the checklist flags as a concern.
Nothing here writes a DPARiskItem or changes approval_status — the caller
(the view) persists the suggestions and a human decides what to do with
them. Detection that finds nothing leaves a field at its default (False /
blank) rather than guessing, matching the rest of this codebase's "no
invented data" rule.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from contracts.models import DPARiskItem


@dataclass
class RiskSuggestion:
    category: str
    title: str
    description: str
    severity: str
    owners: str  # comma-separated DPARiskItem.Owner codes
    fallback_recommendation: str = ''


# --- Section 3: payroll-specific data category keywords -------------------
PAYROLL_DATA_KEYWORDS = {
    'has_employee_identity_data': ['employee name', 'employee id', 'date of birth', 'employee identity'],
    'has_salary_wage_data': ['salary', 'wage', 'compensation amount', 'remuneration'],
    'has_tax_data': ['tax id', 'tax withholding', 'income tax', 'tax data'],
    'has_social_security_data': ['social security', 'national insurance number', 'ssn'],
    'has_bank_account_data': ['bank account', 'iban', 'account number', 'sort code'],
    'has_pension_benefits_data': ['pension', 'retirement benefit', 'benefits enrollment'],
    'has_absence_leave_data': ['sick leave', 'annual leave', 'absence record', 'time off'],
    'has_employment_contract_data': ['employment contract', 'employment agreement terms'],
    'has_national_identifiers': ['national identification number', 'passport number', 'national id'],
    'has_payroll_corrections': ['payroll correction', 'retroactive adjustment'],
    'has_payslip_data': ['payslip', 'pay stub'],
    'has_cross_border_payroll_data': ['cross-border payroll', 'international payroll', 'multi-country payroll'],
}

SECURITY_KEYWORDS = {
    'security_encryption': ['encrypt'],
    'security_access_control': ['access control', 'role-based access', 'least privilege'],
    'security_mfa': ['multi-factor authentication', 'multi factor authentication', ' mfa '],
    'security_logging': ['audit log', 'access log', 'logging of'],
    'security_backup': ['backup', 'back-up'],
    'security_incident_response': ['incident response'],
    'security_data_segregation': ['data segregation', 'logical separation', 'tenant isolation'],
}

NON_EEA_HINTS = [
    'outside the eea', 'outside the european economic area', 'outside the eu',
    'united states', 'india', 'philippines', 'united kingdom',
]
TRANSFER_MECHANISM_HINTS = ['standard contractual clauses', ' scc ', 'sccs', 'binding corporate rules', 'adequacy decision', 'data privacy framework']


def _contains_any(text_lower: str, keywords: list[str]) -> bool:
    return any(kw in text_lower for kw in keywords)


def _find_hours_deadline(text_lower: str, near_word: str) -> int | None:
    """Look for '<verb> ... within N hours/days [of/after <near_word>]' style
    language. Returns hours (days converted x24), or None if not found."""
    pattern = re.compile(r'within\s+(\d+)\s*(hour|day)s?', re.IGNORECASE)
    best = None
    for match in pattern.finditer(text_lower):
        window = text_lower[max(0, match.start() - 200):match.end() + 200]
        if near_word in window:
            amount = int(match.group(1))
            hours = amount * 24 if match.group(2).lower() == 'day' else amount
            if best is None or hours < best:
                best = hours
    return best


def _find_days_deadline(text_lower: str, near_word: str) -> int | None:
    pattern = re.compile(r'(\d+)\s*days?', re.IGNORECASE)
    best = None
    for match in pattern.finditer(text_lower):
        window = text_lower[max(0, match.start() - 150):match.end() + 150]
        if near_word in window:
            days = int(match.group(1))
            if best is None or days < best:
                best = days
    return best


def run_dpa_analysis(review_pack) -> list[RiskSuggestion]:
    """Scan review_pack.contract.content and update the checklist fields on
    review_pack in place (caller must .save()). Returns suggested risks —
    the caller decides whether/how to persist them as DPARiskItem rows."""
    text = review_pack.contract.content or ''
    # Collapse whitespace (including line wraps) before matching — real
    # contract text wraps unpredictably, and a phrase split across a line
    # break (e.g. "prior written\napproval") must still match "prior
    # written approval" as a single keyword.
    text_lower = re.sub(r'\s+', ' ', text.lower())
    suggestions: list[RiskSuggestion] = []

    # 1. Role qualification
    has_controller = 'client is the controller' in text_lower or 'client acts as controller' in text_lower or 'data controller' in text_lower
    has_processor = 'payrollminds is the processor' in text_lower or 'acting as processor' in text_lower or 'processor shall' in text_lower
    has_joint = 'joint controller' in text_lower or 'joint control' in text_lower
    has_independent = 'independent controller' in text_lower
    review_pack.subprocessors_involved = 'subprocessor' in text_lower

    if has_joint:
        review_pack.role_qualification = review_pack.RoleQualification.JOINT_CONTROLLER
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Joint-controller language found',
            description='The DPA text includes joint-controller language. Confirm this is intended — a payroll processor arrangement is normally sole controller/processor, and joint control shifts liability and notice obligations onto Payrollminds.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL',
            fallback_recommendation='Replace joint-controller wording with standard controller (client) / processor (Payrollminds) roles.',
        ))
    elif has_independent:
        review_pack.role_qualification = review_pack.RoleQualification.INDEPENDENT_CONTROLLER
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Independent-controller language found',
            description='The DPA suggests Payrollminds may act as an independent controller for some processing, which is inconsistent with a payroll-processing engagement.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL',
        ))
    elif has_controller and has_processor:
        review_pack.role_qualification = review_pack.RoleQualification.CONTROLLER_PROCESSOR
    else:
        review_pack.role_qualification = review_pack.RoleQualification.AMBIGUOUS
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Role qualification unclear',
            description='The DPA does not clearly state that the client is controller and Payrollminds is processor.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL',
            fallback_recommendation='Add explicit role wording: "Client is Controller; Payrollminds is Processor with respect to Personal Data processed under this DPA."',
        ))

    # 3. Payroll-specific data categories
    for field_name, keywords in PAYROLL_DATA_KEYWORDS.items():
        setattr(review_pack, field_name, _contains_any(text_lower, keywords))
    sensitive_fields = ['has_tax_data', 'has_social_security_data', 'has_bank_account_data', 'has_national_identifiers']
    if any(getattr(review_pack, f) for f in sensitive_fields) and not _contains_any(text_lower, ['heightened', 'additional safeguard', 'enhanced security']):
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.PROCESSING_SCOPE,
            title='Sensitive payroll data without heightened safeguards language',
            description='Tax, social security, bank account, or national identifier data is referenced, but no heightened/enhanced safeguard language was found nearby.',
            severity=DPARiskItem.Severity.HIGH, owners='DPO_SECURITY',
            fallback_recommendation='Request explicit heightened technical/organizational measures for financial and government-ID payroll data categories.',
        ))

    # 4. Subprocessor / vendor review
    review_pack.subprocessor_prior_approval_required = 'prior written approval' in text_lower or 'prior written consent' in text_lower
    review_pack.subprocessor_general_authorization_allowed = 'general authorization' in text_lower or 'general written authorization' in text_lower
    notice_days = _find_days_deadline(text_lower, 'subprocessor')
    review_pack.subprocessor_notification_period_days = notice_days
    if review_pack.subprocessor_prior_approval_required and review_pack.subprocessor_general_authorization_allowed:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.SUBPROCESSOR,
            title='Contradictory subprocessor authorization model',
            description='The DPA references both prior-approval and general-authorization subprocessor models, which conflict — Payrollminds’ delivery model (adding subprocessors without per-instance client sign-off) needs one clear model.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL',
            fallback_recommendation='Adopt general authorization with a fixed notice period (e.g. 30 days) and a client objection right, not case-by-case prior approval.',
        ))
    elif review_pack.subprocessor_general_authorization_allowed and notice_days is None:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.SUBPROCESSOR,
            title='General authorization without a notification period',
            description='General subprocessor authorization is present but no notice period before adding a new subprocessor was found.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL',
        ))

    # 5. International transfer review
    review_pack.transfers_outside_eea = _contains_any(text_lower, NON_EEA_HINTS)
    review_pack.transfer_mechanism_present = _contains_any(text_lower, TRANSFER_MECHANISM_HINTS)
    if review_pack.transfers_outside_eea and not review_pack.transfer_mechanism_present:
        review_pack.transfer_escalation_required = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.TRANSFER,
            title='Cross-border transfer without an identified transfer mechanism',
            description='The DPA references processing or access outside the EEA, but no SCCs, adequacy decision, or other transfer safeguard was found.',
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL,DPO_SECURITY',
            fallback_recommendation='Add Standard Contractual Clauses (or confirm an adequacy decision) covering the non-EEA processing location before signature.',
        ))
    elif review_pack.transfers_outside_eea:
        review_pack.transfer_escalation_required = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.TRANSFER,
            title='Cross-border transfer detected — DPO escalation recommended',
            description='A transfer mechanism is referenced, but any non-EEA payroll processing should still be reviewed by DPO/Security for a Transfer Impact Assessment.',
            severity=DPARiskItem.Severity.MEDIUM, owners='DPO_SECURITY',
        ))

    # 6. Security measures review
    hits = 0
    for field_name, keywords in SECURITY_KEYWORDS.items():
        found = _contains_any(text_lower, keywords)
        setattr(review_pack, field_name, found)
        hits += int(found)
    review_pack.security_measures_specific = hits >= 3
    if not review_pack.security_measures_specific:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.SECURITY,
            title='Security measures described in vague or generic terms',
            description=f'Only {hits} of {len(SECURITY_KEYWORDS)} concrete security measure categories (encryption, access control, MFA, logging, backup, incident response, segregation) were found in the DPA text.',
            severity=DPARiskItem.Severity.MEDIUM, owners='DPO_SECURITY',
            fallback_recommendation='Request an Annex/Schedule listing concrete technical and organizational measures rather than generic "appropriate security" language.',
        ))

    # 7. Breach notification review
    breach_hours = _find_hours_deadline(text_lower, 'breach')
    review_pack.breach_notification_deadline_hours = breach_hours
    if breach_hours is not None and breach_hours <= 24:
        review_pack.breach_notification_realistic = False
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.BREACH_NOTIFICATION,
            title=f'Breach notification deadline of {breach_hours} hours may be unrealistic',
            description='A very short notification window creates operational risk if incident triage genuinely needs longer to confirm scope.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL,BUSINESS',
            fallback_recommendation='Propose "without undue delay and in any event within 72 hours of becoming aware" (GDPR-aligned) instead of a same-day deadline.',
        ))
    elif breach_hours is None:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.BREACH_NOTIFICATION,
            title='No clear breach notification deadline found',
            description='The DPA does not specify a clear breach notification deadline.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL',
        ))
    else:
        review_pack.breach_notification_realistic = True

    # 8. Data subject request assistance
    review_pack.dsar_assistance_required = 'data subject request' in text_lower and 'assist' in text_lower
    review_pack.dsar_assistance_deadline_days = _find_days_deadline(text_lower, 'data subject request')
    review_pack.dsar_assistance_chargeable = _contains_any(text_lower, ['reasonable costs', 'chargeable', 'additional fee']) and 'at its own cost' not in text_lower and 'no additional fee' not in text_lower
    review_pack.dsar_business_confirmation_needed = review_pack.dsar_assistance_required
    if review_pack.dsar_assistance_chargeable:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.DSAR,
            title='DSAR assistance may be chargeable',
            description='The DPA suggests Payrollminds may charge for data subject request assistance rather than including it in standard fees.',
            severity=DPARiskItem.Severity.MEDIUM, owners='BUSINESS,FINANCE',
            fallback_recommendation='Confirm with Business/Finance whether DSAR assistance is priced into the engagement before accepting chargeable language.',
        ))

    # 9. Audit rights
    review_pack.audit_rights_onsite_allowed = _contains_any(text_lower, ['on-site audit', 'on site audit', 'on-premises audit'])
    review_pack.audit_rights_frequency_limited = _contains_any(text_lower, ['once per year', 'once annually', 'no more than once'])
    review_pack.audit_third_party_reports_accepted = _contains_any(text_lower, ['third-party audit report', 'soc 2', 'iso 27001'])
    review_pack.audit_costs_addressed = _contains_any(text_lower, ['audit costs', 'cost of the audit', 'client shall bear'])
    if review_pack.audit_rights_onsite_allowed:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.AUDIT,
            title='On-site audit rights requested',
            description='The DPA allows on-site audits, which carries a real operational burden for a payroll processor handling many clients.',
            severity=DPARiskItem.Severity.MEDIUM, owners='DELIVERY,DPO_SECURITY',
            fallback_recommendation='Offer third-party certification (SOC 2 / ISO 27001) reports in lieu of on-site audits where possible, with on-site limited to once per year and reasonable notice.',
        ))
    if not review_pack.audit_rights_frequency_limited:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.AUDIT,
            title='Audit frequency not limited',
            description='No language limiting audit frequency (e.g. "once per year") was found — this creates unbounded audit exposure.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL',
        ))

    # 10. Deletion and return
    review_pack.deletion_return_deadline_days = _find_days_deadline(text_lower, 'deletion') or _find_days_deadline(text_lower, 'return')
    review_pack.deletion_certification_required = _contains_any(text_lower, ['certificate of deletion', 'certification of deletion'])
    review_pack.deletion_backup_addressed = 'backup' in text_lower and ('delet' in text_lower or 'purge' in text_lower)
    if review_pack.deletion_return_deadline_days is not None and review_pack.deletion_return_deadline_days <= 30 and _contains_any(text_lower, ['statutory retention', 'tax retention', 'payroll records must be retained']):
        review_pack.deletion_legal_retention_conflict = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.DELETION,
            title='Deletion deadline may conflict with statutory payroll/tax retention',
            description=f'A {review_pack.deletion_return_deadline_days}-day deletion deadline was found alongside statutory retention language — payroll/tax records often must be retained for years by law.',
            severity=DPARiskItem.Severity.HIGH, owners='DELIVERY,LEGAL',
            fallback_recommendation='Carve out data Payrollminds is required to retain under applicable tax/employment law from the deletion deadline.',
        ))

    # 11. Liability conflict detection
    review_pack.liability_uncapped = _contains_any(text_lower, ['uncapped', 'unlimited liability', 'no limitation of liability'])
    review_pack.liability_overrides_msa_cap = _contains_any(text_lower, ['notwithstanding the limitation of liability', 'notwithstanding any limitation of liability', 'notwithstanding any other provision of the agreement'])
    review_pack.liability_separate_indemnities = 'indemnif' in text_lower
    if review_pack.liability_uncapped:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='DPA introduces uncapped liability',
            description='The DPA contains uncapped/unlimited liability language, which conflicts with Payrollminds’ standard liability position.',
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL',
            fallback_recommendation='Align DPA liability with the MSA’s liability cap, or negotiate a specific (not unlimited) enhanced cap for data breach liability only.',
        ))
    if review_pack.liability_overrides_msa_cap:
        review_pack.liability_conflicts_standard_position = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='DPA overrides the MSA liability cap',
            description='"Notwithstanding" language suggests the DPA is designed to override the MSA’s limitation of liability.',
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL',
        ))
    if review_pack.liability_separate_indemnities:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='Separate indemnity language found',
            description='The DPA includes indemnity language distinct from the MSA — confirm it does not duplicate or conflict with MSA indemnities.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL',
        ))

    return suggestions
