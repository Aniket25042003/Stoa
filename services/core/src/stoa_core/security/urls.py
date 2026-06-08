"""URL and filename safety helpers."""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_storage_filename(filename: str, *, fallback: str = "upload.txt") -> str:
    """Return a single-segment filename safe for object storage keys."""
    base = os.path.basename(filename or fallback).strip()
    if not base or base in {".", ".."}:
        base = fallback
    cleaned = _SAFE_FILENAME_RE.sub("_", base)
    return cleaned[:200] or fallback


def is_safe_external_href(url: str) -> bool:
    """Allow only http(s) links for user-facing anchors."""
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
