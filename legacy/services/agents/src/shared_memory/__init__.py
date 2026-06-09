"""Shared company knowledge base (Supabase + pgvector) for GTM and Marketing agents."""

from shared_memory.kb import (
    KB_EMBEDDING_DIM,
    embed_text,
    kb_facts,
    kb_insert,
    kb_search,
)

__all__ = [
    "KB_EMBEDDING_DIM",
    "embed_text",
    "kb_facts",
    "kb_insert",
    "kb_search",
]
