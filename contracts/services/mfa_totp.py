"""Authenticator-app MFA using RFC 4226/6238 compatible TOTP codes.

The canonical identity remains ``UserProfile``. This service owns secret
generation, authenticated encryption, provisioning, confirmation, and atomic
replay prevention; views never implement factor cryptography.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import secrets
import struct
import time
from urllib.parse import quote, urlencode

import qrcode
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from contracts.models import UserProfile


TOTP_PERIOD_SECONDS = 30
TOTP_DIGITS = 6
TOTP_VALIDATION_WINDOW = 1
TOTP_CIPHER_PREFIX = 'enc:v1:'


class MfaTotpError(RuntimeError):
    """A TOTP factor could not be safely read or written."""


def _cipher_for_key(configured_key: str) -> Fernet:
    try:
        return Fernet(configured_key.encode('ascii'))
    except (ValueError, TypeError) as exc:
        raise ImproperlyConfigured(
            'MFA TOTP encryption keys must be valid Fernet keys.'
        ) from exc


def _cipher() -> Fernet:
    configured_key = str(getattr(settings, 'MFA_TOTP_ENCRYPTION_KEY', '') or '').strip()
    if configured_key:
        return _cipher_for_key(configured_key)

    if str(getattr(settings, 'DJANGO_ENV', '')).lower() == 'production':
        raise ImproperlyConfigured(
            'A vaulted MFA_TOTP_ENCRYPTION_KEY is required to use TOTP in production.'
        )

    # Local/test fallback only. Production is rejected above so a factor key is
    # never silently coupled to the Django signing key in a deployed system.
    material = f'{settings.SECRET_KEY}:clmone-mfa-totp-local-v1'.encode('utf-8')
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(material).digest()))


def _decryption_ciphers() -> list[Fernet]:
    ciphers = [_cipher()]
    for previous_key in getattr(settings, 'MFA_TOTP_ENCRYPTION_PREVIOUS_KEYS', ()):
        normalized = str(previous_key or '').strip()
        if normalized:
            ciphers.append(_cipher_for_key(normalized))
    return ciphers


def generate_totp_secret() -> str:
    """Return a 160-bit Base32 secret accepted by common authenticator apps."""
    return base64.b32encode(secrets.token_bytes(20)).decode('ascii').rstrip('=')


def encrypt_totp_secret(secret: str) -> str:
    normalized = str(secret or '').strip().upper()
    if not normalized:
        raise MfaTotpError('A TOTP secret is required.')
    token = _cipher().encrypt(normalized.encode('ascii')).decode('ascii')
    return f'{TOTP_CIPHER_PREFIX}{token}'


def decrypt_totp_secret(stored_secret: str) -> str:
    secret, _key_index = _decrypt_totp_secret_with_key_index(stored_secret)
    return secret


def _decrypt_totp_secret_with_key_index(stored_secret: str) -> tuple[str, int]:
    stored = str(stored_secret or '').strip()
    if not stored.startswith(TOTP_CIPHER_PREFIX):
        raise MfaTotpError('TOTP secret is missing or uses an unsupported format.')
    payload = stored[len(TOTP_CIPHER_PREFIX):].encode('ascii')
    for key_index, cipher in enumerate(_decryption_ciphers()):
        try:
            return cipher.decrypt(payload).decode('ascii'), key_index
        except (InvalidToken, ValueError, UnicodeError):
            continue
    raise MfaTotpError('TOTP secret could not be decrypted.')


def _decoded_secret(secret: str) -> bytes:
    normalized = ''.join(str(secret or '').upper().split())
    padding = '=' * ((8 - len(normalized) % 8) % 8)
    try:
        return base64.b32decode(normalized + padding, casefold=True)
    except (ValueError, TypeError) as exc:
        raise MfaTotpError('TOTP secret is invalid.') from exc


def hotp_code(secret: str, counter: int, *, digits: int = TOTP_DIGITS) -> str:
    digest = hmac.new(
        _decoded_secret(secret),
        struct.pack('>Q', int(counter)),
        hashlib.sha1,
    ).digest()
    offset = digest[-1] & 0x0F
    truncated = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f'{truncated % (10 ** digits):0{digits}d}'


def totp_code(secret: str, *, at_time: float | None = None) -> str:
    timestamp = time.time() if at_time is None else float(at_time)
    return hotp_code(secret, int(timestamp // TOTP_PERIOD_SECONDS))


def _matching_counter(
    secret: str,
    code: str,
    *,
    at_time: float | None = None,
    last_counter: int | None = None,
) -> int | None:
    normalized_code = str(code or '').strip()
    if len(normalized_code) != TOTP_DIGITS or not normalized_code.isdigit():
        return None
    timestamp = time.time() if at_time is None else float(at_time)
    current_counter = int(timestamp // TOTP_PERIOD_SECONDS)
    for offset in range(-TOTP_VALIDATION_WINDOW, TOTP_VALIDATION_WINDOW + 1):
        counter = current_counter + offset
        if counter < 0 or (last_counter is not None and counter <= last_counter):
            continue
        if hmac.compare_digest(hotp_code(secret, counter), normalized_code):
            return counter
    return None


def begin_totp_enrollment(profile: UserProfile) -> str:
    """Create or replace a pending encrypted factor and return it once for setup."""
    secret = generate_totp_secret()
    profile.mfa_totp_secret_encrypted = encrypt_totp_secret(secret)
    profile.mfa_totp_confirmed_at = None
    profile.mfa_totp_last_counter = None
    profile.save(update_fields=[
        'mfa_totp_secret_encrypted',
        'mfa_totp_confirmed_at',
        'mfa_totp_last_counter',
        'updated_at',
    ])
    return secret


def pending_totp_secret(profile: UserProfile) -> str:
    if not profile.mfa_totp_secret_encrypted or profile.mfa_totp_confirmed_at:
        return ''
    return decrypt_totp_secret(profile.mfa_totp_secret_encrypted)


def confirm_totp_enrollment(
    profile: UserProfile,
    code: str,
    *,
    at_time: float | None = None,
) -> bool:
    """Confirm a pending factor and consume its first time-step atomically."""
    with transaction.atomic():
        locked = UserProfile.objects.select_for_update().get(pk=profile.pk)
        if not locked.mfa_totp_secret_encrypted or locked.mfa_totp_confirmed_at:
            return False
        try:
            secret, key_index = _decrypt_totp_secret_with_key_index(
                locked.mfa_totp_secret_encrypted
            )
        except MfaTotpError:
            return False
        counter = _matching_counter(secret, code, at_time=at_time)
        if counter is None:
            return False
        now = timezone.now()
        locked.mfa_enabled = True
        locked.mfa_verified_at = now
        locked.mfa_totp_confirmed_at = now
        locked.mfa_totp_last_counter = counter
        if key_index:
            locked.mfa_totp_secret_encrypted = encrypt_totp_secret(secret)
        locked.save(update_fields=[
            'mfa_enabled',
            'mfa_verified_at',
            'mfa_totp_confirmed_at',
            'mfa_totp_last_counter',
            'mfa_totp_secret_encrypted',
            'updated_at',
        ])
    profile.refresh_from_db()
    return True


def verify_totp_challenge(
    profile: UserProfile,
    code: str,
    *,
    at_time: float | None = None,
) -> bool:
    """Verify and consume a TOTP time-step atomically to prevent replay."""
    with transaction.atomic():
        locked = UserProfile.objects.select_for_update().get(pk=profile.pk)
        if not locked.uses_totp:
            return False
        try:
            secret, key_index = _decrypt_totp_secret_with_key_index(
                locked.mfa_totp_secret_encrypted
            )
        except MfaTotpError:
            return False
        counter = _matching_counter(
            secret,
            code,
            at_time=at_time,
            last_counter=locked.mfa_totp_last_counter,
        )
        if counter is None:
            return False
        locked.mfa_totp_last_counter = counter
        locked.mfa_verified_at = timezone.now()
        update_fields = ['mfa_totp_last_counter', 'mfa_verified_at', 'updated_at']
        if key_index:
            locked.mfa_totp_secret_encrypted = encrypt_totp_secret(secret)
            update_fields.append('mfa_totp_secret_encrypted')
        locked.save(update_fields=update_fields)
    profile.refresh_from_db()
    return True


def totp_provisioning_uri(*, secret: str, account_name: str) -> str:
    issuer = str(getattr(settings, 'MFA_TOTP_ISSUER', 'CLM One') or 'CLM One').strip()
    label = quote(f'{issuer}:{account_name}', safe='')
    params = urlencode({
        'secret': secret,
        'issuer': issuer,
        'algorithm': 'SHA1',
        'digits': TOTP_DIGITS,
        'period': TOTP_PERIOD_SECONDS,
    })
    return f'otpauth://totp/{label}?{params}'


def totp_qr_data_uri(*, secret: str, account_name: str) -> str:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=4,
    )
    qr.add_data(totp_provisioning_uri(secret=secret, account_name=account_name))
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white')
    output = io.BytesIO()
    image.save(output, format='PNG')
    encoded = base64.b64encode(output.getvalue()).decode('ascii')
    return f'data:image/png;base64,{encoded}'
