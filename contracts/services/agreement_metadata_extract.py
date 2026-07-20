"""Conservative agreement metadata extraction for Upload & Review.

Hints are surfaced for human confirmation — never treated as approved facts.
Extraction runs from readable text only (no image OCR).
"""
from __future__ import annotations

import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from typing import Optional

from contracts.models import Contract

CONFIDENCE_HIGH = 'high'
CONFIDENCE_MEDIUM = 'medium'
CONFIDENCE_LOW = 'low'
CONFIDENCE_NONE = 'none'

_TYPE_PATTERNS = (
    (Contract.ContractType.DPA, re.compile(r'\b(?:data processing agreement|data processing addendum|\bDPA\b)\b', re.I)),
    (Contract.ContractType.NDA, re.compile(r'\b(?:non[- ]disclosure|confidentiality agreement|\bNDA\b)\b', re.I)),
    (Contract.ContractType.MSA, re.compile(r'\b(?:master (?:service|services) agreement|\bMSA\b)\b', re.I)),
    (Contract.ContractType.SOW, re.compile(r'\b(?:statement of work|\bSOW\b)\b', re.I)),
    (Contract.ContractType.SAAS, re.compile(r'\b(?:saas|software[- ]as[- ]a[- ]service|subscription agreement)\b', re.I)),
    (Contract.ContractType.VENDOR, re.compile(r'\b(?:vendor|supplier|procurement) agreement\b', re.I)),
    (Contract.ContractType.AMENDMENT, re.compile(r'\b(?:amendment|addendum|variation)\b', re.I)),
    (Contract.ContractType.BAA, re.compile(r'\b(?:business associate agreement|\bBAA\b)\b', re.I)),
)

_DPA_SIGNAL = re.compile(
    r'\b(?:data processing|personal data|gdpr|controller|processor|sub[- ]?processor|'
    r'standard contractual clauses|\bSCCs?\b|data subject)\b',
    re.I,
)

_DATE_PATTERNS = (
    ('start_date', re.compile(
        r'(?:effective(?:\s+date)?|commencement(?:\s+date)?|start(?:\s+date)?)\s*'
        r'(?:(?:is|as of|on|:|=)\s*)?'
        r'(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}|\d{4}[\/\-.]\d{1,2}[\/\-.]\d{1,2}|'
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|'
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        re.I,
    )),
    ('end_date', re.compile(
        r'(?:expir(?:y|ation|es)(?:\s+date)?|end(?:\s+date)?|terminat(?:es|ion)(?:\s+date)?)\s*'
        r'(?:(?:is|as of|on|:|=)\s*)?'
        r'(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}|\d{4}[\/\-.]\d{1,2}[\/\-.]\d{1,2}|'
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|'
        r'\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
        re.I,
    )),
)

_COUNTERPARTY_PATTERNS = (
    re.compile(r'between\s+([^,\n]{3,80}?)\s+and\s+([^,\n.]{3,80})', re.I),
    re.compile(r'(?:counterparty|other party|vendor|supplier|customer)\s*:\s*([^\n,]{3,80})', re.I),
)

_TITLE_PATTERNS = (
    re.compile(r'^\s*(?:agreement|contract)\s*(?:title|name)\s*:\s*(.+)$', re.I | re.M),
    re.compile(r'^\s*((?:master |data processing |non[- ]disclosure |statement of work ).{0,80})$', re.I | re.M),
)


@dataclass
class ExtractedField:
    value: str
    confidence: str
    source: str = ''

    def to_dict(self):
        return asdict(self)


@dataclass
class AgreementExtractionResult:
    title: ExtractedField
    contract_type: ExtractedField
    counterparty: ExtractedField
    start_date: ExtractedField
    end_date: ExtractedField
    governing_law: ExtractedField
    value: ExtractedField
    currency: ExtractedField
    possible_dpa: ExtractedField
    text_available: bool
    extraction_source: str
    message: str

    def to_dict(self):
        return {
            'title': self.title.to_dict(),
            'contract_type': self.contract_type.to_dict(),
            'counterparty': self.counterparty.to_dict(),
            'start_date': self.start_date.to_dict(),
            'end_date': self.end_date.to_dict(),
            'governing_law': self.governing_law.to_dict(),
            'value': self.value.to_dict(),
            'currency': self.currency.to_dict(),
            'possible_dpa': self.possible_dpa.to_dict(),
            'text_available': self.text_available,
            'extraction_source': self.extraction_source,
            'message': self.message,
        }


