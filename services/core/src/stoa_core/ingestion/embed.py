"""Embedding generation (gemini-embedding-001 @ 3072 dims)."""

from __future__ import annotations

import logging
from typing import Any

from stoa_core.config import get_settings

logger = logging.getLogger(__name__)


def embed_texts(
    texts: list[str],
    *,
    task_type: str | None = None,
) -> list[list[float]]:
    if not texts:
        return []
    settings = get_settings()
    task = task_type or settings.embed_task_doc
    dim = settings.embed_dimensions
    batch_size = settings.embed_batch_size

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        batch_emb = _embed_batch(batch, task_type=task, dimensions=dim)
        all_embeddings.extend(batch_emb)
    return all_embeddings


def embed_query(text: str) -> list[float]:
    settings = get_settings()
    result = embed_texts([text], task_type=settings.embed_task_query)
    return result[0] if result else _zero_vector(settings.embed_dimensions)


def _embed_batch(texts: list[str], *, task_type: str, dimensions: int) -> list[list[float]]:
    vertex = _vertex_embed(texts, task_type=task_type, dimensions=dimensions)
    if vertex is not None:
        return vertex
    openai = _openai_embed(texts, dimensions=dimensions)
    if openai is not None:
        return openai
    logger.warning("No embedding provider available; returning zero vectors")
    return _zero_vectors(len(texts), dimensions)


def _vertex_embed(texts: list[str], *, task_type: str, dimensions: int) -> list[list[float]] | None:
    settings = get_settings()
    try:
        import vertexai
        from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
    except Exception as exc:
        logger.debug("Vertex embedding SDK unavailable: %s", exc)
        return None

    try:
        project = settings.vertex_project
        location = settings.vertex_location
        if project:
            vertexai.init(project=project, location=location)
        model = TextEmbeddingModel.from_pretrained(settings.embed_model)
        inputs = [TextEmbeddingInput(text=t[:8000], task_type=task_type) for t in texts]
        kwargs: dict[str, Any] = {}
        if dimensions:
            kwargs["output_dimensionality"] = dimensions
        response = model.get_embeddings(inputs, **kwargs)
        out: list[list[float]] = []
        for emb in response:
            values = list(getattr(emb, "values", []) or [])
            if len(values) < dimensions:
                values = values + [0.0] * (dimensions - len(values))
            out.append(values[:dimensions])
        return out
    except Exception as exc:
        logger.warning("Vertex embedding failed: %s", exc)
        return None


def _openai_embed(texts: list[str], *, dimensions: int) -> list[list[float]] | None:
    import os

    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        from langchain_openai import OpenAIEmbeddings
    except Exception as exc:
        logger.debug("OpenAI embeddings unavailable: %s", exc)
        return None
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=dimensions)
        return embedder.embed_documents(texts)
    except Exception as exc:
        logger.warning("OpenAI embedding failed: %s", exc)
        return None


def _zero_vector(dim: int) -> list[float]:
    return [0.0] * dim


def _zero_vectors(n: int, dim: int) -> list[list[float]]:
    return [_zero_vector(dim) for _ in range(n)]
