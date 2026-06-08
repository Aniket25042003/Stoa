"""Structured logging helpers."""

from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar

from stoa_core.security.pii import redact_pii_for_logs

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class _PiiRedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if isinstance(record.msg, str):
            record.msg = redact_pii_for_logs(record.msg)
        if record.args:
            record.args = tuple(redact_pii_for_logs(str(a)) if isinstance(a, str) else a for a in record.args)
        return super().format(record)


def setup_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _PiiRedactingFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)


def new_request_id() -> str:
    rid = str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    return request_id_var.get() or ""
