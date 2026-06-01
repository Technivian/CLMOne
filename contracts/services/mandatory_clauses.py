"""Mandatory clause enforcement service — checks contracts for missing required clauses."""
from __future__ import annotations

from dataclasses import dataclass, field

from contracts.models import ClauseTemplate, Contract, Organization
from contracts.services.clause_policy import clause_applies_to_contract, normalize_clause_type_list


@dataclass
class MissingClause:
    clause_id: int
    clause_title: str
    jurisdiction_scope: str
    applicable_contract_types: list[str]
    fallback_available: bool


@dataclass
class ContractComplianceReport:
    contract_id: int
    contract_title: str
    contract_type: str | None
    is_compliant: bool
    missing_mandatory_clauses: list[MissingClause] = field(default_factory=list)
    present_mandatory_clauses: list[dict] = field(default_factory=list)


@dataclass
class OrgComplianceSummary:
    org_id: int
    total_contracts_checked: int
    compliant_contracts: int
    non_compliant_contracts: int
    compliance_rate_pct: float
    most_missing_clauses: list[dict]  # [{clause_id, clause_title, missing_in_count}]


class MandatoryClauseEnforcementService:
    def get_missing_mandatory_clauses(self, contract: Contract) -> list[MissingClause]:
        """Return all mandatory clauses that should apply to this contract but are absent."""
        org = contract.organization
        if not org:
            return []
        mandatory_clauses = ClauseTemplate.objects.filter(
            organization=org,
            is_mandatory=True,
            is_approved=True,
        ).prefetch_related('category')

        # The contract's text content is used to detect presence (simple substring match on title)
        contract_content_lower = (contract.content or '').lower()
        missing = []
        for clause in mandatory_clauses:
            if not clause_applies_to_contract(clause, contract):
                continue
            # Check if clause title is referenced in contract content (heuristic)
            if clause.title.lower() in contract_content_lower:
                continue
            missing.append(MissingClause(
                clause_id=clause.pk,
                clause_title=clause.title,
                jurisdiction_scope=clause.jurisdiction_scope,
                applicable_contract_types=list(normalize_clause_type_list(clause.applicable_contract_types or '')),
                fallback_available=bool(clause.fallback_content),
            ))
        return missing

    def check_contract_compliance(self, contract: Contract) -> ContractComplianceReport:
        org = contract.organization
        if not org:
            return ContractComplianceReport(
                contract_id=contract.pk,
                contract_title=contract.title,
                contract_type=contract.contract_type,
                is_compliant=True,
            )
        mandatory_clauses = ClauseTemplate.objects.filter(
            organization=org,
            is_mandatory=True,
            is_approved=True,
        ).prefetch_related('category')
        contract_content_lower = (contract.content or '').lower()
        missing = []
        present = []
        for clause in mandatory_clauses:
            if not clause_applies_to_contract(clause, contract):
                continue
            if clause.title.lower() in contract_content_lower:
                present.append({'clause_id': clause.pk, 'clause_title': clause.title})
            else:
                missing.append(MissingClause(
                    clause_id=clause.pk,
                    clause_title=clause.title,
                    jurisdiction_scope=clause.jurisdiction_scope,
                    applicable_contract_types=list(normalize_clause_type_list(clause.applicable_contract_types or '')),
                    fallback_available=bool(clause.fallback_content),
                ))
        return ContractComplianceReport(
            contract_id=contract.pk,
            contract_title=contract.title,
            contract_type=contract.contract_type,
            is_compliant=len(missing) == 0,
            missing_mandatory_clauses=missing,
            present_mandatory_clauses=present,
        )

    def get_org_compliance_summary(self, org: Organization) -> OrgComplianceSummary:
        contracts = Contract.objects.filter(organization=org)
        total = contracts.count()
        if not total:
            return OrgComplianceSummary(
                org_id=org.pk,
                total_contracts_checked=0,
                compliant_contracts=0,
                non_compliant_contracts=0,
                compliance_rate_pct=0,
                most_missing_clauses=[],
            )

        missing_counts: dict[int, dict] = {}
        compliant_count = 0
        for contract in contracts:
            report = self.check_contract_compliance(contract)
            if report.is_compliant:
                compliant_count += 1
            for m in report.missing_mandatory_clauses:
                if m.clause_id not in missing_counts:
                    missing_counts[m.clause_id] = {'clause_title': m.clause_title, 'count': 0}
                missing_counts[m.clause_id]['count'] += 1

        most_missing = sorted(
            [{'clause_id': cid, 'clause_title': v['clause_title'], 'missing_in_count': v['count']}
             for cid, v in missing_counts.items()],
            key=lambda x: -x['missing_in_count'],
        )[:10]

        non_compliant = total - compliant_count
        return OrgComplianceSummary(
            org_id=org.pk,
            total_contracts_checked=total,
            compliant_contracts=compliant_count,
            non_compliant_contracts=non_compliant,
            compliance_rate_pct=round(compliant_count / total * 100, 1),
            most_missing_clauses=most_missing,
        )


def get_mandatory_enforcement_service() -> MandatoryClauseEnforcementService:
    return MandatoryClauseEnforcementService()
