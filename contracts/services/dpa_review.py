"""Heuristic DPA analysis for the DPA Review Pack module.

This is a deterministic keyword/regex scanner over `contract.content` — not
an LLM call (see contracts/services/ai_extraction.py for the one real LLM
integration in this codebase, which extracts generic clause spans and
would need a live GEMINI_API_KEY; this module intentionally does not
depend on that, so DPA analysis works offline and is unit-testable).

`run_dpa_analysis()` populates the DPAReviewPack's checklist fields from
whatever it can detect in the DPA text and returns a list of suggested
DPARiskItem specs (RiskSuggestion) for anything the checklist flags as a
concern. Nothing here writes a DPARiskItem or changes approval_status —
the caller (the view) persists the suggestions and a human decides what to
do with them. Detection that finds nothing leaves a field at its default
(False / blank) rather than guessing, matching the rest of this codebase's
"no invented data" rule.

Each RiskSuggestion carries an `evidence` snippet (the actual matched text,
not just a description of what was found) and a `confidence` level — a
direct phrase match ("uncapped", "joint controller") is HIGH confidence;
an inference from the *absence* of expected language is lower confidence,
since absence-of-evidence is weaker evidence than a positive match.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from contracts.models import DPARiskItem

_SNIPPET_WINDOW = 90
MANUAL_EVIDENCE = 'Evidence requires manual verification'


@dataclass
class RiskSuggestion:
    category: str
    title: str
    description: str
    severity: str
    owners: str  # comma-separated DPARiskItem.Owner codes
    fallback_recommendation: str = ''
    evidence_text: str = ''
    source_section: str = ''
    source_field: str = ''
    detection_rule: str = ''
    confidence: str = DPARiskItem.Confidence.MEDIUM
    conflict_type: str = ''
    related_contract_evidence_text: str = ''
    is_cross_document_conflict: bool = False

    def __post_init__(self):
        if not self.evidence_text:
            self.evidence_text = MANUAL_EVIDENCE


def normalize(text: str) -> str:
    """Collapse whitespace (including line wraps) and lowercase — real
    contract text wraps unpredictably, and a phrase split across a line
    break (e.g. "prior written\\napproval") must still match "prior
    written approval" as a single keyword."""
    return re.sub(r'\s+', ' ', (text or '').lower())


def snippet_for(text_lower: str, needle: str, window: int = _SNIPPET_WINDOW) -> str:
    """First-occurrence evidence snippet for *needle* within *text_lower*,
    trimmed to a readable window and sentence-cased. Returns '' if not
    found — callers should not claim evidence they don't have."""
    idx = text_lower.find(needle)
    if idx == -1:
        return ''
    start = max(0, idx - window)
    end = min(len(text_lower), idx + len(needle) + window)
    excerpt = text_lower[start:end].strip()
    if start > 0:
        excerpt = f'…{excerpt}'
    if end < len(text_lower):
        excerpt = f'{excerpt}…'
    return excerpt[0].upper() + excerpt[1:] if excerpt else excerpt


def snippet_for_any(text_lower: str, keywords: list[str], window: int = _SNIPPET_WINDOW) -> str:
    for kw in keywords:
        found = snippet_for(text_lower, kw, window)
        if found:
            return found
    return ''


def snippet_for_match(text_lower: str, match: re.Match, window: int = _SNIPPET_WINDOW) -> str:
    start = max(0, match.start() - window)
    end = min(len(text_lower), match.end() + window)
    excerpt = text_lower[start:end].strip()
    if start > 0:
        excerpt = f'…{excerpt}'
    if end < len(text_lower):
        excerpt = f'{excerpt}…'
    return excerpt[0].upper() + excerpt[1:] if excerpt else excerpt


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


def _find_hours_deadline(text_lower: str, near_word: str) -> tuple[int | None, str]:
    """Look for 'within N hours/days [of/after <near_word>]' style
    language. Returns (hours, evidence_snippet) — hours is None if not
    found. Days are converted to hours (x24)."""
    pattern = re.compile(r'within\s+(\d+)\s*(hour|day)s?', re.IGNORECASE)
    best, best_match = None, None
    for match in pattern.finditer(text_lower):
        window = text_lower[max(0, match.start() - 200):match.end() + 200]
        if near_word in window:
            amount = int(match.group(1))
            hours = amount * 24 if match.group(2).lower() == 'day' else amount
            if best is None or hours < best:
                best, best_match = hours, match
    if best_match is None:
        return None, ''
    return best, snippet_for_match(text_lower, best_match)


