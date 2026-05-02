"""LangSmith observability helpers for the GTM agent package.

Uses official LangSmith patterns: tracing_context, trace, traceable, metadata/tags.
Instrumentation is best-effort: failures or missing deps never break the pipeline.

References:
- https://docs.langchain.com/oss/python/langgraph/observability
- https://docs.langchain.com/langsmith/annotate-code
- https://docs.langchain.com/langsmith/add-metadata-tags
- https://docs.langchain.com/langsmith/conditional-tracing
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Callable, Iterator, TypeVar

# Sensitive key substrings (lowercase)
_REDACT_KEY_SUBSTRINGS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "authorization",
    "bearer",
    "credential",
    "service_role",
    "jwt",
    "private_key",
)

F = TypeVar("F", bound=Callable[..., Any])

try:
    import langsmith as ls  # type: ignore[import-untyped]
    from langsmith import traceable  # type: ignore[import-untyped]

    _LANGSMITH_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    ls = None  # type: ignore[assignment]
    traceable = None  # type: ignore[assignment]
    _LANGSMITH_AVAILABLE = False


def langsmith_installed() -> bool:
    return _LANGSMITH_AVAILABLE


def tracing_enabled_from_env() -> bool:
    """True when LangSmith tracing is explicitly enabled via env."""
    v = (os.getenv("LANGSMITH_TRACING") or "").strip().lower()
    if v in ("true", "1", "yes"):
        return True
    # Legacy LangChain tracing flag (still honored in worker bootstrap)
    lc = (os.getenv("LANGCHAIN_TRACING_V2") or "").strip().lower()
    return lc in ("true", "1", "yes")


def sync_langsmith_env_from_legacy() -> None:
    """Map legacy LANGCHAIN_* tracing vars to LANGSMITH_* when the latter are unset.

    Official tracing uses LANGSMITH_TRACING and LANGSMITH_API_KEY.
    """
    if (os.getenv("LANGSMITH_TRACING") or "").strip().lower() not in ("true", "1", "yes"):
        lc = (os.getenv("LANGCHAIN_TRACING_V2") or "").strip().lower()
        if lc in ("true", "1", "yes"):
            os.environ.setdefault("LANGSMITH_TRACING", "true")
    if not (os.getenv("LANGSMITH_API_KEY") or "").strip():
        lk = (os.getenv("LANGCHAIN_API_KEY") or "").strip()
        if lk:
            os.environ.setdefault("LANGSMITH_API_KEY", lk)
    if not (os.getenv("LANGSMITH_PROJECT") or "").strip():
        proj = (os.getenv("LANGCHAIN_PROJECT") or "").strip()
        if proj:
            os.environ.setdefault("LANGSMITH_PROJECT", proj)


def _should_redact_key(key: str) -> bool:
    lower = key.lower()
    return any(s in lower for s in _REDACT_KEY_SUBSTRINGS)


def redact_value(obj: Any, max_depth: int = 6, _depth: int = 0) -> Any:
    """Recursively redact secrets and bound size for trace payloads."""
    if _depth > max_depth:
        return "<max_depth>"
    if obj is None or isinstance(obj, (bool, int, float)):
        return obj
    if isinstance(obj, str):
        if len(obj) > 2000:
            return obj[:2000] + "…(truncated)"
        return obj
    if isinstance(obj, (list, tuple)):
        out = [redact_value(x, max_depth, _depth + 1) for x in obj[:100]]
        if len(obj) > 100:
            out.append(f"<{len(obj) - 100} more items>")
        return out
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in list(obj.items())[:200]:
            if _should_redact_key(str(k)):
                out[str(k)] = "<redacted>"
            else:
                out[str(k)] = redact_value(v, max_depth, _depth + 1)
        if len(obj) > 200:
            out["_truncated_keys"] = len(obj) - 200
        return out
    return str(obj)[:500]


def summarize_run_input(inp: dict[str, Any] | None) -> dict[str, Any]:
    """Bounded summary of founder input for trace metadata (not full dump)."""
    if not inp:
        return {}
    keys = (
        "product_name",
        "product_description",
        "website_url",
        "target_customers",
        "geography",
        "business_model",
        "stage",
        "horizon_days",
    )
    out: dict[str, Any] = {}
    for k in keys:
        v = inp.get(k)
        if v is None:
            continue
        if k == "product_description" and isinstance(v, str):
            out[k] = v[:800] + ("…" if len(v) > 800 else "")
        else:
            out[k] = v
    return redact_value(out)  # type: ignore[return-value]


def base_tags() -> list[str]:
    return ["gtm-agent", "celery-worker"]


def base_metadata(run_id: str | None, user_id: str | None, **extra: Any) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "run_id": run_id,
        "user_id": user_id,
        "environment": os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("VERCEL_ENV") or os.getenv("ENV", "development"),
    }
    meta.update({k: v for k, v in extra.items() if v is not None})
    return redact_value(meta)  # type: ignore[return-value]


def graph_invoke_config(run_id: str | None, user_id: str | None) -> dict[str, Any]:
    """Config dict for LangGraph invoke: tags + metadata per LangGraph observability docs."""
    return {
        "tags": base_tags() + (["run:" + str(run_id)] if run_id else []),
        "metadata": base_metadata(run_id, user_id),
    }


@contextmanager
def pipeline_tracing_context(
    run_id: str | None,
    user_id: str | None,
    *,
    project_name: str | None = None,
    enabled: bool | None = None,
) -> Iterator[None]:
    """Apply tracing_context for the whole pipeline when LangSmith is available."""
    sync_langsmith_env_from_legacy()
    if not _LANGSMITH_AVAILABLE:
        yield
        return
    should = tracing_enabled_from_env() if enabled is None else bool(enabled)
    if not should:
        yield
        return
    proj = project_name or (os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "").strip() or None
    meta = base_metadata(run_id, user_id)
    tags = base_tags()
    try:
        with ls.tracing_context(  # type: ignore[union-attr]
            enabled=True,
            project_name=proj,
            tags=tags,
            metadata=meta,
        ):
            yield
    except Exception:
        yield


@contextmanager
def root_trace(
    name: str,
    run_type: str,
    inputs: dict[str, Any],
    *,
    project_name: str | None = None,
) -> Iterator[Any]:
    """Optional root span (ls.trace) for Celery task; no-op if LangSmith unavailable."""
    sync_langsmith_env_from_legacy()
    if not _LANGSMITH_AVAILABLE or not tracing_enabled_from_env():
        yield None
        return
    proj = project_name or (os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "").strip() or None
    try:
        with ls.trace(  # type: ignore[union-attr]
            name,
            run_type,
            inputs=redact_value(inputs),
            project_name=proj,
            tags=base_tags(),
        ) as rt:
            yield rt
    except Exception:
        yield None


def get_current_trace_correlation() -> dict[str, Any]:
    """Best-effort trace/run ids for correlating with Supabase events."""
    sync_langsmith_env_from_legacy()
    if not _LANGSMITH_AVAILABLE or not tracing_enabled_from_env():
        return {}
    try:
        rt = ls.get_current_run_tree()  # type: ignore[union-attr]
        if rt is None:
            return {}
        trace_id = getattr(rt, "trace_id", None) or getattr(rt, "traceId", None)
        run_id = getattr(rt, "id", None)
        out: dict[str, Any] = {}
        if trace_id:
            out["langsmith_trace_id"] = str(trace_id)
        if run_id:
            out["langsmith_run_id"] = str(run_id)
        return out
    except Exception:
        return {}


def flush_traces() -> None:
    """Ensure traces are submitted before worker process teardown (best-effort)."""
    if not _LANGSMITH_AVAILABLE:
        return
    try:
        from langsmith import Client  # type: ignore[import-untyped]

        Client().flush()
    except Exception:
        pass


def traced_tool(name: str | None = None, run_type: str = "tool") -> Callable[[F], F]:
    """Decorator for tool-like functions; falls back to identity when LangSmith is unavailable."""

    def deco(fn: F) -> F:
        if traceable is None:
            return fn
        return traceable(name=name or fn.__name__, run_type=run_type)(fn)  # type: ignore[misc]

    return deco


@contextmanager
def span(name: str, run_type: str, inputs: dict[str, Any]) -> Iterator[Any]:
    """Public context manager for a timed trace span."""
    sync_langsmith_env_from_legacy()
    if not _LANGSMITH_AVAILABLE or not tracing_enabled_from_env():
        yield None
        return
    try:
        with ls.trace(name, run_type, inputs=redact_value(inputs)) as rt:  # type: ignore[union-attr]
            yield rt
    except Exception:
        yield None


def wrap_with_span(name: str, run_type: str, inputs: dict[str, Any], fn: Callable[[], Any]) -> Any:
    """Run fn inside a trace span if tracing is on; otherwise run fn()."""
    if not _LANGSMITH_AVAILABLE or not tracing_enabled_from_env():
        return fn()
    try:
        with ls.trace(name, run_type, inputs=redact_value(inputs)) as rt:  # type: ignore[union-attr]
            try:
                out = fn()
            except Exception as e:
                if rt is not None and hasattr(rt, "end"):
                    try:
                        rt.end(error=str(e))
                    except Exception:
                        pass
                raise
            if rt is not None and hasattr(rt, "end"):
                try:
                    rt.end(outputs=redact_value({"result": out}))
                except Exception:
                    pass
            return out
    except Exception:
        return fn()
