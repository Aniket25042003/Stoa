"""
File: services/core/src/stoa_core/rag/__init__.py
Layer: Core Retrieval / RAG
Purpose: Implements   init   behavior for the core retrieval / rag.
Dependencies: stoa_core
"""

from stoa_core.rag.answer import answer_question
from stoa_core.rag.ingest import ingest_knowledge, profile_to_knowledge_text
from stoa_core.rag.retrieve import retrieve_context

__all__ = [
    "answer_question",
    "ingest_knowledge",
    "profile_to_knowledge_text",
    "retrieve_context",
]
