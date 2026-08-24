"""Field-level encryption for highly sensitive PII (currently: SSN).

Uses Fernet (AES-128-CBC + HMAC) symmetric encryption. The key is derived
from a dedicated SSN_ENCRYPTION_KEY env var when present; otherwise it is
derived deterministically from SECRET_KEY (domain-separated) so no extra
configuration is required to get real encryption-at-rest, though setting
SSN_ENCRYPTION_KEY explicitly in production is recommended so SSN data
remains protected even if SECRET_KEY (used for auth tokens) ever leaks.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re

from cryptography.fernet import Fernet, InvalidToken

from app.core.security import SECRET_KEY

_SSN_KEY_ENV = "SSN_ENCRYPTION_KEY"


def _derive_key() -> bytes:
    raw = os.getenv(_SSN_KEY_ENV)
    if raw:
        # Allow either a ready-made Fernet key or an arbitrary passphrase.
        try:
            Fernet(raw.encode())
            return raw.encode()
        except (ValueError, InvalidToken):
            digest = hashlib.sha256(raw.encode()).digest()
            return base64.urlsafe_b64encode(digest)

    if not SECRET_KEY:
        raise RuntimeError(
            "Cannot encrypt SSN: neither SSN_ENCRYPTION_KEY nor SECRET_KEY is configured"
        )
    # Domain-separated derivation so this key is never identical to any
    # other use of SECRET_KEY (e.g. JWT signing) even though it's sourced
    # from the same secret in the absence of a dedicated key.
    digest = hashlib.sha256(f"ssn-encryption:{SECRET_KEY}".encode()).digest()
    return base64.urlsafe_b64encode(digest)


_fernet = Fernet(_derive_key())

_SSN_DIGITS_RE = re.compile(r"\D+")


def normalize_ssn(raw: str) -> str:
    """Strip formatting, returning exactly 9 digits, or raise ValueError."""
    digits = _SSN_DIGITS_RE.sub("", raw or "")
    if len(digits) != 9:
        raise ValueError("SSN must be 9 digits")
    return digits


def _lookup_secret() -> str:
    raw = os.getenv(_SSN_KEY_ENV)
    if raw:
        return raw
    if not SECRET_KEY:
        raise RuntimeError(
            "Cannot hash SSN: neither SSN_ENCRYPTION_KEY nor SECRET_KEY is configured"
        )
    return SECRET_KEY


def ssn_lookup_hash(raw: str) -> str:
    """Deterministic HMAC-SHA256 of a normalized SSN, for equality lookups.

    Fernet ciphertext is randomized (fresh IV per call) so ssn_encrypted can
    never be compared directly across rows. This separate keyed hash lets us
    find "is this the same SSN as another user's record" (e.g. to link the
    same person's accounts across agencies) without ever decrypting stored
    SSNs just to compare them.
    """
    digits = normalize_ssn(raw)
    key = hashlib.sha256(f"ssn-lookup:{_lookup_secret()}".encode()).digest()
    return hmac.new(key, digits.encode(), hashlib.sha256).hexdigest()


def encrypt_ssn(raw: str) -> tuple[str, str, str]:
    """Returns (ciphertext, last4, lookup_hash) for a normalized 9-digit SSN."""
    digits = normalize_ssn(raw)
    ciphertext = _fernet.encrypt(digits.encode()).decode()
    return ciphertext, digits[-4:], ssn_lookup_hash(digits)


def decrypt_ssn(ciphertext: str) -> str:
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Unable to decrypt SSN (key mismatch or corrupt data)") from exc


def mask_ssn(last4: str | None) -> str | None:
    if not last4:
        return None
    return f"***-**-{last4}"
