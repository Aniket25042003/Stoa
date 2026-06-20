"""
File: services/core/src/stoa_core/ingestion/extract.py
Layer: Core Ingestion Pipeline
Purpose: Implements extract behavior for the core ingestion pipeline.
Dependencies: stoa_core
"""


from __future__ import annotations

from typing import Any

from stoa_core.llm.router import invoke_json

EXTRACT_SYSTEM = """You extract structured customer intelligence signals from marketing/sales text.
Return JSON: {"signals": [{"kind": "pain_point|objection|buying_trigger|segment|win_loss",
"content": "...", "confidence": 0.0-1.0, "evidence_quote": "..."}]}
Only include signals clearly supported by the text. Max 8 signals per chunk."""


def extract_signals(chunk: str, document_id: str) -> list[dict[str, Any]]:
    """Handles extract signals logic for the surrounding Stoa workflow.

    Args:
        chunk (str): Input value used by this workflow step.
        document_id (str): Input value used by this workflow step.

    Returns:
        list[dict[str, Any]]: Result produced for the caller.
    """
    parsed, _provider = invoke_json(
        EXTRACT_SYSTEM,
        {"chunk": chunk[:8000], "document_id": document_id},
        task_name="extract",
    )
    if not parsed:
        return []
    signals = parsed.get("signals") or []
    if not isinstance(signals, list):
        return []
    out: list[dict[str, Any]] = []
    for s in signals:
        if isinstance(s, dict) and s.get("kind") and s.get("content"):
            out.append(s)
    return out
