"""
File: services/core/src/stoa_core/ingestion/embed.py
Layer: Core Ingestion Pipeline
Purpose: Implements embed behavior for the core ingestion pipeline.
Dependencies: stoa_core
"""


from __future__ import annotations

import logging
from typing import Any

from stoa_core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingUnavailableError(RuntimeError):
    """Raised when no embedding provider can produce a query vector."""


def embed_texts(
    texts: list[str],
    *,
    task_type: str | None = None,
) -> list[list[float]]:
    """Handles embed texts logic for the surrounding Stoa workflow.

    Args:
        texts (list[str]): Input value used by this workflow step.
        task_type (str | None): Input value used by this workflow step.

    Returns:
        list[list[float]]: Result produced for the caller.
    """
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
    """Handles embed query logic for the surrounding Stoa workflow.

    Args:
        text (str): Input value used by this workflow step.

    Returns:
        list[float]: Result produced for the caller.
    """
    settings = get_settings()
    result = embed_texts([text], task_type=settings.embed_task_query)
    if not result:
        raise EmbeddingUnavailableError("No embedding returned for query")
    vector = result[0]
    if not vector or all(v == 0.0 for v in vector):
        raise EmbeddingUnavailableError("Embedding providers returned a zero vector")
    return vector


def _embed_batch(texts: list[str], *, task_type: str, dimensions: int) -> list[list[float]]:
    """Handles  embed batch logic for the surrounding Stoa workflow.

    Args:
        texts (list[str]): Input value used by this workflow step.
        task_type (str): Input value used by this workflow step.
        dimensions (int): Input value used by this workflow step.

    Returns:
        list[list[float]]: Result produced for the caller.
    """
    vertex = _vertex_embed(texts, task_type=task_type, dimensions=dimensions)
    if vertex is not None:
        return vertex
    openai = _openai_embed(texts, dimensions=dimensions)
    if openai is not None:
        return openai
    logger.warning("No embedding provider available for batch of %d texts", len(texts))
    raise EmbeddingUnavailableError("No embedding provider available")


def _vertex_embed(texts: list[str], *, task_type: str, dimensions: int) -> list[list[float]] | None:
    """Handles  vertex embed logic for the surrounding Stoa workflow.

    Args:
        texts (list[str]): Input value used by this workflow step.
        task_type (str): Input value used by this workflow step.
        dimensions (int): Input value used by this workflow step.

    Returns:
        list[list[float]] | None: Result produced for the caller.
    """
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
    """Handles  openai embed logic for the surrounding Stoa workflow.

    Args:
        texts (list[str]): Input value used by this workflow step.
        dimensions (int): Input value used by this workflow step.

    Returns:
        list[list[float]] | None: Result produced for the caller.
    """
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
    """Handles  zero vector logic for the surrounding Stoa workflow.

    Args:
        dim (int): Input value used by this workflow step.

    Returns:
        list[float]: Result produced for the caller.
    """
    return [0.0] * dim


def _zero_vectors(n: int, dim: int) -> list[list[float]]:
    """Handles  zero vectors logic for the surrounding Stoa workflow.

    Args:
        n (int): Input value used by this workflow step.
        dim (int): Input value used by this workflow step.

    Returns:
        list[list[float]]: Result produced for the caller.
    """
    return [_zero_vector(dim) for _ in range(n)]
