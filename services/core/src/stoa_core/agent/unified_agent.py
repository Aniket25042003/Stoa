from __future__ import annotations

import logging
import re
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from stoa_core.agent.bounded_agent import run_bounded_agent_turn
from stoa_core.agent.evidence import clear_turn_accumulator, persist_turn_evidence
from stoa_core.agent.precomputed_context import (
    build_enriched_context,
    build_structured_rag_prefix,
    load_matched_insight,
    synthesize_from_enriched_context,
)
from stoa_core.agent.progress import AgentProgressCallback
from stoa_core.agent.route_resolver import RouteDecision, resolve_agent_route
from stoa_core.agent.tools.registry import AGENT_MEMORY_KINDS, build_agent_tools
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.conversation import maybe_checkpoint_conversation
from stoa_core.llm.content import extract_text_content
from stoa_core.llm.langchain_chat import build_chat_model
from stoa_core.rag.answer import answer_question
from stoa_core.rag.query_prepare import PreparedQuery, retrieve_context_prepared
from stoa_core.rag.retrieve import retrieve_context

logger = logging.getLogger(__name__)

SHORT_TERM_CHAR_BUDGET = 14000
SHORT_TERM_RECENT_MESSAGES = 28
HIGH_ROUTE_CONFIDENCE = 0.8


@dataclass
class UnifiedAgentResult:
    answer: str
    citations: list[str]
    used_tools: list[str]
    tool_events: list[dict[str, Any]]
    route: str = "tools"
    retrieved_context: list[dict[str, Any]] | None = None
    prepared_query: PreparedQuery | None = None
    route_reason: str = ""
    matched_insight_key: str | None = None
    llm_calls_estimate: int = 0
    duration_ms: int = 0


def _load_messages(conversation_id: str, *, limit: int = 80) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("messages")
        .select("role, content, created_at")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    rows = list(reversed(res.data or []))
    return [r for r in rows if isinstance(r, dict)]


def _compact_older_messages(rows: list[dict[str, Any]]) -> str | None:
    if not rows:
        return None
    snippets: list[str] = []
    for row in rows[-12:]:
        role = (row.get("role") or "user").strip().lower()
        txt = str(row.get("content") or "").strip().replace("\n", " ")
        if not txt:
            continue
        snippets.append(f"{role}: {txt[:180]}")
    if not snippets:
        return None
    return " | ".join(snippets)


def _build_short_term_history(conversation_id: str) -> list[Any]:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    rows = _load_messages(conversation_id)
    if not rows:
        return []

    total_chars = 0
    kept: list[dict[str, Any]] = []
    for row in reversed(rows):
        content = str(row.get("content") or "")
        if not content:
            continue
        if kept and total_chars + len(content) > SHORT_TERM_CHAR_BUDGET:
            break
        kept.append(row)
        total_chars += len(content)
        if len(kept) >= SHORT_TERM_RECENT_MESSAGES:
            break
    kept.reverse()

    older_count = max(0, len(rows) - len(kept))
    history: list[Any] = []
    if older_count > 0:
        compacted = _compact_older_messages(rows[:older_count])
        if compacted:
            history.append(
                SystemMessage(
                    content=(
                        "Compacted prior conversation context (older messages beyond active "
                        "window): " + compacted
                    )
                )
            )

    for row in kept:
        role = (row.get("role") or "user").strip().lower()
        content = str(row.get("content") or "")
        if role == "assistant":
            history.append(AIMessage(content=content))
        elif role == "system":
            history.append(SystemMessage(content=content))
        else:
            history.append(HumanMessage(content=content))

    return history


def _history_snippets(rows: list[dict[str, Any]]) -> list[str]:
    return [
        f"{row.get('role', 'user')}: {str(row.get('content') or '')[:180]}"
        for row in rows[-4:]
        if row.get("content")
    ]


def _finalize_turn(
    org_id: str,
    conversation_id: str,
    answer: str,
    citations: list[str],
) -> None:
    acc = clear_turn_accumulator(org_id, conversation_id)
    persist_turn_evidence(
        org_id,
        conversation_id,
        acc,
        used_refs=set(citations),
        answer=answer,
    )
    maybe_checkpoint_conversation(org_id, conversation_id)


def _collect_citations(answer: str, long_term_context: list[dict[str, Any]]) -> list[str]:
    refs = set(re.findall(r"\[(kb:[^\]]+)\]", answer or ""))
    for item in long_term_context[:8]:
        ref = item.get("ref")
        if isinstance(ref, str) and ref:
            refs.add(ref)
    return sorted(refs)[:20]


