"""Token-aware structure-aware text chunking for embedding."""

from __future__ import annotations

import re
from dataclasses import dataclass

_HEADING_RE = re.compile(r"(?:^|\n)(#{1,6}\s+.+|\n[A-Z][^\n]{0,80}\n[-=]{3,})")


def estimate_tokens(text: str) -> int:
    """Rough token estimate without external deps (avg ~4 chars/token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass(frozen=True)
class TextChunk:
    content: str
    token_count: int
    chunk_index: int


def _split_sections(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    parts = _HEADING_RE.split(text)
    sections: list[str] = []
    for part in parts:
        part = part.strip()
        if part:
            sections.append(part)
    return sections or [text]


def _split_paragraphs(section: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
    return paras or [section.strip()]


def chunk_text(
    text: str,
    *,
    target_tokens: int = 600,
    max_tokens: int = 800,
    overlap_tokens: int = 80,
) -> list[TextChunk]:
    """Split text into overlapping chunks sized for embedding models."""
    text = text.strip()
    if not text:
        return []

    if estimate_tokens(text) <= max_tokens:
        return [TextChunk(content=text, token_count=estimate_tokens(text), chunk_index=0)]

    units: list[str] = []
    for section in _split_sections(text):
        for para in _split_paragraphs(section):
            if estimate_tokens(para) > max_tokens:
                # Fall back to char windows for very long paragraphs
                char_size = max_tokens * 4
                overlap_chars = overlap_tokens * 4
                start = 0
                while start < len(para):
                    end = min(start + char_size, len(para))
                    units.append(para[start:end].strip())
                    if end >= len(para):
                        break
                    start = max(end - overlap_chars, start + 1)
            else:
                units.append(para)

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if current:
            chunks.append("\n\n".join(current))
            current = []
            current_tokens = 0

    for unit in units:
        unit_tokens = estimate_tokens(unit)
        if unit_tokens > max_tokens:
            flush()
            chunks.append(unit)
            continue
        if current_tokens + unit_tokens > target_tokens and current:
            flush()
        current.append(unit)
        current_tokens += unit_tokens
        if current_tokens >= target_tokens:
            flush()

    flush()

    if not chunks:
        return [TextChunk(content=text, token_count=estimate_tokens(text), chunk_index=0)]

    # Apply overlap between consecutive chunks
    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            overlapped.append(chunk)
            continue
        prev = chunks[i - 1]
        prev_words = prev.split()
        overlap_word_count = max(1, overlap_tokens)
        prefix = " ".join(prev_words[-overlap_word_count:]) if prev_words else ""
        merged = f"{prefix}\n\n{chunk}".strip() if prefix else chunk
        overlapped.append(merged)

    return [
        TextChunk(content=c, token_count=estimate_tokens(c), chunk_index=i)
        for i, c in enumerate(overlapped)
        if c.strip()
    ]


def chunk_text_strings(
    text: str,
    *,
    target_tokens: int = 600,
    max_tokens: int = 800,
    overlap_tokens: int = 80,
) -> list[str]:
    """Backward-compatible string-only chunk API."""
    return [c.content for c in chunk_text(text, target_tokens=target_tokens, max_tokens=max_tokens, overlap_tokens=overlap_tokens)]
