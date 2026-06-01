"""Clause analytics service — usage stats, top clauses, dependency graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from collections import Counter

from contracts.models import (
    ClauseTemplate,
    ClauseUsageEvent,
    Contract,
    Organization,
)


@dataclass
class ClauseUsageStat:
    clause_id: int
    clause_title: str
    category: str | None
    jurisdiction_scope: str
    total_uses: int
    accepted_count: int
    rejected_count: int
    modified_count: int
    acceptance_rate_pct: float


@dataclass
class ClauseDependencyNode:
    clause_id: int
    clause_title: str
    co_occurring_clauses: list[dict]  # [{id, title, count}]


class ClauseAnalyticsService:
    def get_most_used_clauses(self, org: Organization, limit: int = 20) -> list[ClauseUsageStat]:
        events = ClauseUsageEvent.objects.filter(organization=org).select_related('clause', 'clause__category')
        stats: dict[int, dict] = {}
        for ev in events:
            cid = ev.clause_id
            if cid not in stats:
                stats[cid] = {
                    'clause': ev.clause,
                    'total': 0, 'accepted': 0, 'rejected': 0, 'modified': 0,
                }
            stats[cid]['total'] += 1
            if ev.action == ClauseUsageEvent.Action.ACCEPTED:
                stats[cid]['accepted'] += 1
            elif ev.action == ClauseUsageEvent.Action.REJECTED:
                stats[cid]['rejected'] += 1
            elif ev.action == ClauseUsageEvent.Action.MODIFIED:
                stats[cid]['modified'] += 1

        results = []
        for cid, s in sorted(stats.items(), key=lambda x: -x[1]['total'])[:limit]:
            c = s['clause']
            total = s['total']
            accepted = s['accepted']
            results.append(ClauseUsageStat(
                clause_id=cid,
                clause_title=c.title,
                category=c.category.name if c.category_id and c.category else None,
                jurisdiction_scope=c.jurisdiction_scope,
                total_uses=total,
                accepted_count=accepted,
                rejected_count=s['rejected'],
                modified_count=s['modified'],
                acceptance_rate_pct=round(accepted / total * 100, 1) if total else 0,
            ))
        return results

    def get_clause_usage_stats(self, org: Organization) -> dict:
        qs = ClauseUsageEvent.objects.filter(organization=org)
        total = qs.count()
        by_action = {}
        for action in ClauseUsageEvent.Action.values:
            by_action[action.lower()] = qs.filter(action=action).count()
        unique_clauses = qs.values('clause_id').distinct().count()
        unique_contracts = qs.filter(contract_id__isnull=False).values('contract_id').distinct().count()
        return {
            'total_events': total,
            'unique_clauses_used': unique_clauses,
            'unique_contracts': unique_contracts,
            'by_action': by_action,
        }

    def record_usage(
        self,
        org: Organization,
        clause: ClauseTemplate,
        contract: Contract | None,
        action: str,
        performed_by=None,
        note: str = '',
    ) -> ClauseUsageEvent:
        return ClauseUsageEvent.objects.create(
            organization=org,
            clause=clause,
            contract=contract,
            action=action,
            performed_by=performed_by,
            note=note,
        )

    def get_dependency_graph(self, org: Organization) -> list[ClauseDependencyNode]:
        """
        For each clause, find which other clauses co-appear in the same contracts.
        Returns nodes sorted by most co-occurrences.
        """
        # Map contract_id → set of clause_ids
        events = (
            ClauseUsageEvent.objects
            .filter(organization=org, contract_id__isnull=False, action=ClauseUsageEvent.Action.ADDED)
            .values('contract_id', 'clause_id', 'clause__title')
        )
        contract_clauses: dict[int, list[tuple[int, str]]] = {}
        for ev in events:
            cid = ev['contract_id']
            if cid not in contract_clauses:
                contract_clauses[cid] = []
            contract_clauses[cid].append((ev['clause_id'], ev['clause__title']))

        # Count co-occurrences
        co_counts: dict[int, Counter] = {}
        clause_titles: dict[int, str] = {}
        for pairs in contract_clauses.values():
            ids = [p[0] for p in pairs]
            for cid, ctitle in pairs:
                clause_titles[cid] = ctitle
                if cid not in co_counts:
                    co_counts[cid] = Counter()
                for other_id in ids:
                    if other_id != cid:
                        co_counts[cid][other_id] += 1

        nodes = []
        for cid, counter in sorted(co_counts.items(), key=lambda x: -sum(x[1].values())):
            co = [
                {'id': oid, 'title': clause_titles.get(oid, ''), 'count': cnt}
                for oid, cnt in counter.most_common(10)
            ]
            nodes.append(ClauseDependencyNode(
                clause_id=cid,
                clause_title=clause_titles.get(cid, ''),
                co_occurring_clauses=co,
            ))
        return nodes


def get_clause_analytics_service() -> ClauseAnalyticsService:
    return ClauseAnalyticsService()
