"""Deterministic cross-document conflict detection for DPA Review Pack.

This module compares checklist facts found in the DPA against linked
commercial contracts. It intentionally does not scan the DPA checklist
itself; `contracts.services.dpa_review.run_dpa_analysis()` remains the
DPA-only scanner and must run before this service.
"""
from __future__ import annotations

from dataclasses import dataclass

from contracts.models import Contract, DPARiskItem
from contracts.services.dpa_review import (
    MANUAL_EVIDENCE,
    RiskSuggestion,
    _find_hours_deadline,
    normalize,
    snippet_for_any,
)


@dataclass(frozen=True)
class RelatedEvidence:
    contract: Contract
    evidence_text: str


LIABILITY_CAP_KEYWORDS = [
    'limitation of liability',
    'liability cap',
    'aggregate liability',
    'total liability',
    'fees paid',
    'fees payable',
    'shall not exceed',
]
DPA_UNCAPPED_KEYWORDS = [
    'uncapped',
    'unlimited liability',
    'no limitation of liability',
    'notwithstanding the limitation of liability',
    'notwithstanding any limitation of liability',
]

AUDIT_BROAD_KEYWORDS = [
    'on-site audit',
    'onsite audit',
    'audit at any time',
    'unlimited audit',
    'unrestricted audit',
    'audit of facilities',
    'audit of premises',
]
AUDIT_LIMIT_KEYWORDS = [
    'no more than once per year',
    'once per year',
    'annually',
    'reasonable notice',
    '30 days notice',
    '30 days prior notice',
    'soc 2 report shall satisfy',
    'third-party report',
    'restricted scope',
]

DPA_BREACH_NOTICE_KEYWORDS = [
    'within 4 hours',
    'within 8 hours',
    'within 12 hours',
    'within 24 hours',
    'immediately notify',
    'notify immediately',
]
CONTRACT_NOTICE_KEYWORDS = [
    'within 72 hours',
    'without undue delay',
    'promptly notify',
    'as soon as reasonably practicable',
    'following confirmation',
    'after confirming',
]

DPA_DELETION_KEYWORDS = [
    'delete or return',
    'delete all personal data',
    'return all personal data',
    'within 30 days',
    'immediately delete',
    'immediate deletion',
]
RETENTION_KEYWORDS = [
    'statutory retention',
    'retention period',
    'retain payroll',
    'retain tax',
    'tax records',
    'payroll records',
    'legal recordkeeping',
    'archive',
    'archival',
]

DPA_SUBPROCESSOR_APPROVAL_KEYWORDS = [
    'prior written approval',
    'specific prior written approval',
    'case-by-case approval',
    'approval is required before any new subprocessor',
]
DELIVERY_SUBPROCESSOR_KEYWORDS = [
    'payroll vendor',
    'payroll vendors',
    'subprocessor',
    'subcontractor',
    'saas',
    'hosting provider',
    'cloud provider',
    'affiliate',
    'third party',
    'third-party',
]

DPA_ASSISTANCE_KEYWORDS = [
    'unlimited assistance',
    'at no cost',
    'at no additional fee',
    'free assistance',
    'assist client with data subject requests',
    'assist controller with data subject requests',
    'assist with audits',
    'assist with investigations',
    'controller obligations',
]
SCOPE_FEE_LIMIT_KEYWORDS = [
    'chargeable',
    'additional fees',
    'professional services fees',
    'out of scope',
    'beyond scope',
    'change control',
    'statement of work',
    'support fees',
]

DPA_SPECIFIC_SECURITY_KEYWORDS = [
    'encryption',
    'multi-factor authentication',
    'multi factor authentication',
    'mfa',
    'audit logging',
    'logging',
    'regular backup',
    'backups',
    'segregation',
    'incident response',
    'access reviews',
    'certifications',
    'penetration testing',
    'pen testing',
]
WEAK_SECURITY_KEYWORDS = [
    'commercially reasonable security',
    'commercially reasonable measures',
    'appropriate technical and organisational measures',
    'appropriate technical and organizational measures',
    'reasonable safeguards',
    'industry standard security',
]


def _related_contracts(review_pack):
    return review_pack.related_contracts.all()


def _related_evidence(review_pack, keywords: list[str]) -> RelatedEvidence | None:
    for contract in _related_contracts(review_pack):
        text_lower = normalize(contract.content or '')
        evidence = snippet_for_any(text_lower, keywords)
        if evidence:
            return RelatedEvidence(contract=contract, evidence_text=evidence)
    return None


def _dpa_evidence(dpa_text: str, keywords: list[str], fallback_allowed: bool = True) -> str:
    evidence = snippet_for_any(dpa_text, keywords)
    if evidence:
        return evidence
    return MANUAL_EVIDENCE if fallback_allowed else ''


