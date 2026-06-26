"""
File: services/core/src/stoa_core/competitive/monitor.py
Layer: Core Competitive Intelligence
Purpose: Implements monitor behavior for the core competitive intelligence.
Dependencies: stoa_core
"""


from __future__ import annotations

import hashlib
import logging
from typing import Any

from stoa_core.llm.router import invoke_json
from stoa_core.research.fetch import fetch_page_text as _fetch_page_text

logger = logging.getLogger(__name__)

USER_AGENT = "Stoa-Intel-Bot/0.1 (+https://stoa.ai)"


def fetch_page_text(url: str, timeout: float = 15.0) -> str:
    """Fetch page HTML (legacy competitive monitor compatibility)."""
    return _fetch_page_text(url, timeout=timeout, as_text=False)


def content_hash(text: str) -> str:
    """Handles content hash logic for the surrounding Stoa workflow.

    Args:
        text (str): Input value used by this workflow step.

    Returns:
        str: Result produced for the caller.
    """
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def detect_changes(old_text: str, new_text: str, competitor_name: str) -> dict[str, Any] | None:
    """Handles detect changes logic for the surrounding Stoa workflow.

    Args:
        old_text (str): Input value used by this workflow step.
        new_text (str): Input value used by this workflow step.
        competitor_name (str): Input value used by this workflow step.

    Returns:
        dict[str, Any] | None: Result produced for the caller.
    """
    if not new_text:
        return None
    if content_hash(old_text) == content_hash(new_text):
        return {"changed": False, "summary": "No changes detected"}
    schema = (
        '{"changed": true, "summary": "...", '
        '"categories": ["pricing|product|messaging|hiring"], '
        '"severity": "low|medium|high"}'
    )
    parsed, _ = invoke_json(
        "Summarize what changed between two competitor page snapshots. Return JSON: " + schema,
        {
            "competitor": competitor_name,
            "old_excerpt": old_text[:4000],
            "new_excerpt": new_text[:4000],
        },
        task_name="summarize",
    )
    fallback = {
        "changed": True,
        "summary": "Content changed (details unavailable)",
        "severity": "medium",
    }
    return parsed or fallback
