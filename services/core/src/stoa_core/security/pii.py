"""PII detection and redaction for storage, logs, and exports."""

from __future__ import annotations

import re
from typing import Any

# --- Contact & identity ---
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_E164_RE = re.compile(r"\+[1-9]\d{7,14}\b")
PHONE_US_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
PHONE_INTL_RE = re.compile(
    r"(?<!\d)(?:\+?\d{1,3}[-.\s.]?)?\(?\d{2,4}\)?"
    r"[-.\s.]?\d{3,4}[-.\s.]?\d{3,4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
UK_NINO_RE = re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]?\b", re.I)
PASSPORT_RE = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")
IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
DRIVER_LICENSE_RE = re.compile(r"\b[A-Z]\d{7,8}\b")

# --- Financial ---
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# --- Secrets & tokens (logs / accidental paste) ---
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")
JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b")
BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}", re.I)

# --- Network (logging) ---
IPV4_RE = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\b")

# --- Dates often used as DOB ---
DOB_RE = re.compile(
    r"\b(?:0[1-9]|1[0-2])[/.-](?:0[1-9]|[12]\d|3[01])[/.-](?:19|20)\d{2}\b"
)

_REDACTION_RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (BEARER_RE, "[TOKEN]"),
    (JWT_RE, "[JWT]"),
    (OPENAI_KEY_RE, "[API_KEY]"),
    (AWS_KEY_RE, "[AWS_KEY]"),
    (EMAIL_RE, "[EMAIL]"),
    (IBAN_RE, "[IBAN]"),
    (SSN_RE, "[SSN]"),
    (UK_NINO_RE, "[NINO]"),
    (PHONE_E164_RE, "[PHONE]"),
    (PHONE_US_RE, "[PHONE]"),
    (PHONE_INTL_RE, "[PHONE]"),
    (CARD_RE, "[CARD]"),
    (PASSPORT_RE, "[PASSPORT]"),
    (DRIVER_LICENSE_RE, "[LICENSE]"),
    (DOB_RE, "[DOB]"),
)

_LOG_EXTRA_RULES: tuple[tuple[re.Pattern[str], str], ...] = ((IPV4_RE, "[IP]"),)


def _apply_rules(text: str, rules: tuple[tuple[re.Pattern[str], str], ...]) -> str:
    out = text
    for pattern, replacement in rules:
        out = pattern.sub(replacement, out)
    return out


def redact_pii(text: str) -> str:
    """Redact common PII/secrets from text destined for storage or user-visible exports."""
    if not text:
        return text
    return _apply_rules(text, _REDACTION_RULES)


def redact_pii_for_logs(text: str) -> str:
    """Redact PII plus network identifiers from log lines."""
    if not text:
        return text
    combined = _REDACTION_RULES + _LOG_EXTRA_RULES
    return _apply_rules(text, combined)


def redact_json(value: Any) -> Any:
    """Recursively redact string leaves in JSON-like structures (audit metadata, SSE payloads)."""
    if isinstance(value, str):
        return redact_pii(value)
    if isinstance(value, dict):
        return {k: redact_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_json(item) for item in value]
    return value
