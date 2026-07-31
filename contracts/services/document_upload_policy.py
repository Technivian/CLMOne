"""Shared conservative validation for existing internal document upload paths."""

from __future__ import annotations

import os

from django.core.exceptions import ValidationError


ALLOWED_DOCUMENT_UPLOAD_EXTENSIONS = frozenset({
    '.pdf',
    '.docx',
    '.txt',
    '.md',
    '.csv',
    '.html',
    '.xml',
    '.json',
})
MAX_DOCUMENT_UPLOAD_BYTES = 50 * 1024 * 1024


class DocumentUploadValidationError(ValidationError):
    def __init__(self, message, *, status_code: int):
        self.status_code = status_code
        super().__init__(message)


def validate_document_upload(uploaded_file) -> None:
    """Reject unsupported or oversized files before storage mutation.

    Extensions are intentionally conservative and mirror the existing
    extraction path. Browser-provided MIME values are recorded as metadata,
    never trusted as proof of type.
    """
    if uploaded_file is None:
        return
    if uploaded_file.size > MAX_DOCUMENT_UPLOAD_BYTES:
        raise DocumentUploadValidationError(
            f'File exceeds maximum size of {MAX_DOCUMENT_UPLOAD_BYTES // (1024 * 1024)} MB.',
            status_code=413,
        )
    extension = os.path.splitext(uploaded_file.name or '')[1].lower()
    if extension not in ALLOWED_DOCUMENT_UPLOAD_EXTENSIONS:
        allowed = ', '.join(sorted(ALLOWED_DOCUMENT_UPLOAD_EXTENSIONS))
        raise DocumentUploadValidationError(
            f'File type {extension!r} is not supported. Allowed: {allowed}',
            status_code=415,
        )
