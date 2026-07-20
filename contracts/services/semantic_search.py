"""Semantic clause search — uses Google Gemini Flash to rerank results by query relevance.

Falls back to a keyword/synonym ranker when the provider is unavailable or returns
an invalid payload, so search stays tenant-scoped and usable in local dev.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Iterable

from contracts.models import ClauseTemplate

logger = logging.getLogger(__name__)


def _gemini_model() -> str:
    from django.conf import settings
    return getattr(settings, 'GEMINI_MODEL', 'gemini-3.5-flash')


def _semantic_provider_enabled() -> bool:
    from django.conf import settings
    if not getattr(settings, 'GEMINI_AI_ENABLED', True):
        return False
    return bool(os.getenv("GEMINI_API_KEY", "").strip())


_MAX_CANDIDATES = 40  # cap prompt size for the reranking call

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SYNONYM_GROUPS = (
    {"nda", "nondisclosure", "non", "disclosure", "confidentiality", "confidential", "secret"},
    {"indemnity", "indemnification", "liability", "damages"},
    {"privacy", "gdpr", "dpa", "data", "protection"},
    {"termination", "exit", "winddown", "expiry", "expiration"},
    {"governing", "law", "jurisdiction", "venue"},
)

_RERANK_SCHEMA = {
    "type": "object",
    "properties": {
        "ranked_indices": {
            "type": "array",
            "items": {"type": "integer"},
            "description": "Input list indices ordered by relevance, most relevant first",
        }
    },
    "required": ["ranked_indices"],
}


def rank_clause_templates_semantic(
    clauses: Iterable[ClauseTemplate],
    query: str,
    *,
    limit: int = 10,
    min_score: float = 0.1,
) -> list[ClauseTemplate]:
    """Rank clause templates by relevance to ``query``.

    Contract:
      - Args are ``(clauses, query)`` in that order. ``clauses`` is any iterable
        of ClauseTemplate (a queryset is accepted and materialized here).
      - Returns a plain ``list[ClauseTemplate]`` (NOT a queryset), ordered most
        relevant first, already truncated to ``limit`` and filtered by relevance.
        Callers must paginate the list, not call queryset methods on it.
      - Empty/blank query or empty candidate set returns ``[]`` (never raises).
      - Provider failures always fall back to tenant-scoped keyword ranking.
    """
    clause_list = list(clauses)
    if not clause_list or not query or not str(query).strip():
        return []

    e2e_result = _e2e_semantic_fixture(clause_list, query, limit=limit, min_score=min_score)
    if e2e_result is not None:
        return e2e_result

    if not _semantic_provider_enabled():
        return _keyword_rank(clause_list, query, limit=limit, min_score=min_score)

    try:
        return _llm_rank(clause_list, query, limit=limit)
    except Exception:
        logger.warning("ai semantic_search: provider call failed; using keyword fallback", exc_info=True)
        return _keyword_rank(clause_list, query, limit=limit, min_score=0.0)


def _e2e_semantic_fixture(clause_list, query, *, limit: int, min_score: float):
    """DJANGO_E2E-only fixtures so browser tests can exercise provider-shape paths.

    Query format: ``e2e_fixture:<name>`` where name is one of
    valid | list | malformed | empty | error | timeout | keyword.
    Returns ``None`` when fixtures are inactive.
    """
    from django.conf import settings

    if not getattr(settings, 'DJANGO_E2E', False):
        return None
    raw = str(query).strip().lower()
    if not raw.startswith('e2e_fixture:'):
        return None
    name = raw.split(':', 1)[1].strip()
    if name in {'empty'}:
        return []
    if name in {'malformed', 'error', 'timeout', 'keyword'}:
        # Simulate provider failure / bad payload → safe keyword fallback.
        logger.warning('ai semantic_search: e2e fixture %s; using keyword fallback', name)
        return _keyword_rank(clause_list, 'indemnity confidentiality privacy', limit=limit, min_score=0.0)
    if name in {'valid', 'list'}:
        # Deterministic reordering without calling the provider.
        return list(reversed(clause_list))[:limit]
    return _keyword_rank(clause_list, query, limit=limit, min_score=min_score)


def _extract_ranked_indices(payload: Any) -> list[int] | None:
    """Normalize documented provider payload shapes to ranked index integers."""
    if payload is None:
        return None

    if isinstance(payload, list):
        if not payload:
            return []
        if all(isinstance(item, int) for item in payload):
            return [item for item in payload if isinstance(item, int)]
        if all(isinstance(item, dict) for item in payload):
            indices: list[int] = []
            for item in payload:
                if not isinstance(item, dict):
                    continue
                idx = item.get('index', item.get('idx', item.get('ranked_index')))
                if isinstance(idx, int):
                    indices.append(idx)
            return indices
        return None

    if isinstance(payload, dict):
        for key in ('ranked_indices', 'indices', 'results', 'rankings'):
            if key in payload:
                nested = _extract_ranked_indices(payload.get(key))
                if nested is not None:
                    return nested
        return None

    return None


def _parse_provider_payload(raw_text: str) -> list[int] | None:
    if not raw_text or not str(raw_text).strip():
        return None
    try:
        payload = json.loads(raw_text)
    except (ValueError, TypeError):
        return None
    return _extract_ranked_indices(payload)


# ---------------------------------------------------------------------------
# LLM reranker
# ---------------------------------------------------------------------------


def _llm_rank(clauses: list[ClauseTemplate], query: str, *, limit: int) -> list[ClauseTemplate]:
    from google import genai
    from google.genai import types

    candidates = clauses[:_MAX_CANDIDATES]
    items_text = "\n".join(
        f"[{i}] {c.title or 'Untitled'}: {(c.content or c.tags or '')[:200]}"
        for i, c in enumerate(candidates)
    )

    prompt = (
        f'Rank the following contract clause templates by relevance to this search query: "{query}"\n\n'
        f"Return the indices of the most relevant clauses ordered from most to least relevant. "
        f"Include at most {limit} indices. Omit clauses that are not relevant to the query.\n\n"
        f"CLAUSES:\n{items_text}"
    )

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=_gemini_model(),
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type='application/json'),
    )

    ranked_indices = _parse_provider_payload(getattr(response, 'text', '') or '')
    if ranked_indices is None:
        logger.warning("ai semantic_search: invalid rerank payload shape; using keyword fallback")
        return _keyword_rank(clauses, query, limit=limit, min_score=0.0)

    result: list[ClauseTemplate] = []
    seen: set[int] = set()
    for idx in ranked_indices:
        if isinstance(idx, int) and 0 <= idx < len(candidates) and idx not in seen:
            result.append(candidates[idx])
            seen.add(idx)

    return result[:limit]


# ---------------------------------------------------------------------------
# Keyword fallback (no API key required)
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> set[str]:
    if not text:
        return set()
    return {t for t in _TOKEN_RE.findall(text.lower()) if t}


def _expand_tokens(tokens: set[str]) -> set[str]:
    if not tokens:
        return set()
    expanded = set(tokens)
    for group in _SYNONYM_GROUPS:
        if expanded & group:
            expanded.update(group)
    return expanded


def _keyword_score(clause: ClauseTemplate, query_tokens: set[str]) -> float:
    title_t = _expand_tokens(_tokenize(clause.title or ""))
    tags_t = _expand_tokens(_tokenize(clause.tags or ""))
    content_t = _expand_tokens(_tokenize(clause.content or ""))
    fallback_t = _expand_tokens(
        _tokenize((clause.fallback_content or "") + " " + (clause.playbook_notes or ""))
    )
    weighted = (
        3.0 * len(query_tokens & title_t)
        + 2.0 * len(query_tokens & tags_t)
        + 1.0 * len(query_tokens & content_t)
        + 1.0 * len(query_tokens & fallback_t)
    )
    return weighted / max(7.0 * len(query_tokens), 1)


def _keyword_rank(
    clauses: list[ClauseTemplate],
    query: str,
    *,
    limit: int,
    min_score: float,
) -> list[ClauseTemplate]:
    query_tokens = _expand_tokens(_tokenize(query))
    scored = [
        (c, _keyword_score(c, query_tokens))
        for c in clauses
    ]
    scored = [(c, s) for c, s in scored if s >= min_score]
    scored.sort(
        key=lambda x: (
            -x[1],
            -(x[0].updated_at.timestamp() if x[0].updated_at else 0),
            x[0].pk,
        )
    )
    return [c for c, _ in scored[:limit]]