def _empty_field(confidence=CONFIDENCE_NONE):
    return ExtractedField(value='', confidence=confidence)


def _parse_date_to_iso(raw: str) -> Optional[str]:
    cleaned = re.sub(r'\s+', ' ', (raw or '').strip().rstrip('.'))
    formats = (
        '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
        '%d.%m.%Y', '%B %d, %Y', '%B %d %Y', '%d %B %Y',
    )
    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def extract_text_from_upload(uploaded_file, filename: str = '') -> tuple[str, str]:
    """Return (text, source_label) from an in-memory upload without persisting."""
    name = filename or getattr(uploaded_file, 'name', '') or ''
    ext = os.path.splitext(name)[1].lower()
    raw = uploaded_file.read()
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)

    if ext == '.pdf':
        try:
            from pypdf import PdfReader
            reader = PdfReader(BytesIO(raw))
            text = '\n'.join((page.extract_text() or '') for page in reader.pages).strip()
            if not text:
                return '', 'manual-review-image-pdf'
            return text, 'pdf-extraction'
        except Exception:
            return '', 'manual-review'

    if ext == '.docx':
        try:
            import docx as python_docx
            doc = python_docx.Document(BytesIO(raw))
            text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip()).strip()
            if not text:
                return '', 'manual-review-empty'
            return text, 'docx-extraction'
        except Exception:
            return '', 'manual-review'

    if ext in {'.txt', '.md', '.csv', '.html', '.htm', '.xml', '.json', '.log', '.rtf'}:
        text = raw.decode('utf-8', errors='ignore').strip()
        if not text:
            return '', 'manual-review-empty'
        return text, 'text-extraction'

    return '', 'manual-review'


def _extract_title(text: str, filename: str) -> ExtractedField:
    for pattern in _TITLE_PATTERNS:
        match = pattern.search(text)
        if match:
            value = re.sub(r'\s+', ' ', match.group(1)).strip(' -:\t')
            if 4 <= len(value) <= 160:
                return ExtractedField(value=value, confidence=CONFIDENCE_MEDIUM, source='document text')
    stem = os.path.splitext(os.path.basename(filename or ''))[0].replace('_', ' ').replace('-', ' ').strip()
    if stem:
        return ExtractedField(value=stem, confidence=CONFIDENCE_LOW, source='filename')
    return _empty_field()


def _extract_contract_type(text: str, filename: str) -> ExtractedField:
    haystacks = (text[:4000], filename or '')
    for contract_type, pattern in _TYPE_PATTERNS:
        for haystack in haystacks:
            if pattern.search(haystack):
                confidence = CONFIDENCE_HIGH if haystack is haystacks[0] else CONFIDENCE_MEDIUM
                return ExtractedField(value=contract_type, confidence=confidence, source='keyword match')
    return _empty_field()


def _extract_counterparty(text: str) -> ExtractedField:
    for pattern in _COUNTERPARTY_PATTERNS:
        match = pattern.search(text[:5000])
        if not match:
            continue
        if match.lastindex and match.lastindex >= 2:
            # Prefer the second party in "between X and Y"
            candidate = match.group(2).strip(' "\'')
        else:
            candidate = match.group(1).strip(' "\'')
        candidate = re.sub(r'\s+', ' ', candidate)[:120]
        if len(candidate) >= 3:
            return ExtractedField(value=candidate, confidence=CONFIDENCE_MEDIUM, source='document text')
    return _empty_field()


def _extract_dates(text: str) -> tuple[ExtractedField, ExtractedField]:
    start = _empty_field()
    end = _empty_field()
    for key, pattern in _DATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        iso = _parse_date_to_iso(match.group(1))
        if not iso:
            continue
        field = ExtractedField(value=iso, confidence=CONFIDENCE_MEDIUM, source='document text')
        if key == 'start_date':
            start = field
        else:
            end = field
    return start, end


def _extract_governing_law(text: str) -> ExtractedField:
    match = re.search(r'governed by the laws? of ([^.\n;]{2,80})', text, re.I)
    if match:
        return ExtractedField(
            value=match.group(1).strip().rstrip(','),
            confidence=CONFIDENCE_HIGH,
            source='document text',
        )
    match = re.search(r'governing law[:\s]+([^.\n;]{2,80})', text, re.I)
    if match:
        return ExtractedField(
            value=match.group(1).strip().rstrip(','),
            confidence=CONFIDENCE_MEDIUM,
            source='document text',
        )
    return _empty_field()


