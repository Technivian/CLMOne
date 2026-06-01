"""Playbook service — lookup, resolve, and list negotiation playbooks for a contract."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from contracts.models import ClausePlaybook, ClauseTemplate, ClauseVariant, Contract, Organization
from contracts.services.clause_variants import resolve_clause_variant

_ClausePlaybookDoesNotExist = ClausePlaybook.DoesNotExist
_ClauseTemplateDoesNotExist = ClauseTemplate.DoesNotExist


@dataclass
class PlaybookVariantDTO:
    clause_id: int
    clause_title: str
    standard_text: str
    variant_content: str | None
    fallback_content: str | None
    playbook_notes: str
    jurisdiction_scope: str


@dataclass
class PlaybookDTO:
    playbook_id: int
    name: str
    description: str
    jurisdiction_scope: str
    risk_level: str
    fallback_position: str
    clauses: list[PlaybookVariantDTO] = field(default_factory=list)


class PlaybookService:
    def list_playbooks(self, org: Organization, jurisdiction: str = None, risk_level: str = None) -> list[PlaybookDTO]:
        qs = ClausePlaybook.objects.filter(organization=org, is_active=True).order_by('name')
        if jurisdiction:
            qs = qs.filter(jurisdiction_scope__iexact=jurisdiction)
        if risk_level:
            qs = qs.filter(risk_level__iexact=risk_level)
        return [_playbook_to_dto(p) for p in qs]

    def get_playbook(self, playbook_id: int, org: Organization) -> PlaybookDTO:
        playbook = ClausePlaybook.objects.get(pk=playbook_id, organization=org)
        variants_qs = (
            ClauseVariant.objects
            .filter(playbook=playbook, is_active=True)
            .select_related('template')
            .order_by('priority')
        )
        dto = _playbook_to_dto(playbook)
        dto.clauses = [_variant_to_clause_dto(v) for v in variants_qs]
        return dto

    def get_playbooks_for_contract(self, contract: Contract) -> list[PlaybookDTO]:
        """Return playbooks relevant to this contract based on jurisdiction and type."""
        if not contract.organization_id:
            return []
        qs = ClausePlaybook.objects.filter(organization=contract.organization, is_active=True)
        matching = []
        for playbook in qs:
            score = 0
            if playbook.jurisdiction_scope in ('GLOBAL', ''):
                score += 1
            elif contract.jurisdiction and playbook.jurisdiction_scope.upper() in (contract.jurisdiction or '').upper():
                score += 2
            if playbook.risk_level and contract.risk_level and \
               playbook.risk_level.upper() == (contract.risk_level or '').upper():
                score += 2
            if score > 0:
                matching.append((score, playbook))
        matching.sort(key=lambda x: -x[0])
        return [_playbook_to_dto(p) for _, p in matching]

    def resolve_clause_for_playbook(self, clause_id: int, contract: Contract) -> Optional[PlaybookVariantDTO]:
        """Resolve the best variant of a clause given a contract context."""
        try:
            template = ClauseTemplate.objects.get(pk=clause_id)
        except _ClauseTemplateDoesNotExist:
            return None
        resolved = resolve_clause_variant(template, contract)
        return PlaybookVariantDTO(
            clause_id=clause_id,
            clause_title=template.title,
            standard_text=template.content,
            variant_content=resolved.fallback_content if resolved else None,
            fallback_content=template.fallback_content,
            playbook_notes=template.playbook_notes,
            jurisdiction_scope=template.jurisdiction_scope,
        )


def _playbook_to_dto(p: ClausePlaybook) -> PlaybookDTO:
    return PlaybookDTO(
        playbook_id=p.pk,
        name=p.name,
        description=p.description or '',
        jurisdiction_scope=p.jurisdiction_scope,
        risk_level=p.risk_level or '',
        fallback_position=p.fallback_position or '',
    )


def _variant_to_clause_dto(v: ClauseVariant) -> PlaybookVariantDTO:
    t = v.template
    return PlaybookVariantDTO(
        clause_id=t.pk,
        clause_title=t.title,
        standard_text=t.content,
        variant_content=v.fallback_content or None,
        fallback_content=t.fallback_content,
        playbook_notes=v.playbook_notes or t.playbook_notes,
        jurisdiction_scope=v.jurisdiction_scope or t.jurisdiction_scope,
    )


def get_playbook_service() -> PlaybookService:
    return PlaybookService()