def _retrieve_for_turn(
    org_id: str,
    question: str,
    conversation_id: str,
    *,
    message_rows: list[dict[str, Any]] | None = None,
    k: int = 8,
) -> tuple[list[dict[str, Any]], PreparedQuery, str]:
    rows = message_rows if message_rows is not None else _load_messages(conversation_id)
    try:
        context, prepared = retrieve_context_prepared(
            org_id,
            question,
            kinds=AGENT_MEMORY_KINDS,
            k=k,
            conversation_id=conversation_id,
            history=rows,
        )
        status = "ok" if context else "no_matches"
        return context, prepared, status
    except Exception as exc:
        from stoa_core.ingestion.embed import EmbeddingUnavailableError

        if isinstance(exc, EmbeddingUnavailableError):
            prepared = PreparedQuery(question, question, [question], False)
            return [], prepared, "embedding_unavailable"
        raise


def _merge_context(
    primary: list[dict[str, Any]],
    extra: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    merged: list[dict[str, Any]] = []
    for item in [*extra, *primary]:
        ref = str(item.get("ref") or "")
        if ref and ref in seen:
            continue
        if ref:
            seen.add(ref)
        merged.append(item)
    return merged


def _rag_only_answer(
    org_id: str,
    question: str,
    context: list[dict[str, Any]],
    *,
    retrieval_status: str,
    prepared: PreparedQuery,
    llm_calls: int = 1,
) -> UnifiedAgentResult:
    answer = answer_question(
        question,
        context,
        org_id=org_id,
        kinds=AGENT_MEMORY_KINDS,
        retrieval_status=retrieval_status,
    )
    citations = [str(c.get("ref")) for c in context[:10] if isinstance(c.get("ref"), str)]
    return UnifiedAgentResult(
        answer=answer,
        citations=citations,
        used_tools=[],
        tool_events=[],
        route="rag_only",
        retrieved_context=context,
        prepared_query=prepared,
        llm_calls_estimate=llm_calls + (1 if prepared.rewrite_used else 0),
    )


def _precomputed_enriched_answer(
    org_id: str,
    conversation_id: str,
    question: str,
    decision: RouteDecision,
    message_rows: list[dict[str, Any]],
    *,
    on_progress: Callable[[dict[str, Any]], None] | None,
) -> UnifiedAgentResult:
    if on_progress:
        on_progress({"status": "thinking", "message": "Using prepared intelligence…"})

    insight = load_matched_insight(
        org_id,
        decision.matched_insight_key or "",
        decision.matched_scope or "intelligence",
    )
    if insight is None:
        context, prepared, status = _retrieve_for_turn(
            org_id, question, conversation_id, message_rows=message_rows
        )
        return _rag_only_answer(
            org_id,
            question,
            context,
            retrieval_status=status,
            prepared=prepared,
        )

    skip_retrieval = decision.confidence >= HIGH_ROUTE_CONFIDENCE
    enriched = build_enriched_context(
        org_id,
        insight,
        question,
        light_retrieval_k=4,
        skip_retrieval=skip_retrieval,
    )
    prepared = PreparedQuery(question, question, [question], False)

    if on_progress:
        on_progress({"status": "thinking", "message": "Synthesizing answer…"})

    answer = synthesize_from_enriched_context(
        question,
        enriched,
        history_snippets=_history_snippets(message_rows),
    )
    citations = _collect_citations(answer, enriched)
    insight_citations = insight.get("citations") or []
    if isinstance(insight_citations, list):
        for c in insight_citations:
            if isinstance(c, str) and c not in citations:
                citations.append(c)

    return UnifiedAgentResult(
        answer=answer,
        citations=citations[:20],
        used_tools=[],
        tool_events=[],
        route="precomputed_enriched",
        retrieved_context=enriched,
        prepared_query=prepared,
        route_reason=decision.reason,
        matched_insight_key=decision.matched_insight_key,
        llm_calls_estimate=1,
    )


def _run_react_agent(
    org_id: str,
    conversation_id: str,
    question: str,
    long_term_context: list[dict[str, Any]],
    prepared: PreparedQuery,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None,
) -> UnifiedAgentResult:
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = build_chat_model("premium")
    if llm is None:
        raise RuntimeError("No chat model available for react agent")

    if on_progress:
        on_progress({"status": "thinking", "message": "Planning tool strategy…"})

    tools = build_agent_tools(org_id, conversation_id)
    chat_history = _build_short_term_history(conversation_id)
    long_term_block = "\n".join(
        f"[{c.get('ref')}] {c.get('text', '')[:260]}" for c in long_term_context
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are Stoa's unified GTM Agent with tiered tools. "
                    "Use dashboard tools for ICP, campaigns, competitive, and alignment. "
                    "Avoid redundant search_workspace_memory when context is already rich. "
                    "Prefer quantitative metrics and cite evidence refs when available."
                ),
            ),
            (
                "system",
                "Long-term memory context from Supabase/pgvector retrieval:\n{long_term_context}",
            ),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        max_iterations=3,
    )

    progress_handler = AgentProgressCallback(on_progress) if on_progress else None
    invoke_config = {"callbacks": [progress_handler]} if progress_handler else {}
    raw = executor.invoke(
        {
            "input": question,
            "chat_history": chat_history,
            "long_term_context": long_term_block,
        },
        config=invoke_config,
    )
    answer = extract_text_content(raw.get("output")).strip() or (
        "I couldn't generate a response right now."
    )

    used_tools: list[str] = list(progress_handler.used_tools) if progress_handler else []
    tool_events: list[dict[str, Any]] = []
    for step in raw.get("intermediate_steps") or []:
        try:
            action, observation = step
            tool_name = str(getattr(action, "tool", ""))
            if tool_name and tool_name not in used_tools:
                used_tools.append(tool_name)
            if tool_name:
                tool_events.append(
                    {
                        "tool": tool_name,
                        "observation_preview": str(observation)[:400],
                    }
                )
        except Exception:
            continue

    citations = _collect_citations(answer, long_term_context)
    return UnifiedAgentResult(
        answer=answer,
        citations=citations,
        used_tools=sorted(set(used_tools)),
        tool_events=tool_events,
        route="tools_react",
        retrieved_context=long_term_context,
        prepared_query=prepared,
        llm_calls_estimate=4,
    )


