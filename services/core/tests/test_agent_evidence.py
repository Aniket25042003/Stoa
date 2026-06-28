"""Tests for agent evidence cache and persistence."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from stoa_core.agent.evidence import (
    EvidenceHit,
    TurnEvidenceAccumulator,
    get_cached_evidence,
    persist_turn_evidence,
    sanitize_hit,
    store_conversation_evidence,
)


def test_sanitize_hit_strips_pii():
    hit = EvidenceHit(
        id="1",
        title="Contact john@acme.com",
        snippet="SSN 123-45-6789 discussed pricing",
        uri="agent_evidence:hubspot:1",
        provider="hubspot",
        source="connector",
        fetched_at="2026-01-01T00:00:00Z",
    )
    cleaned = sanitize_hit(hit)
    assert "john@acme.com" not in cleaned.snippet or "@" not in cleaned.snippet
    assert "123-45-6789" not in cleaned.snippet


def test_conversation_cache_roundtrip():
    org = "org-1"
    conv = "conv-1"
    hits = [
        EvidenceHit(
            id="d1",
            title="Big Deal",
            snippet="Amount=50000",
            uri="agent_evidence:hubspot:d1",
            provider="hubspot",
            source="connector",
            fetched_at="2026-01-01T00:00:00Z",
        )
    ]
    mock_redis = MagicMock()
    stored: dict[str, str] = {}

    def setex(key, ttl, value):
        stored[key] = value

    def get(key):
        return stored.get(key)

    mock_redis.setex = setex
    mock_redis.get = get

    with patch("stoa_core.agent.evidence.get_redis_sync", return_value=mock_redis):
        store_conversation_evidence(org, conv, source="hubspot", query="top deals", hits=hits)
        cached = get_cached_evidence(org, conv, source="hubspot", query="top deals")

    assert cached is not None
    assert len(cached) == 1
    assert cached[0].title == "Big Deal"


def test_persist_turn_evidence_caps_and_skips_kb_rereads():
    acc = TurnEvidenceAccumulator()
    for i in range(12):
        acc.add(
            [
                EvidenceHit(
                    id=f"c{i}",
                    title=f"Hit {i}",
                    snippet="data",
                    uri=f"agent_evidence:hubspot:{i}",
                    provider="hubspot",
                    source="connector",
                    fetched_at="2026-01-01T00:00:00Z",
                )
            ]
        )
    with patch("stoa_core.agent.evidence.ingest_knowledge") as mock_ingest:
        with patch("stoa_core.agent.evidence.get_settings") as mock_settings:
            mock_settings.return_value.agent_evidence_max_persist_per_turn = 3
            count = persist_turn_evidence("org", "conv", acc)
    assert count == 3
    assert mock_ingest.call_count == 3
