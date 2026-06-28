"""Sanitized conversation evidence cache and durable KB persistence for agent searches."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from stoa_core.config import get_settings
from stoa_core.rag.ingest import ingest_knowledge
from stoa_core.redis.client import get_redis_sync
from stoa_core.security.pii import redact_pii
from stoa_core.security.sanitize import sanitize_user_content

logger = logging.getLogger(__name__)

AGENT_SEARCH_EVIDENCE_KIND = "agent_search_evidence"
EVIDENCE_PREFIX = "stoa:agent:evidence:"

_TURN_ACCUMULATORS: dict[str, TurnEvidenceAccumulator] = {}


@dataclass
class EvidenceHit:
    id: str
    title: str
    snippet: str
    uri: str
    provider: str
    source: str
    fetched_at: str
    entity_type: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)
    persist_eligible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "snippet": self.snippet,
            "uri": self.uri,
            "provider": self.provider,
            "source": self.source,
            "fetched_at": self.fetched_at,
            "entity_type": self.entity_type,
            "meta": self.meta,
            "persist_eligible": self.persist_eligible,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EvidenceHit:
        return cls(
            id=str(data.get("id") or ""),
            title=str(data.get("title") or ""),
            snippet=str(data.get("snippet") or ""),
            uri=str(data.get("uri") or ""),
            provider=str(data.get("provider") or ""),
            source=str(data.get("source") or ""),
            fetched_at=str(data.get("fetched_at") or ""),
            entity_type=data.get("entity_type"),
            meta=data.get("meta") if isinstance(data.get("meta"), dict) else {},
            persist_eligible=bool(data.get("persist_eligible", True)),
        )


@dataclass
class TurnEvidenceAccumulator:
    hits: list[EvidenceHit] = field(default_factory=list)
    seen_uris: set[str] = field(default_factory=set)

    def add(self, hits: list[EvidenceHit]) -> None:
        for hit in hits:
            key = hit.uri or hit.id
            if key and key in self.seen_uris:
                continue
            if key:
                self.seen_uris.add(key)
            self.hits.append(hit)


def _normalize_query(query: str) -> str:
    return re.sub(r"\s+", " ", query.strip().lower())


def _cache_key(
    org_id: str,
    conversation_id: str,
    source: str,
    query: str,
    entity_type: str | None,
) -> str:
    raw = "|".join([source, entity_type or "", _normalize_query(query)])
    digest = hashlib.sha256(raw.encode()).hexdigest()[:32]
    return f"{EVIDENCE_PREFIX}{org_id}:{conversation_id}:{digest}"


def _sanitize_text(text: str) -> str:
    settings = get_settings()
    cleaned = sanitize_user_content(redact_pii(text.strip()))
    return cleaned[: settings.agent_evidence_max_snippet_chars]


def sanitize_hit(hit: EvidenceHit) -> EvidenceHit:
    return EvidenceHit(
        id=hit.id,
        title=_sanitize_text(hit.title)[:200],
        snippet=_sanitize_text(hit.snippet),
        uri=hit.uri,
        provider=hit.provider,
        source=hit.source,
        fetched_at=hit.fetched_at,
        entity_type=hit.entity_type,
        meta=hit.meta,
        persist_eligible=hit.persist_eligible,
    )


def get_turn_accumulator(org_id: str, conversation_id: str) -> TurnEvidenceAccumulator:
    key = f"{org_id}:{conversation_id}"
    if key not in _TURN_ACCUMULATORS:
        _TURN_ACCUMULATORS[key] = TurnEvidenceAccumulator()
    return _TURN_ACCUMULATORS[key]


def clear_turn_accumulator(org_id: str, conversation_id: str) -> TurnEvidenceAccumulator:
    key = f"{org_id}:{conversation_id}"
    acc = _TURN_ACCUMULATORS.pop(key, TurnEvidenceAccumulator())
    return acc


def get_cached_evidence(
    org_id: str,
    conversation_id: str,
    *,
    source: str,
    query: str,
    entity_type: str | None = None,
) -> list[EvidenceHit] | None:
    r = get_redis_sync()
    key = _cache_key(org_id, conversation_id, source, query, entity_type)
    raw = r.get(key)
    if not raw:
        return None
    try:
        data = json.loads(raw)
        if not isinstance(data, list):
            return None
        return [EvidenceHit.from_dict(item) for item in data if isinstance(item, dict)]
    except json.JSONDecodeError:
        return None


def store_conversation_evidence(
    org_id: str,
    conversation_id: str,
    *,
    source: str,
    query: str,
    hits: list[EvidenceHit],
    entity_type: str | None = None,
) -> list[EvidenceHit]:
    sanitized = [sanitize_hit(h) for h in hits]
    if not sanitized:
        return []
    settings = get_settings()
    r = get_redis_sync()
    key = _cache_key(org_id, conversation_id, source, query, entity_type)
    r.setex(
        key,
        settings.agent_evidence_conversation_ttl_seconds,
        json.dumps([h.to_dict() for h in sanitized]),
    )
    get_turn_accumulator(org_id, conversation_id).add(sanitized)
    return sanitized


def hits_to_tool_json(hits: list[EvidenceHit], *, cached: bool = False) -> str:
    payload = {
        "cached": cached,
        "count": len(hits),
        "hits": [
            {
                "id": h.id,
                "title": h.title,
                "snippet": h.snippet[:400],
                "uri": h.uri,
                "provider": h.provider,
                "fetched_at": h.fetched_at,
            }
            for h in hits[:12]
        ],
    }
    return json.dumps(payload, default=str)


def persist_turn_evidence(
    org_id: str,
    conversation_id: str,
    accumulator: TurnEvidenceAccumulator,
    *,
    used_refs: set[str] | None = None,
    answer: str = "",
) -> int:
    settings = get_settings()
    used_refs = used_refs or set()
    if answer:
        used_refs.update(re.findall(r"\[(kb:[^\]]+)\]", answer))

    to_persist: list[EvidenceHit] = []
    for hit in accumulator.hits:
        if not hit.persist_eligible:
            continue
        if hit.source in {"connector", "web", "canonical"}:
            to_persist.append(hit)
        elif hit.uri in used_refs or hit.uri.replace("agent_evidence:", "kb:") in used_refs:
            to_persist.append(hit)

    persisted = 0
    for hit in to_persist[: settings.agent_evidence_max_persist_per_turn]:
        uri = hit.uri if hit.uri.startswith("agent_evidence:") else (
            f"agent_evidence:{hit.provider}:{hit.id}"
        )
        query_hash = hashlib.sha256(_normalize_query(hit.title).encode()).hexdigest()[:16]
        ingest_knowledge(
            org_id,
            kind=AGENT_SEARCH_EVIDENCE_KIND,
            title=f"{hit.provider}: {hit.title}"[:200],
            text=hit.snippet,
            feature_origin="agent",
            uri=uri,
            metadata={
                "conversation_id": conversation_id,
                "provider": hit.provider,
                "source": hit.source,
                "fetched_at": hit.fetched_at,
                "entity_type": hit.entity_type,
                "source_query_hash": query_hash,
            },
        )
        persisted += 1
    if persisted:
        logger.info(
            "persisted_agent_evidence org=%s conversation=%s count=%d",
            org_id,
            conversation_id,
            persisted,
        )
    return persisted
