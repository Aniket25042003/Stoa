"""Content sanitization and upload validation."""

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
    re.compile(r"you\s+are\s+now\s+", re.I),
    re.compile(r"system\s*:\s*", re.I),
    re.compile(r"<\s*script", re.I),
    re.compile(r"\[INST\]", re.I),
]


class UploadValidationError(ValueError):
    """Raised when an upload fails validation."""


def validate_doc_type(doc_type: str) -> None:
    if not DOC_TYPE_PATTERN.match(doc_type):
        raise UploadValidationError(f"Unsupported document type: {doc_type}")


def validate_upload(filename: str, content_type: str | None, size: int, max_bytes: int) -> None:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError(f"Unsupported file type: {ext or filename}")
    if content_type and content_type not in ALLOWED_MIME:
        raise UploadValidationError(f"Unsupported MIME type: {content_type}")
    if size > max_bytes:
        raise UploadValidationError(f"File exceeds max size of {max_bytes} bytes")


def sanitize_user_content(text: str) -> str:
    cleaned = text.replace("\x00", "")
    for pattern in INJECTION_PATTERNS:
        cleaned = pattern.sub("[filtered]", cleaned)
    return cleaned.strip()


def read_limited(stream: BinaryIO, max_bytes: int) -> bytes:
    data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise UploadValidationError("File too large")
    return data
