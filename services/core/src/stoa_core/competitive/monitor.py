"""Competitive intelligence monitoring helpers."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from stoa_core.llm.router import invoke_json
from stoa_core.security.ssrf import resolve_safe_https_target

logger = logging.getLogger(__name__)

USER_AGENT = "Stoa-Intel-Bot/0.1 (+https://stoa.ai)"


def fetch_page_text(url: str, timeout: float = 15.0) -> str:
    try:
        target = resolve_safe_https_target(url)
        pinned_url = f"https://{target.ip}{target.path_with_query}"
        with httpx.Client(timeout=timeout, follow_redirects=False) as client:
            resp = client.get(
                pinned_url,
                headers={"Host": target.hostname, "User-Agent": USER_AGENT},
            )
            resp.raise_for_status()
            return resp.text[:50000]
    except Exception as exc:
        logger.warning("Fetch failed for %s: %s", url, exc)
        return ""


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def detect_changes(old_text: str, new_text: str, competitor_name: str) -> dict[str, Any] | None:
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
