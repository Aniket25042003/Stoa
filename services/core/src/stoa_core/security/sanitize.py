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

DOC_TYPE_PATTERN = re.compile(r"^(call_transcript|review|crm_export|note)$")

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


def validate_upload(filename: str, content_type: str | None, size: int, max_bytes: int) -> None:
    """Handles validate upload logic for the surrounding Stoa workflow.

    Args:
        filename (str): Input value used by this workflow step.
        content_type (str | None): Input value used by this workflow step.
        size (int): Input value used by this workflow step.
        max_bytes (int): Input value used by this workflow step.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(f"Unsupported file type: {ext or filename}")
    if content_type and content_type not in ALLOWED_MIME:
        raise UploadValidationError(f"Unsupported MIME type: {content_type}")
    if size > max_bytes:
        raise UploadValidationError(f"File exceeds max size of {max_bytes} bytes")


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
