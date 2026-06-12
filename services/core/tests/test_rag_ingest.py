from unittest.mock import MagicMock, patch

from stoa_core.rag.ingest import content_hash, ingest_knowledge, profile_to_knowledge_text


def test_content_hash_stable():
    assert content_hash("hello") == content_hash("hello")
    assert content_hash("hello") != content_hash("world")


def test_profile_to_knowledge_text():
    text = profile_to_knowledge_text(
        {
            "name": "Acme",
            "website_url": "https://acme.com",
            "industry": "SaaS",
            "profile": {"brand_voice": "Direct", "goals": "Expand ICP"},
        },
        user_profile={"role_type": "founder", "use_case": "ICP research"},
    )
    assert "Acme" in text
    assert "Brand Voice" in text
    assert "Primary use case" in text


@patch("stoa_core.rag.ingest.bump_kb_version")
@patch("stoa_core.rag.ingest.embed_texts", return_value=[[0.1] * 3072])
@patch("stoa_core.rag.ingest.get_supabase_admin")
def test_ingest_knowledge_idempotent_skip(mock_sb, mock_embed, mock_bump):
    sb = MagicMock()
    mock_sb.return_value = sb
    limit_chain = sb.table.return_value.select.return_value.eq.return_value.eq.return_value.limit
    limit_chain.return_value.execute.return_value = MagicMock(
        data=[{"id": "item-1", "content_hash": content_hash("same text"), "version": 1}]
    )

    result = ingest_knowledge(
        "org-1",
        kind="document",
        title="Doc",
        text="same text",
        uri="document:doc-1",
    )
    assert result["id"] == "item-1"
    mock_embed.assert_not_called()
