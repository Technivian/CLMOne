"""Minimal cross-document conflict detection for DPA v2.

This module intentionally implements only the next foundation requested for
DPA Review Pack v2: DPA uncapped/unlimited liability vs a linked MSA liability
cap. It does not implement the broader MSA/SOW relationship graph.
"""
from __future__ import annotations

from contracts.models import DPARiskItem
from contracts.services.dpa_review import RiskSuggestion, MANUAL_EVIDENCE, normalize, snippet_for_any

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


def check_cross_document_conflicts(review_pack) -> list[RiskSuggestion]:
    suggestions: list[RiskSuggestion] = []
    dpa_has_uncapped = review_pack.liability_uncapped or review_pack.liability_overrides_msa_cap
    if not dpa_has_uncapped:
        return suggestions

    dpa_text = normalize(review_pack.contract.content or '')
    dpa_evidence = snippet_for_any(dpa_text, DPA_UNCAPPED_KEYWORDS) or MANUAL_EVIDENCE

    for contract in review_pack.related_contracts.all():
        title_lower = (contract.title or '').lower()
        if contract.contract_type != contract.ContractType.MSA and 'msa' not in title_lower and 'master service' not in title_lower:
            continue
        msa_text = normalize(contract.content or '')
        msa_evidence = snippet_for_any(msa_text, LIABILITY_CAP_KEYWORDS)
        if not msa_evidence:
            continue
        suggestions.append(RiskSuggestion(
            category=DPARiskItem.Category.LIABILITY,
            title=f'DPA liability conflicts with "{contract.title}" liability cap',
            description=f'"{contract.title}" contains a liability cap, but the DPA contains uncapped or cap-overriding liability language. Align the DPA liability language with the MSA cap or escalate to Head of Legal.',
            severity=DPARiskItem.Severity.CRITICAL,
            owners='LEGAL,HEAD_LEGAL',
            confidence=DPARiskItem.Confidence.HIGH if dpa_evidence != MANUAL_EVIDENCE else DPARiskItem.Confidence.MEDIUM,
            evidence_text=dpa_evidence,
            related_contract_evidence_text=msa_evidence,
            source_section='Liability',
            source_field='liability_uncapped',
            detection_rule='dpa_liability_vs_msa_cap',
            conflict_type='dpa_liability_vs_msa_cap',
            fallback_recommendation='Align DPA liability with the MSA cap, or escalate any enhanced data-breach cap to Head of Legal before approval.',
            is_cross_document_conflict=True,
        ))
    return suggestions
