"""
File: services/core/src/stoa_core/security/sanitize.py
Layer: Core Security Utilities
Purpose: Implements sanitize behavior for the core security utilities.
Dependencies: standard library / local modules
"""


from __future__ import annotations

import re
from typing import BinaryIO

ALLOWED_MIME = {
    "text/plain",
    "text/csv",
    "application/csv",
    "text/markdown",
    "application/json",
}
ALLOWED_EXTENSIONS = {".txt", ".csv", ".md", ".json"}

_BINARY_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"%PDF", "PDF"),
    (b"\x89PNG", "PNG"),
    (b"GIF87a", "GIF"),
    (b"GIF89a", "GIF"),
    (b"\xff\xd8\xff", "JPEG"),
    (b"PK\x03\x04", "ZIP"),
    (b"PK\x05\x06", "ZIP"),
    (b"MZ", "PE executable"),
    (b"\x7fELF", "ELF"),
    (b"Rar!", "RAR"),
    (b"7z\xbc\xaf\x27\x1c", "7z archive"),
    (b"\xd0\xcf\x11\xe0", "OLE document"),
    (b"RIFF", "RIFF container"),
)

_SNIFF_SAMPLE_BYTES = 8192

_DOC_TYPE_PATTERN = re.compile(r"^(call_transcript|review|crm_export|note)$")
DOC_TYPE_PATTERN = _DOC_TYPE_PATTERN

INLINE_CITATION_PATTERN = re.compile(
    r"\s*\[(?:kb|doc|signal|precomputed|crm|agent_evidence):[^\]]+\]",
    re.IGNORECASE,
)

INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.I),
    re.compile(r"disregard\s+(all\s+)?prior\s+instructions", re.I),
    re.compile(r"forget\s+(all\s+)?(previous|prior)\s+instructions", re.I),
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"act\s+as\s+(a\s+)?(system|admin|root)\b", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"assistant\s*:\s*", re.I),
    re.compile(r"<\s*script", re.I),
    re.compile(r"\[INST\]", re.I),
    re.compile(r"<\|im_start\|>", re.I),
    re.compile(r"<\|system\|>", re.I),
    re.compile(r"```\s*system", re.I),
    re.compile(r"jailbreak", re.I),
    re.compile(r"do\s+anything\s+now", re.I),
]

# Collapse oversized delimiter-heavy blocks that often wrap injected instructions.
_DELIMITER_RUN = re.compile(r"(?:<\|[^|]+\|>|\[/?INST\]){3,}", re.I)
_MAX_SANITIZED_CHARS = 512_000


class UploadValidationError(ValueError):
    """Raised when an upload fails validation."""


def validate_doc_type(doc_type: str) -> None:
    """Handles validate doc type logic for the surrounding Stoa workflow.

    Args:
        doc_type (str): Input value used by this workflow step.
    """
    if not DOC_TYPE_PATTERN.match(doc_type):
        raise UploadValidationError(f"Unsupported document type: {doc_type}")


def _normalize_mime(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def _detect_binary_signature(data: bytes) -> str | None:
    for signature, label in _BINARY_SIGNATURES:
        if data.startswith(signature):
            return label
    return None


def validate_upload_content(content: bytes, *, ext: str) -> None:
    """Reject binary payloads masquerading as text uploads."""
    if not content:
        return
    head = content[:16]
    binary_kind = _detect_binary_signature(head)
    if binary_kind:
        raise UploadValidationError(f"Binary content detected ({binary_kind})")
    sample = content[:_SNIFF_SAMPLE_BYTES]
    if b"\x00" in sample:
        raise UploadValidationError("Binary content detected (null bytes)")
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UploadValidationError("Upload must be valid UTF-8 text") from exc
    if ext == ".json":
        stripped = content.lstrip()
        if stripped and stripped[:1] not in (b"{", b"["):
            raise UploadValidationError("JSON upload must start with { or [")


def validate_upload(
    filename: str,
    content_type: str | None,
    size: int,
    max_bytes: int,
    *,
    content: bytes | None = None,
) -> None:
    """Handles validate upload logic for the surrounding Stoa workflow.

    Args:
        filename (str): Input value used by this workflow step.
        content_type (str | None): Input value used by this workflow step.
        size (int): Input value used by this workflow step.
        max_bytes (int): Input value used by this workflow step.
        content (bytes | None): Optional payload for magic-byte sniffing.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(f"Unsupported file type: {ext or filename}")
    if not content_type or not content_type.strip():
        raise UploadValidationError("Content-Type is required")
    mime = _normalize_mime(content_type)
    if mime not in ALLOWED_MIME:
        raise UploadValidationError(f"Unsupported MIME type: {content_type}")
    if size > max_bytes:
        raise UploadValidationError(f"File exceeds max size of {max_bytes} bytes")
    if content is not None:
        validate_upload_content(content, ext=ext)


def strip_inline_citations(text: str) -> str:
    """Remove inline evidence markers from user-facing LLM answers."""
    cleaned = INLINE_CITATION_PATTERN.sub("", text or "")
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def sanitize_user_content(text: str) -> str:
    """Handles sanitize user content logic for the surrounding Stoa workflow.

    Args:
        text (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    cleaned = text.replace("\x00", "")
    cleaned = _DELIMITER_RUN.sub("[filtered]", cleaned)
    for pattern in INJECTION_PATTERNS:
        cleaned = pattern.sub("[filtered]", cleaned)
    if len(cleaned) > _MAX_SANITIZED_CHARS:
        cleaned = cleaned[:_MAX_SANITIZED_CHARS]
    return cleaned.strip()


def read_limited(stream: BinaryIO, max_bytes: int) -> bytes:
    """Handles read limited logic for the surrounding Stoa workflow.

    Args:
        stream (BinaryIO): Input value used by this workflow step.
        max_bytes (int): Input value used by this workflow step.

    Returns:
        bytes: Result produced for the caller.
    """
    data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise UploadValidationError("File too large")
    return data
