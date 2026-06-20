"""
File: services/core/src/stoa_core/ingestion/__init__.py
Layer: Core Ingestion Pipeline
Purpose: Implements   init   behavior for the core ingestion pipeline.
Dependencies: stoa_core
"""

from stoa_core.ingestion.chunk import chunk_text, chunk_text_strings
from stoa_core.ingestion.embed import embed_query, embed_texts
from stoa_core.ingestion.extract import extract_signals

__all__ = ["chunk_text", "chunk_text_strings", "extract_signals", "embed_texts", "embed_query"]
