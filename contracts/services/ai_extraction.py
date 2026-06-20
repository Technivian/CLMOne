"""AI clause extraction service — uses Claude API to identify and locate legal clause spans.

Claude is asked to quote verbatim text for each clause it finds; Python then locates
exact character offsets via str.find so AIExtractionSpan records carry valid positions.
"""

from __future__ import annotations

import json
import logging
from decimal import Decimal

import anthropic

from contracts.models import AIExtractionSpan, Document, Organization

logger = logging.getLogger(__name__)

_MODEL = "claude-opus-4-8"
_MAX_TEXT_CHARS = 50_000  # ~12.5 K tokens — covers most contracts

_CLAUSE_LABELS = [
    "indemnity",
    "termination",
    "liability_cap",
    "data_processing",
    "renewal",
    "governing_law",
    "confidentiality",
    "payment_terms",
    "ip_ownership",
]

_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "spans": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": _CLAUSE_LABELS},
                    "text": {
                        "type": "string",
                        "description": "Verbatim quote from the document (<=400 chars)",
                    },
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                },
                "required": ["label", "text", "confidence"],
            },
        }
    },
    "required": ["spans"],
}

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def extract_clause_spans(
    text: str,
    organization: Organization,
    document: Document,
    *,
    replace_existing: bool = True,
) -> list[AIExtractionSpan]:
    """Extract labelled clause spans from *text* using Claude and persist AIExtractionSpan rows.

    Set *replace_existing=True* (default) to delete prior spans for this document
    before inserting new ones (idempotent re-extraction).
    """
    if not text or not text.strip():
        return []

    label_list = ", ".join(_CLAUSE_LABELS)
    prompt = (
        "Extract all legal clause spans from the contract text below.\n\n"
        f"For each clause found return:\n"
        f"  label      - one of: {label_list}\n"
        "  text       - a VERBATIM quote (<=400 chars) capturing the key sentence(s)."
        " The text MUST appear in the document exactly as written.\n"
        "  confidence - 0.0-1.0 (omit spans below 0.5)\n\n"
        "Multiple spans per label are allowed when the clause appears more than once.\n\n"
        f"CONTRACT TEXT:\n{text[:_MAX_TEXT_CHARS]}"
    )

    with _get_client().messages.stream(
        model=_MODEL,
        max_tokens=8192,
        thinking={"type": "adaptive"},
        output_config={
            "format": {
                "type": "json_schema",
                "json_schema": {"name": "clause_spans", "schema": _EXTRACTION_SCHEMA},
            }
        },
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()

    text_block = next((b for b in message.content if b.type == "text"), None)
    if not text_block:
        logger.warning("ai_extraction: no text block in response for document %s", document.pk)
        return []

    data = json.loads(text_block.text)

    if replace_existing:
        AIExtractionSpan.objects.filter(document=document).delete()

    spans: list[AIExtractionSpan] = []
    for item in data.get("spans", []):
        span_text = (item.get("text") or "").strip()
        if not span_text:
            continue
        pos = text.find(span_text)
        if pos == -1:
            pos = text.lower().find(span_text.lower())
        if pos == -1:
            logger.debug(
                "ai_extraction: quoted span not located in document %s, skipping: %.80s",
                document.pk,
                span_text,
            )
            continue
        confidence = Decimal(str(round(float(item.get("confidence", 0.75)), 4)))
        spans.append(
            AIExtractionSpan(
                document=document,
                organization=organization,
                label=item["label"],
                span_text=span_text,
                start_char=pos,
                end_char=pos + len(span_text),
                confidence=confidence,
                extraction_model=_MODEL,
            )
        )

    if spans:
        AIExtractionSpan.objects.bulk_create(spans)

    return spans


def get_spans_for_document(document: Document) -> list[AIExtractionSpan]:
    return list(
        AIExtractionSpan.objects.filter(document=document).order_by("start_char")
    )


def get_spans_summary(document: Document) -> dict:
    """Return a label->spans dict suitable for JSON serialisation."""
    by_label: dict[str, list[dict]] = {}
    for span in get_spans_for_document(document):
        by_label.setdefault(span.label, []).append(
            {
                "start_char": span.start_char,
                "end_char": span.end_char,
                "confidence": float(span.confidence),
                "excerpt": span.span_text[:300],
            }
        )
    return {
        "extraction_model": _MODEL,
        "label_count": len(by_label),
        "span_count": sum(len(v) for v in by_label.values()),
        "labels": by_label,
    }
