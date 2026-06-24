"""
File: services/core/src/stoa_core/security/client_errors.py
Layer: Core Security Utilities
Purpose: Generic client-safe error messages (no upstream leakage).
"""

from __future__ import annotations

_GENERIC_OPERATION_FAILED = "Operation failed. Contact support if the issue persists."


def client_safe_error_message(error: str | None, *, context: str = "operation") -> str | None:
    """Return a generic message for API/SSE clients; log details server-side separately."""
    if not error:
        return None
    if context == "sync":
        return "Sync failed. Contact support if the issue persists."
    if context == "content":
        return "Content generation failed. Try again or contact support."
    return _GENERIC_OPERATION_FAILED
