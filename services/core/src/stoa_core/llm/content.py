"""Normalize LLM response payloads to plain text (Vertex/Gemini content blocks, etc.)."""

from __future__ import annotations

import ast
import json
import re
from typing import Any

_THOUGHT_SIGNATURE_RE = re.compile(
    r"""['"]thought_signature['"]\s*:\s*['"][^'"]*['"]\s*,?\s*""",
    re.IGNORECASE,
)


def _join_parts(parts: list[str]) -> str:
    if not parts:
        return ""
    return "".join(parts).strip()


def _text_from_block(block: Any) -> str:
    if block is None:
        return ""
    if isinstance(block, str):
        return block
    if isinstance(block, dict):
        block_type = str(block.get("type") or "").lower()
        if block_type in {"", "text"}:
            text = block.get("text") or block.get("content")
            if isinstance(text, str):
                return text
        if block_type == "thinking":
            return ""
        nested = block.get("text") or block.get("content")
        if nested is not None and nested is not block:
            return extract_text_content(nested)
    return ""


def _text_from_sequence(items: list[Any]) -> str:
    parts: list[str] = []
    for item in items:
        if isinstance(item, str):
            parts.append(item)
            continue
        chunk = _text_from_block(item)
        if chunk:
            parts.append(chunk)
    return _join_parts(parts)


def _parse_stringified_blocks(value: str) -> str | None:
    stripped = value.strip()
    if not stripped.startswith("[") or "thought_signature" not in stripped:
        return None
    for parser in (ast.literal_eval, json.loads):
        try:
            parsed = parser(stripped)
        except (ValueError, SyntaxError, json.JSONDecodeError):
            continue
        if isinstance(parsed, list):
            text = _text_from_sequence(parsed)
            if text:
                return text
    return None


def _strip_thought_signature_artifacts(text: str) -> str:
    cleaned = _THOUGHT_SIGNATURE_RE.sub("", text)
    cleaned = re.sub(r"\[\s*\{", "", cleaned)
    cleaned = re.sub(r"\}\s*,?\s*'\.", ".", cleaned)
    cleaned = re.sub(r"'\s*\]\s*$", "", cleaned)
    return cleaned.strip()


def extract_text_content(value: Any) -> str:
    """Return user-visible text from an LLM response or AgentExecutor output."""
    if value is None:
        return ""

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return ""
        parsed = _parse_stringified_blocks(stripped)
        if parsed:
            return parsed
        if "thought_signature" in stripped:
            return _strip_thought_signature_artifacts(stripped)
        return value

    if isinstance(value, list):
        return _text_from_sequence(value)

    if isinstance(value, dict):
        return _text_from_block(value)

    content = getattr(value, "content", None)
    if content is not None and content is not value:
        return extract_text_content(content)

    text = str(value).strip()
    parsed = _parse_stringified_blocks(text)
    return parsed if parsed else text
