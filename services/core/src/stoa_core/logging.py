"""
File: services/core/src/stoa_core/logging.py
Layer: Application Source
Purpose: Implements logging behavior for the application source.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

from stoa_core.security.pii import redact_pii_for_logs

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class _PiiRedactingFormatter(logging.Formatter):
    """Manage _PiiRedactingFormatter behavior within the Stoa application layer.

    This class groups related state and operations so routes, workers, or core
    pipelines can depend on a focused abstraction instead of duplicating logic.
    """
    def format(self, record: logging.LogRecord) -> str:
        """Handles format logic for the surrounding Stoa workflow.

        Args:
            record (logging.LogRecord): Input value used by this workflow step.

        Returns:
            str: Result produced for the caller.
        """
        if isinstance(record.msg, str):
            record.msg = redact_pii_for_logs(record.msg)
        if record.args:
            record.args = tuple(
                redact_pii_for_logs(str(a)) if isinstance(a, str) else a
                for a in record.args
            )
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """Handles setup logging logic for the surrounding Stoa workflow.

    Args:
        level (int): Input value used by this workflow step.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _PiiRedactingFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def new_request_id() -> str:
    """Handles new request id logic for the surrounding Stoa workflow.

    Returns:
        str: Result produced for the caller.
    """
    rid = str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    """Handles get request id logic for the surrounding Stoa workflow.

    Returns:
        str: Result produced for the caller.
    """
    return request_id_var.get() or ""