def _find_days_deadline(text_lower: str, near_word: str) -> tuple[int | None, str]:
    pattern = re.compile(r'(\d+)\s*days?', re.IGNORECASE)
    best, best_match = None, None
    for match in pattern.finditer(text_lower):
        window = text_lower[max(0, match.start() - 150):match.end() + 150]
        if near_word in window:
            days = int(match.group(1))
            if best is None or days < best:
                best, best_match = days, match
    if best_match is None:
        return None, ''
    return best, snippet_for_match(text_lower, best_match)


def run_dpa_analysis(review_pack) -> list[RiskSuggestion]:
    """Scan review_pack.contract.content and update the checklist fields on
    review_pack in place (caller must .save()). Returns suggested risks —
    the caller decides whether/how to persist them as DPARiskItem rows."""
    text_lower = normalize(review_pack.contract.content or '')
    suggestions: list[RiskSuggestion] = []

    # 1. Role qualification
    controller_kws = ['client is the controller', 'client acts as controller', 'data controller']
    processor_kws = ['payrollminds is the processor', 'acting as processor', 'processor shall']
    has_controller = _contains_any(text_lower, controller_kws)
    has_processor = _contains_any(text_lower, processor_kws)
    has_joint = _contains_any(text_lower, ['joint controller', 'joint control'])
    has_independent = 'independent controller' in text_lower
    review_pack.subprocessors_involved = 'subprocessor' in text_lower

    if has_joint:
        review_pack.role_qualification = review_pack.RoleQualification.JOINT_CONTROLLER
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Joint-controller language found',
            description='The DPA text includes joint-controller language. Confirm this is intended — a payroll processor arrangement is normally sole controller/processor, and joint control shifts liability and notice obligations onto Payrollminds.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Role Qualification', source_field='role_qualification', detection_rule='role_joint_controller',
            evidence_text=snippet_for_any(text_lower, ['joint controller', 'joint control']),
            fallback_recommendation='Replace joint-controller wording with standard controller (client) / processor (Payrollminds) roles.',
        ))
    elif has_independent:
        review_pack.role_qualification = review_pack.RoleQualification.INDEPENDENT_CONTROLLER
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Independent-controller language found',
            description='The DPA suggests Payrollminds may act as an independent controller for some processing, which is inconsistent with a payroll-processing engagement.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Role Qualification', source_field='role_qualification', detection_rule='role_independent_controller',
            evidence_text=snippet_for(text_lower, 'independent controller'),
        ))
    elif has_controller and has_processor:
        review_pack.role_qualification = review_pack.RoleQualification.CONTROLLER_PROCESSOR
    else:
        review_pack.role_qualification = review_pack.RoleQualification.AMBIGUOUS
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.ROLE_QUALIFICATION,
            title='Role qualification unclear',
            description='The DPA does not clearly state that the client is controller and Payrollminds is processor.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL', confidence=DPARiskItem.Confidence.NEEDS_HUMAN_CHECK,
            source_section='Role Qualification', source_field='role_qualification', detection_rule='role_ambiguous_missing_controller_processor',
            fallback_recommendation='Add explicit role wording: "Client is Controller; Payrollminds is Processor with respect to Personal Data processed under this DPA."',
        ))

    # 3. Payroll-specific data categories
    for field_name, keywords in PAYROLL_DATA_KEYWORDS.items():
        setattr(review_pack, field_name, _contains_any(text_lower, keywords))
    sensitive_fields = ['has_tax_data', 'has_social_security_data', 'has_bank_account_data', 'has_national_identifiers']
    sensitive_keywords = {
        'has_tax_data': PAYROLL_DATA_KEYWORDS['has_tax_data'],
        'has_social_security_data': PAYROLL_DATA_KEYWORDS['has_social_security_data'],
        'has_bank_account_data': PAYROLL_DATA_KEYWORDS['has_bank_account_data'],
        'has_national_identifiers': PAYROLL_DATA_KEYWORDS['has_national_identifiers'],
    }
    if any(getattr(review_pack, f) for f in sensitive_fields) and not _contains_any(text_lower, ['heightened', 'additional safeguard', 'enhanced security']):
        hit_field = next(f for f in sensitive_fields if getattr(review_pack, f))
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.PROCESSING_SCOPE,
            title='Sensitive payroll data without heightened safeguards language',
            description='Tax, social security, bank account, or national identifier data is referenced, but no heightened/enhanced safeguard language was found nearby.',
            severity=DPARiskItem.Severity.HIGH, owners='DPO_SECURITY', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='Processing Scope', source_field=hit_field, detection_rule='sensitive_payroll_data_without_heightened_safeguards',
            evidence_text=snippet_for_any(text_lower, sensitive_keywords[hit_field]),
            fallback_recommendation='Request explicit heightened technical/organizational measures for financial and government-ID payroll data categories.',
        ))

    # 4. Subprocessor / vendor review
    review_pack.subprocessor_prior_approval_required = 'prior written approval' in text_lower or 'prior written consent' in text_lower
    review_pack.subprocessor_general_authorization_allowed = 'general authorization' in text_lower or 'general written authorization' in text_lower
    notice_days, notice_evidence = _find_days_deadline(text_lower, 'subprocessor')
    review_pack.subprocessor_notification_period_days = notice_days
    if review_pack.subprocessor_prior_approval_required and review_pack.subprocessor_general_authorization_allowed:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.SUBPROCESSOR,
            title='Contradictory subprocessor authorization model',
            description='The DPA references both prior-approval and general-authorization subprocessor models, which conflict — Payrollminds’ delivery model (adding subprocessors without per-instance client sign-off) needs one clear model.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Subprocessors', source_field='subprocessor_prior_approval_required', detection_rule='subprocessor_prior_approval_and_general_authorization',
            evidence_text=snippet_for_any(text_lower, ['prior written approval', 'prior written consent']),
            fallback_recommendation='Adopt general authorization with a fixed notice period (e.g. 30 days) and a client objection right, not case-by-case prior approval.',
        ))
    elif review_pack.subprocessor_general_authorization_allowed and notice_days is None:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.SUBPROCESSOR,
            title='General authorization without a notification period',
            description='General subprocessor authorization is present but no notice period before adding a new subprocessor was found.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='Subprocessors', source_field='subprocessor_notification_period_days', detection_rule='subprocessor_general_authorization_missing_notice_period',
            evidence_text=snippet_for_any(text_lower, ['general authorization', 'general written authorization']),
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
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL,DPO_SECURITY', confidence=DPARiskItem.Confidence.HIGH,
            source_section='International Transfers', source_field='transfer_mechanism_present', detection_rule='non_eea_transfer_missing_mechanism',
            evidence_text=snippet_for_any(text_lower, NON_EEA_HINTS),
            fallback_recommendation='Add Standard Contractual Clauses (or confirm an adequacy decision) covering the non-EEA processing location before signature.',
        ))
    elif review_pack.transfers_outside_eea:
        review_pack.transfer_escalation_required = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.TRANSFER,
            title='Cross-border transfer detected — DPO escalation recommended',
            description='A transfer mechanism is referenced, but any non-EEA payroll processing should still be reviewed by DPO/Security for a Transfer Impact Assessment.',
            severity=DPARiskItem.Severity.MEDIUM, owners='DPO_SECURITY', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='International Transfers', source_field='transfers_outside_eea', detection_rule='non_eea_transfer_detected',
            evidence_text=snippet_for_any(text_lower, NON_EEA_HINTS),
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
            severity=DPARiskItem.Severity.MEDIUM, owners='DPO_SECURITY', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='Security Measures', source_field='security_measures_specific', detection_rule='security_measures_vague_or_incomplete',
            fallback_recommendation='Request an Annex/Schedule listing concrete technical and organizational measures rather than generic "appropriate security" language.',
        ))

    # 7. Breach notification review
    breach_hours, breach_evidence = _find_hours_deadline(text_lower, 'breach')
    review_pack.breach_notification_deadline_hours = breach_hours
    if breach_hours is not None and breach_hours <= 24:
        review_pack.breach_notification_realistic = False
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.BREACH_NOTIFICATION,
            title=f'Breach notification deadline of {breach_hours} hours may be unrealistic',
            description='A very short notification window creates operational risk if incident triage genuinely needs longer to confirm scope.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL,BUSINESS', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Breach Notification', source_field='breach_notification_deadline_hours', detection_rule='breach_notification_short_deadline',
            evidence_text=breach_evidence,
            fallback_recommendation='Propose "without undue delay and in any event within 72 hours of becoming aware" (GDPR-aligned) instead of a same-day deadline.',
        ))
    elif breach_hours is None:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.BREACH_NOTIFICATION,
            title='No clear breach notification deadline found',
            description='The DPA does not specify a clear breach notification deadline.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL', confidence=DPARiskItem.Confidence.NEEDS_HUMAN_CHECK,
            source_section='Breach Notification', source_field='breach_notification_deadline_hours', detection_rule='breach_notification_deadline_missing',
        ))
    else:
        review_pack.breach_notification_realistic = True

    # 8. Data subject request assistance
    review_pack.dsar_assistance_required = 'data subject request' in text_lower and 'assist' in text_lower
    dsar_days, dsar_days_evidence = _find_days_deadline(text_lower, 'data subject request')
    review_pack.dsar_assistance_deadline_days = dsar_days
    chargeable_kws = ['reasonable costs', 'chargeable', 'additional fee']
    review_pack.dsar_assistance_chargeable = _contains_any(text_lower, chargeable_kws) and 'at its own cost' not in text_lower and 'no additional fee' not in text_lower
    review_pack.dsar_business_confirmation_needed = review_pack.dsar_assistance_required
    if review_pack.dsar_assistance_chargeable:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.DSAR,
            title='DSAR assistance may be chargeable',
            description='The DPA suggests Payrollminds may charge for data subject request assistance rather than including it in standard fees.',
            severity=DPARiskItem.Severity.MEDIUM, owners='BUSINESS,FINANCE', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='DSAR Assistance', source_field='dsar_assistance_chargeable', detection_rule='dsar_assistance_chargeable',
            evidence_text=snippet_for_any(text_lower, chargeable_kws),
            fallback_recommendation='Confirm with Business/Finance whether DSAR assistance is priced into the engagement before accepting chargeable language.',
        ))

    # 9. Audit rights
    onsite_kws = ['on-site audit', 'on site audit', 'on-premises audit']
    review_pack.audit_rights_onsite_allowed = _contains_any(text_lower, onsite_kws)
    review_pack.audit_rights_frequency_limited = _contains_any(text_lower, ['once per year', 'once annually', 'no more than once'])
    review_pack.audit_third_party_reports_accepted = _contains_any(text_lower, ['third-party audit report', 'soc 2', 'iso 27001'])
    review_pack.audit_costs_addressed = _contains_any(text_lower, ['audit costs', 'cost of the audit', 'client shall bear'])
    if review_pack.audit_rights_onsite_allowed:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.AUDIT,
            title='On-site audit rights requested',
            description='The DPA allows on-site audits, which carries a real operational burden for a payroll processor handling many clients.',
            severity=DPARiskItem.Severity.MEDIUM, owners='DELIVERY,DPO_SECURITY', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Audit Rights', source_field='audit_rights_onsite_allowed', detection_rule='audit_rights_onsite_allowed',
            evidence_text=snippet_for_any(text_lower, onsite_kws),
            fallback_recommendation='Offer third-party certification (SOC 2 / ISO 27001) reports in lieu of on-site audits where possible, with on-site limited to once per year and reasonable notice.',
        ))
    if not review_pack.audit_rights_frequency_limited:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.AUDIT,
            title='Audit frequency not limited',
            description='No language limiting audit frequency (e.g. "once per year") was found — this creates unbounded audit exposure.',
            severity=DPARiskItem.Severity.MEDIUM, owners='LEGAL', confidence=DPARiskItem.Confidence.NEEDS_HUMAN_CHECK,
            source_section='Audit Rights', source_field='audit_rights_frequency_limited', detection_rule='audit_frequency_not_limited',
        ))

    # 10. Deletion and return
    deletion_days, deletion_evidence = _find_days_deadline(text_lower, 'deletion')
    if deletion_days is None:
        deletion_days, deletion_evidence = _find_days_deadline(text_lower, 'return')
    review_pack.deletion_return_deadline_days = deletion_days
    review_pack.deletion_certification_required = _contains_any(text_lower, ['certificate of deletion', 'certification of deletion'])
    review_pack.deletion_backup_addressed = 'backup' in text_lower and ('delet' in text_lower or 'purge' in text_lower)
    retention_kws = ['statutory retention', 'tax retention', 'payroll records must be retained']
    if review_pack.deletion_return_deadline_days is not None and review_pack.deletion_return_deadline_days <= 30 and _contains_any(text_lower, retention_kws):
        review_pack.deletion_legal_retention_conflict = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.DELETION,
            title='Deletion deadline may conflict with statutory payroll/tax retention',
            description=f'A {review_pack.deletion_return_deadline_days}-day deletion deadline was found alongside statutory retention language — payroll/tax records often must be retained for years by law.',
            severity=DPARiskItem.Severity.HIGH, owners='DELIVERY,LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Deletion and Return', source_field='deletion_return_deadline_days', detection_rule='deletion_deadline_statutory_retention_conflict',
            evidence_text=f'{deletion_evidence} … {snippet_for_any(text_lower, retention_kws)}',
            fallback_recommendation='Carve out data Payrollminds is required to retain under applicable tax/employment law from the deletion deadline.',
        ))

    # 11. Liability conflict detection
    uncapped_kws = ['uncapped', 'unlimited liability', 'no limitation of liability']
    override_kws = ['notwithstanding the limitation of liability', 'notwithstanding any limitation of liability', 'notwithstanding any other provision of the agreement']
    review_pack.liability_uncapped = _contains_any(text_lower, uncapped_kws)
    review_pack.liability_overrides_msa_cap = _contains_any(text_lower, override_kws)
    review_pack.liability_separate_indemnities = 'indemnif' in text_lower
    if review_pack.liability_uncapped:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='DPA introduces uncapped liability',
            description='The DPA contains uncapped/unlimited liability language, which conflicts with Payrollminds’ standard liability position.',
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Liability', source_field='liability_uncapped', detection_rule='dpa_uncapped_liability',
            evidence_text=snippet_for_any(text_lower, uncapped_kws),
            fallback_recommendation='Align DPA liability with the MSA’s liability cap, or negotiate a specific (not unlimited) enhanced cap for data breach liability only.',
        ))
    if review_pack.liability_overrides_msa_cap:
        review_pack.liability_conflicts_standard_position = True
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='DPA overrides the MSA liability cap',
            description='"Notwithstanding" language suggests the DPA is designed to override the MSA’s limitation of liability.',
            severity=DPARiskItem.Severity.CRITICAL, owners='LEGAL', confidence=DPARiskItem.Confidence.HIGH,
            source_section='Liability', source_field='liability_overrides_msa_cap', detection_rule='dpa_overrides_msa_cap',
            evidence_text=snippet_for_any(text_lower, override_kws),
        ))
    if review_pack.liability_separate_indemnities:
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title='Separate indemnity language found',
            description='The DPA includes indemnity language distinct from the MSA — confirm it does not duplicate or conflict with MSA indemnities.',
            severity=DPARiskItem.Severity.HIGH, owners='LEGAL', confidence=DPARiskItem.Confidence.MEDIUM,
            source_section='Liability', source_field='liability_separate_indemnities', detection_rule='dpa_separate_indemnity',
            evidence_text=snippet_for(text_lower, 'indemnif'),
        ))

    return suggestions