def _append_once(suggestions: list[RiskSuggestion], emitted: set[str], suggestion: RiskSuggestion) -> None:
    if suggestion.conflict_type in emitted:
        return
    emitted.add(suggestion.conflict_type)
    suggestions.append(suggestion)


def check_cross_document_conflicts(review_pack) -> list[RiskSuggestion]:
    suggestions: list[RiskSuggestion] = []
    emitted: set[str] = set()
    dpa_text = normalize(review_pack.contract.content or '')

    dpa_has_uncapped = review_pack.liability_uncapped or review_pack.liability_overrides_msa_cap
    if dpa_has_uncapped:
        related = _related_evidence(review_pack, LIABILITY_CAP_KEYWORDS)
        if related:
            dpa_evidence = _dpa_evidence(dpa_text, DPA_UNCAPPED_KEYWORDS)
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.LIABILITY,
                title=f'DPA liability conflicts with "{related.contract.title}" liability cap',
                description=f'"{related.contract.title}" contains a liability cap, but the DPA contains uncapped or cap-overriding liability language. Align the DPA liability language with the MSA cap or escalate to Head of Legal.',
                severity=DPARiskItem.Severity.CRITICAL,
                owners='LEGAL,HEAD_LEGAL',
                confidence=DPARiskItem.Confidence.HIGH if dpa_evidence != MANUAL_EVIDENCE else DPARiskItem.Confidence.MEDIUM,
                evidence_text=dpa_evidence,
                related_contract_evidence_text=related.evidence_text,
                source_section='Liability',
                source_field='liability_uncapped',
                detection_rule='dpa_liability_vs_msa_cap',
                conflict_type='dpa_liability_vs_msa_cap',
                fallback_recommendation='Align DPA liability with the MSA cap, or escalate any enhanced data-breach cap to Head of Legal before approval.',
                is_cross_document_conflict=True,
            ))

    dpa_has_audit_rights = review_pack.audit_rights_onsite_allowed or bool(snippet_for_any(dpa_text, AUDIT_BROAD_KEYWORDS))
    if dpa_has_audit_rights and not review_pack.audit_rights_frequency_limited:
        related = _related_evidence(review_pack, AUDIT_LIMIT_KEYWORDS)
        if related:
            dpa_evidence = _dpa_evidence(dpa_text, AUDIT_BROAD_KEYWORDS)
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.AUDIT,
                title=f'DPA audit rights exceed "{related.contract.title}" audit limits',
                description='The DPA appears to grant broad audit rights while a linked contract limits audit frequency, notice, scope, or substitution by third-party assurance reports.',
                severity=DPARiskItem.Severity.HIGH,
                owners='LEGAL,DPO_SECURITY',
                confidence=DPARiskItem.Confidence.HIGH if dpa_evidence != MANUAL_EVIDENCE else DPARiskItem.Confidence.MEDIUM,
                evidence_text=dpa_evidence,
                related_contract_evidence_text=related.evidence_text,
                source_section='Audit Rights',
                source_field='audit_rights_onsite_allowed',
                detection_rule='dpa_audit_vs_contract_audit_limit',
                conflict_type='dpa_audit_vs_contract_audit_limit',
                fallback_recommendation='Align DPA audit rights with the linked contract audit cadence, notice, scope, and assurance-report fallback.',
                is_cross_document_conflict=True,
            ))

    breach_hours, breach_evidence = _find_hours_deadline(dpa_text, 'breach')
    if breach_hours is not None and breach_hours <= 24:
        related = _related_evidence(review_pack, CONTRACT_NOTICE_KEYWORDS)
        if related:
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.BREACH_NOTIFICATION,
                title=f'DPA breach notice conflicts with "{related.contract.title}" incident notice',
                description='The DPA requires a very short breach notice deadline while a linked contract uses a different or more operationally practical incident-notice standard.',
                severity=DPARiskItem.Severity.HIGH,
                owners='LEGAL,DPO_SECURITY,DELIVERY',
                confidence=DPARiskItem.Confidence.HIGH,
                evidence_text=breach_evidence or _dpa_evidence(dpa_text, DPA_BREACH_NOTICE_KEYWORDS),
                related_contract_evidence_text=related.evidence_text,
                source_section='Breach Notification',
                source_field='breach_notification_deadline_hours',
                detection_rule='dpa_breach_notice_vs_contract_notice',
                conflict_type='dpa_breach_notice_vs_contract_notice',
                fallback_recommendation='Harmonize breach notice timing with the linked agreement and confirm the operational clock starts from awareness or confirmation.',
                is_cross_document_conflict=True,
            ))

    if review_pack.deletion_return_deadline_days and review_pack.deletion_return_deadline_days <= 30:
        related = _related_evidence(review_pack, RETENTION_KEYWORDS)
        if related:
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.DELETION,
                title=f'DPA deletion deadline conflicts with "{related.contract.title}" retention duties',
                description='The DPA requires immediate or short deletion/return while a linked contract indicates retention, archival, statutory, payroll, tax, or legal recordkeeping obligations.',
                severity=DPARiskItem.Severity.HIGH,
                owners='LEGAL,DELIVERY',
                confidence=DPARiskItem.Confidence.HIGH,
                evidence_text=_dpa_evidence(dpa_text, DPA_DELETION_KEYWORDS),
                related_contract_evidence_text=related.evidence_text,
                source_section='Deletion and Return',
                source_field='deletion_return_deadline_days',
                detection_rule='dpa_deletion_vs_retention_obligation',
                conflict_type='dpa_deletion_vs_retention_obligation',
                fallback_recommendation='Carve out legally required retention and define deletion, return, archive, and certificate obligations consistently across documents.',
                is_cross_document_conflict=True,
            ))

    if review_pack.subprocessor_prior_approval_required:
        related = _related_evidence(review_pack, DELIVERY_SUBPROCESSOR_KEYWORDS)
        if related:
            dpa_evidence = _dpa_evidence(dpa_text, DPA_SUBPROCESSOR_APPROVAL_KEYWORDS)
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.SUBPROCESSOR,
                title=f'DPA subprocessor approval conflicts with "{related.contract.title}" delivery model',
                description='The DPA requires specific prior written subprocessor approval while a linked contract indicates use of vendors, subprocessors, subcontractors, SaaS tools, affiliates, hosting, cloud, or other third parties.',
                severity=DPARiskItem.Severity.HIGH,
                owners='LEGAL,DPO_SECURITY,BUSINESS,DELIVERY',
                confidence=DPARiskItem.Confidence.HIGH if dpa_evidence != MANUAL_EVIDENCE else DPARiskItem.Confidence.MEDIUM,
                evidence_text=dpa_evidence,
                related_contract_evidence_text=related.evidence_text,
                source_section='Subprocessors',
                source_field='subprocessor_prior_approval_required',
                detection_rule='dpa_subprocessor_approval_vs_delivery_model',
                conflict_type='dpa_subprocessor_approval_vs_delivery_model',
                fallback_recommendation='Use a prior-notice/general-authorization model or confirm the delivery model can support prior written approval before each vendor change.',
                is_cross_document_conflict=True,
            ))

    if snippet_for_any(dpa_text, DPA_ASSISTANCE_KEYWORDS):
        related = _related_evidence(review_pack, SCOPE_FEE_LIMIT_KEYWORDS)
        if related:
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.DSAR,
                title=f'DPA assistance obligations may exceed "{related.contract.title}" scope or fees',
                description='The DPA grants broad or free assistance for DSARs, audits, investigations, or controller obligations while a linked contract limits support by scope, fees, or change control.',
                severity=DPARiskItem.Severity.HIGH,
                owners='LEGAL,BUSINESS,FINANCE',
                confidence=DPARiskItem.Confidence.MEDIUM,
                evidence_text=_dpa_evidence(dpa_text, DPA_ASSISTANCE_KEYWORDS, fallback_allowed=False),
                related_contract_evidence_text=related.evidence_text,
                source_section='DSAR Assistance',
                source_field='dsar_assistance_chargeable',
                detection_rule='dpa_assistance_vs_scope_or_fees',
                conflict_type='dpa_assistance_vs_scope_or_fees',
                fallback_recommendation='Clarify included assistance, chargeable support, response standards, and any change-control trigger.',
                is_cross_document_conflict=True,
            ))

    if review_pack.security_measures_specific:
        related = _related_evidence(review_pack, WEAK_SECURITY_KEYWORDS)
        if related:
            _append_once(suggestions, emitted, RiskSuggestion(
                category=DPARiskItem.Category.SECURITY,
                title=f'DPA security obligations are more specific than "{related.contract.title}" security terms',
                description='The DPA imposes specific security controls while a linked contract or security schedule uses weaker or vague security language.',
                severity=DPARiskItem.Severity.MEDIUM,
                owners='DPO_SECURITY,LEGAL',
                confidence=DPARiskItem.Confidence.MEDIUM,
                evidence_text=_dpa_evidence(dpa_text, DPA_SPECIFIC_SECURITY_KEYWORDS),
                related_contract_evidence_text=related.evidence_text,
                source_section='Security Measures',
                source_field='security_measures_specific',
                detection_rule='dpa_security_obligations_vs_contract_security',
                conflict_type='dpa_security_obligations_vs_contract_security',
                fallback_recommendation='Confirm the linked security schedule can support the DPA-specific controls or incorporate the controls into the commercial contract.',
                is_cross_document_conflict=True,
            ))

    return suggestions