def _extract_value(text: str) -> tuple[ExtractedField, ExtractedField]:
    match = re.search(
        r'(?:(?:USD|EUR|GBP|CHF|CAD|AUD)\s*|[$€£]\s*)([\d,]+(?:\.\d{2})?)',
        text,
        re.I,
    )
    if not match:
        return _empty_field(), _empty_field()
    raw_value = match.group(1).replace(',', '')
    try:
        Decimal(raw_value)
    except Exception:
        return _empty_field(), _empty_field()
    currency = 'USD'
    prefix = match.group(0)
    if '€' in prefix or re.search(r'\bEUR\b', prefix, re.I):
        currency = 'EUR'
    elif '£' in prefix or re.search(r'\bGBP\b', prefix, re.I):
        currency = 'GBP'
    elif re.search(r'\bCHF\b', prefix, re.I):
        currency = 'CHF'
    elif re.search(r'\bCAD\b', prefix, re.I):
        currency = 'CAD'
    elif re.search(r'\bAUD\b', prefix, re.I):
        currency = 'AUD'
    return (
        ExtractedField(value=raw_value, confidence=CONFIDENCE_MEDIUM, source='document text'),
        ExtractedField(value=currency, confidence=CONFIDENCE_MEDIUM, source='document text'),
    )


def _extract_possible_dpa(text: str, contract_type: str) -> ExtractedField:
    if contract_type == Contract.ContractType.DPA:
        return ExtractedField(value='true', confidence=CONFIDENCE_HIGH, source='contract type')
    hits = len(_DPA_SIGNAL.findall(text[:8000]))
    if hits >= 3:
        return ExtractedField(value='true', confidence=CONFIDENCE_MEDIUM, source='privacy signals')
    if hits >= 1:
        return ExtractedField(value='true', confidence=CONFIDENCE_LOW, source='privacy signals')
    return ExtractedField(value='false', confidence=CONFIDENCE_LOW, source='no privacy signals')


def extract_agreement_metadata(text: str, filename: str = '', extraction_source: str = '') -> AgreementExtractionResult:
    """Build confirmation-ready field hints from readable agreement text."""
    text = text or ''
    text_available = bool(text.strip())
    if not text_available:
        message = (
            'No readable text was found. Confirm details manually — scanned image-only PDFs need a text layer.'
            if extraction_source == 'manual-review-image-pdf'
            else 'Could not extract readable text from this file. Confirm details manually.'
        )
        empty = _empty_field()
        return AgreementExtractionResult(
            title=_extract_title('', filename),
            contract_type=empty,
            counterparty=empty,
            start_date=empty,
            end_date=empty,
            governing_law=empty,
            value=empty,
            currency=empty,
            possible_dpa=ExtractedField(value='false', confidence=CONFIDENCE_NONE, source=''),
            text_available=False,
            extraction_source=extraction_source or 'manual-review',
            message=message,
        )

    title = _extract_title(text, filename)
    contract_type = _extract_contract_type(text, filename)
    counterparty = _extract_counterparty(text)
    start_date, end_date = _extract_dates(text)
    governing_law = _extract_governing_law(text)
    value, currency = _extract_value(text)
    possible_dpa = _extract_possible_dpa(text, contract_type.value)
    return AgreementExtractionResult(
        title=title,
        contract_type=contract_type,
        counterparty=counterparty,
        start_date=start_date,
        end_date=end_date,
        governing_law=governing_law,
        value=value,
        currency=currency,
        possible_dpa=possible_dpa,
        text_available=True,
        extraction_source=extraction_source or 'text-extraction',
        message='Extracted fields are suggestions — confirm before upload.',
    )


def metadata_hints_from_text(text: str) -> dict:
    """Backward-compatible subset used by post-submit AI review payloads."""
    result = extract_agreement_metadata(text)
    return {
        'governing_law': result.governing_law.value,
        'value': result.value.value,
        'payment_terms': '',
        'confidence': 'Confirm extracted information before relying on it.',
        'title': result.title.value,
        'contract_type': result.contract_type.value,
        'counterparty': result.counterparty.value,
        'start_date': result.start_date.value,
        'end_date': result.end_date.value,
        'possible_dpa': result.possible_dpa.value == 'true',
    }
