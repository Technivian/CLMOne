"""Outbound e-signature providers.

Historically the platform could only *reconcile* inbound provider webhooks
(see ``esign.py``) — there was no way to actually send a document out for
signature. This module adds a small provider abstraction for the outbound
direction.

- ``NullSignatureProvider`` is the default: it simulates a send (no network),
  so the signing flow works end-to-end in development, demos and tests without
  any provider credentials.
- ``HttpSignatureProvider`` posts to a configurable e-sign gateway (DocuSign /
  Adobe Sign / an internal relay), selected via the ``ESIGN_PROVIDER`` setting.

Resolve the configured provider with ``get_signature_provider()``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings


class SignatureProviderError(RuntimeError):
    """Raised when an outbound provider fails to accept a send request."""


@dataclass
class SendResult:
    """Outcome of dispatching a signature request to a provider."""

    external_id: str
    signing_url: str = ''
    provider: str = ''
    raw: dict = field(default_factory=dict)


class OutboundSignatureProvider(Protocol):
    name: str

    def send(self, signature_request) -> SendResult:
        ...


class NullSignatureProvider:
    """Default provider — simulates a send without any external call.

    The external reference is deterministic so retries are idempotent and the
    value is easy to assert in tests.
    """

    name = 'null'

    def send(self, signature_request) -> SendResult:
        external_id = f'null-{signature_request.organization_id}-{signature_request.id}'
        signing_url = f'/contracts/signatures/{signature_request.id}/'
        return SendResult(
            external_id=external_id,
            signing_url=signing_url,
            provider=self.name,
            raw={'simulated': True},
        )


class HttpSignatureProvider:
    """Generic outbound gateway: POST a JSON envelope to a configured endpoint.

    Works with any e-sign service fronted by an HTTP relay that returns an
    ``external_id`` (and optionally a ``signing_url``). Network shape mirrors
    the existing Salesforce integration (urllib, bounded timeout).
    """

    name = 'http'

    def __init__(self, base_url: str, api_key: str, *, timeout: int = 10, opener=None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        # Injectable for tests; defaults to urllib.
        self._opener = opener or urllib_request.urlopen

    def send(self, signature_request) -> SendResult:
        if not self.base_url:
            raise SignatureProviderError('ESIGN_API_BASE is not configured.')
        payload = {
            'reference': f'{signature_request.organization_id}:{signature_request.id}',
            'signer_name': signature_request.signer_name,
            'signer_email': signature_request.signer_email,
            'signer_role': signature_request.signer_role,
            'contract_id': signature_request.contract_id,
        }
        body = json.dumps(payload).encode('utf-8')
        req = urllib_request.Request(
            f'{self.base_url}/envelopes',
            data=body,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
            },
        )
        try:
            with self._opener(req, timeout=self.timeout) as response:
                raw = json.loads(response.read().decode('utf-8') or '{}')
        except urllib_error.URLError as exc:
            raise SignatureProviderError(f'E-sign gateway request failed: {exc}') from exc
        except (ValueError, TypeError) as exc:
            raise SignatureProviderError(f'E-sign gateway returned an invalid response: {exc}') from exc

        external_id = str(raw.get('external_id') or raw.get('envelope_id') or '').strip()
        if not external_id:
            raise SignatureProviderError('E-sign gateway response is missing an external id.')
        return SendResult(
            external_id=external_id,
            signing_url=str(raw.get('signing_url') or '').strip(),
            provider=self.name,
            raw=raw,
        )


def get_signature_provider(config: Optional[Any] = None) -> OutboundSignatureProvider:
    config = config or settings
    provider_name = str(getattr(config, 'ESIGN_PROVIDER', 'null') or 'null').strip().lower()
    if provider_name == 'http':
        return HttpSignatureProvider(
            base_url=str(getattr(config, 'ESIGN_API_BASE', '') or ''),
            api_key=str(getattr(config, 'ESIGN_API_KEY', '') or ''),
            timeout=int(getattr(config, 'ESIGN_API_TIMEOUT_SECONDS', 10)),
        )
    return NullSignatureProvider()