def generate_review_memo(review_pack) -> str:
    """Compose a structured, human-readable review memo from the review
    pack's current checklist fields, linked contracts, and risk items.
    Does not run analysis — call run_dpa_analysis first if a fresh scan is
    wanted. Purely a summarization/formatting step; it does not decide
    anything the reviewer hasn't already recorded."""
    lines: list[str] = []
    lines.append(f'DPA REVIEW MEMO — {review_pack.contract.title}')
    if review_pack.counterparty:
        lines.append(f'Counterparty: {review_pack.counterparty.name}')
    lines.append(f'Approval status: {review_pack.get_approval_status_display()}')
    lines.append('')

    lines.append('1. ROLE QUALIFICATION')
    lines.append(f'  {review_pack.get_role_qualification_display()}')
    if review_pack.role_qualification_notes:
        lines.append(f'  Notes: {review_pack.role_qualification_notes}')
    lines.append('')

    payroll_fields = [
        ('Employee identity data', review_pack.has_employee_identity_data),
        ('Salary / wage data', review_pack.has_salary_wage_data),
        ('Tax data', review_pack.has_tax_data),
        ('Social security data', review_pack.has_social_security_data),
        ('Bank account details', review_pack.has_bank_account_data),
        ('Pension / benefits data', review_pack.has_pension_benefits_data),
        ('Absence / leave data', review_pack.has_absence_leave_data),
        ('Employment contract data', review_pack.has_employment_contract_data),
        ('National identifiers', review_pack.has_national_identifiers),
        ('Payroll corrections', review_pack.has_payroll_corrections),
        ('Payslip data', review_pack.has_payslip_data),
        ('Cross-border payroll data', review_pack.has_cross_border_payroll_data),
    ]
    lines.append('2-3. PROCESSING SCOPE / PAYROLL DATA CATEGORIES')
    lines.append('  Present: ' + (', '.join(label for label, present in payroll_fields if present) or 'None detected'))
    lines.append('')

    lines.append('4. SUBPROCESSOR / VENDOR REVIEW')
    lines.append(f'  Prior approval required: {review_pack.subprocessor_prior_approval_required}; General authorization allowed: {review_pack.subprocessor_general_authorization_allowed}; Notice period: {review_pack.subprocessor_notification_period_days or "not specified"} days')
    lines.append('')

    lines.append('5. INTERNATIONAL TRANSFER REVIEW')
    lines.append(f'  Transfers outside EEA: {review_pack.transfers_outside_eea}; Transfer mechanism present: {review_pack.transfer_mechanism_present}; DPO/Security escalation required: {review_pack.transfer_escalation_required}')
    lines.append('')

    lines.append('6. SECURITY MEASURES')
    lines.append(f'  Measures specific (not vague): {review_pack.security_measures_specific}')
    lines.append('')

    lines.append('7. BREACH NOTIFICATION')
    lines.append(f'  Deadline: {review_pack.breach_notification_deadline_hours or "not specified"} hours; Realistic: {review_pack.breach_notification_realistic}')
    lines.append('')

    lines.append('8. DATA SUBJECT REQUEST ASSISTANCE')
    lines.append(f'  Required: {review_pack.dsar_assistance_required}; Chargeable: {review_pack.dsar_assistance_chargeable}')
    lines.append('')

    lines.append('9. AUDIT RIGHTS')
    lines.append(f'  On-site allowed: {review_pack.audit_rights_onsite_allowed}; Frequency limited: {review_pack.audit_rights_frequency_limited}; Third-party reports accepted: {review_pack.audit_third_party_reports_accepted}')
    lines.append('')

    lines.append('10. DELETION AND RETURN')
    lines.append(f'  Deadline: {review_pack.deletion_return_deadline_days or "not specified"} days; Statutory retention conflict: {review_pack.deletion_legal_retention_conflict}')
    lines.append('')

    lines.append('11. LIABILITY CONFLICT DETECTION')
    lines.append(f'  Uncapped: {review_pack.liability_uncapped}; Overrides MSA cap: {review_pack.liability_overrides_msa_cap}; Separate indemnities: {review_pack.liability_separate_indemnities}')
    lines.append('')

    related = list(review_pack.related_contracts.all())
    lines.append('LINKED DOCUMENTS')
    lines.append(f'  Matter: {review_pack.matter.title if review_pack.matter else "none linked"}')
    lines.append('  Related contracts (MSA/SOW): ' + (', '.join(c.title for c in related) or 'none linked'))
    lines.append('')

    risk_items = list(review_pack.risk_items.all())
    lines.append(f'RISK ITEMS ({len(risk_items)})')
    for risk in risk_items:
        tag = ' [CROSS-DOCUMENT]' if risk.is_cross_document_conflict else ''
        lines.append(f'  - [{risk.get_severity_display()}/{risk.get_confidence_display()}] {risk.title}{tag} — Owner(s): {", ".join(risk.owner_list())} — Status: {risk.get_status_display()}')
        if risk.evidence_text:
            lines.append(f'      Evidence: {risk.evidence_text}')
        if risk.related_contract_evidence_text:
            lines.append(f'      Linked MSA evidence: {risk.related_contract_evidence_text}')
        if risk.reviewer_notes:
            lines.append(f'      Reviewer notes: {risk.reviewer_notes}')
        for note in risk.notes.all():
            actor = note.author.get_full_name() or note.author.username if note.author else 'Unknown reviewer'
            lines.append(f'      Note ({note.created_at:%Y-%m-%d %H:%M}, {actor}): {note.note}')
    if not risk_items:
        lines.append('  No risk items recorded.')
    lines.append('')

    history = list(review_pack.approval_history.all())
    if history:
        lines.append('APPROVAL HISTORY')
        for entry in history:
            actor = entry.changed_by.get_full_name() or entry.changed_by.username if entry.changed_by else 'System'
            lines.append(f'  - {entry.created_at:%Y-%m-%d %H:%M} — {actor}: {entry.from_status or "—"} → {entry.to_status}' + (f' ({entry.comment})' if entry.comment else ''))
        lines.append('')

    lines.append('This memo summarizes recorded findings and does not itself constitute legal approval. Final DPA approval remains a human decision recorded in Approval History.')
    return '\n'.join(lines)