def _log_turn(
    org_id: str,
    conversation_id: str,
    result: UnifiedAgentResult,
    *,
    prepared: PreparedQuery | None,
) -> None:
    logger.info(
        "agent_turn org=%s conversation=%s route=%s reason=%s insight_key=%s "
        "llm_calls_est=%d tools=%s rewrite=%s queries=%s context=%d duration_ms=%d",
        org_id,
        conversation_id,
        result.route,
        result.route_reason,
        result.matched_insight_key,
        result.llm_calls_estimate,
        sorted(set(result.used_tools)),
        prepared.rewrite_used if prepared else False,
        len(prepared.search_queries) if prepared else 0,
        len(result.retrieved_context or []),
        result.duration_ms,
    )


def run_unified_agent_turn(
    org_id: str,
    conversation_id: str,
    question: str,
    *,
    on_progress: Callable[[dict[str, Any]], None] | None = None,
) -> UnifiedAgentResult:
    started = time.monotonic()
    message_rows = _load_messages(conversation_id)

    if on_progress:
        on_progress({"status": "thinking", "message": "Analyzing your question…"})

    decision = resolve_agent_route(org_id, question, history=message_rows)

    if decision.route == "precomputed_enriched":
        result = _precomputed_enriched_answer(
            org_id,
            conversation_id,
            question,
            decision,
            message_rows,
            on_progress=on_progress,
        )
        result.route_reason = decision.reason
        result.duration_ms = int((time.monotonic() - started) * 1000)
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        _log_turn(org_id, conversation_id, result, prepared=result.prepared_query)
        return result

    long_term_context, prepared, retrieval_status = _retrieve_for_turn(
        org_id, question, conversation_id, message_rows=message_rows
    )
    structured_prefix = build_structured_rag_prefix(org_id, question)
    if structured_prefix:
        long_term_context = _merge_context(long_term_context, structured_prefix)

    if decision.route == "rag_only":
        if on_progress:
            on_progress({"status": "thinking", "message": "Synthesizing answer…"})
        result = _rag_only_answer(
            org_id,
            question,
            long_term_context,
            retrieval_status=retrieval_status,
            prepared=prepared,
        )
        result.route_reason = decision.reason
        result.duration_ms = int((time.monotonic() - started) * 1000)
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        _log_turn(org_id, conversation_id, result, prepared=prepared)
        return result

    if decision.route == "tools_bounded":
        try:
            bounded = run_bounded_agent_turn(
                org_id,
                conversation_id,
                question,
                long_term_context,
                on_progress=on_progress,
            )
            citations = _collect_citations(bounded.answer, long_term_context)
            result = UnifiedAgentResult(
                answer=bounded.answer,
                citations=citations,
                used_tools=bounded.used_tools,
                tool_events=bounded.tool_events,
                route="tools_bounded",
                retrieved_context=long_term_context,
                prepared_query=prepared,
                route_reason=bounded.plan_reason or decision.reason,
                llm_calls_estimate=2,
            )
            result.duration_ms = int((time.monotonic() - started) * 1000)
            _finalize_turn(org_id, conversation_id, result.answer, result.citations)
            _log_turn(org_id, conversation_id, result, prepared=prepared)
            return result
        except Exception as exc:
            logger.warning("Bounded agent failed; falling back to react agent: %s", exc)

    try:
        result = _run_react_agent(
            org_id,
            conversation_id,
            question,
            long_term_context,
            prepared,
            on_progress=on_progress,
        )
        result.route_reason = decision.reason
        result.duration_ms = int((time.monotonic() - started) * 1000)
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        _log_turn(org_id, conversation_id, result, prepared=prepared)
        return result
    except Exception as exc:
        logger.exception("Unified agent execution failed; falling back to RAG: %s", exc)
        result = _rag_only_answer(
            org_id,
            question,
            long_term_context,
            retrieval_status=retrieval_status,
            prepared=prepared,
        )
        result.route_reason = "rag_fallback"
        result.duration_ms = int((time.monotonic() - started) * 1000)
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        _log_turn(org_id, conversation_id, result, prepared=prepared)
        return result
