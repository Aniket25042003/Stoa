from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SourceType = Literal["web", "serp", "fetch", "other"]


@dataclass
class ResearchItem:
    source_type: SourceType
    title: str
    raw_excerpt: str
    summary: str
    source_url: str | None = None
    query: str | None = None
    confidence: float = 0.5
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchResult:
    source_type: SourceType
    items: list[ResearchItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
