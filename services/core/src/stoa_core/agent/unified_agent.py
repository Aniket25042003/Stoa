from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from stoa_core.agent.evidence import clear_turn_accumulator, persist_turn_evidence
from stoa_core.agent.route import classify_agent_route
from stoa_core.agent.tools.registry import AGENT_MEMORY_KINDS, build_agent_tools
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.conversation import maybe_checkpoint_conversation
from stoa_core.llm.router import load_config
from stoa_core.rag.answer import answer_question
from stoa_core.rag.query_prepare import PreparedQuery, retrieve_context_prepared

logger = logging.getLogger(__name__)

SHORT_TERM_CHAR_BUDGET = 14000
SHORT_TERM_RECENT_MESSAGES = 28


@dataclass
class UnifiedAgentResult:
    answer: str
    citations: list[str]
    used_tools: list[str]
    tool_events: list[dict[str, Any]]
    route: str = "tools"
    retrieved_context: list[dict[str, Any]] | None = None
    prepared_query: PreparedQuery | None = None


def _build_chat_model(task_tier: str = "premium") -> Any | None:
    cfg = load_config()

    try:
        from langchain_google_vertexai import ChatVertexAI
    except Exception:
        ChatVertexAI = None  # type: ignore[assignment]

    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        ChatOpenAI = None  # type: ignore[assignment]

    for provider in cfg.fallback_chain:
        model = cfg.model_for(provider, task_tier)  # type: ignore[arg-type]
        try:
            if provider == "vertex" and ChatVertexAI is not None:
                kwargs: dict[str, Any] = {
                    "model": model or cfg.vertex_model,
                    "temperature": cfg.temperature,
                    "request_timeout": cfg.timeout_seconds,
                }
                if cfg.vertex_project:
                    kwargs["project"] = cfg.vertex_project
                if cfg.vertex_location:
                    kwargs["location"] = cfg.vertex_location
                return ChatVertexAI(**kwargs)

            if provider == "openai" and ChatOpenAI is not None and os.getenv("OPENAI_API_KEY"):
                return ChatOpenAI(
                    model=model or cfg.openai_model or "gpt-4o-mini",
                    temperature=cfg.temperature,
                    timeout=cfg.timeout_seconds,
                )
        except Exception as exc:
            logger.warning("Unable to initialize %s model for unified agent: %s", provider, exc)

    return None


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
) -> tuple[list[dict[str, Any]], PreparedQuery, str]:
    """Returns context, prepared query metadata, and retrieval_status."""
    rows = message_rows if message_rows is not None else _load_messages(conversation_id)
    try:
        context, prepared = retrieve_context_prepared(
            org_id,
            question,
            kinds=AGENT_MEMORY_KINDS,
            k=8,
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


def _rag_only_answer(
    org_id: str,
    question: str,
    context: list[dict[str, Any]],
    *,
    retrieval_status: str,
    prepared: PreparedQuery,
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
    )


def _fallback_answer(
    org_id: str,
    question: str,
    conversation_id: str,
    *,
    context: list[dict[str, Any]] | None = None,
    prepared: PreparedQuery | None = None,
    retrieval_status: str = "ok",
) -> UnifiedAgentResult:
    if context is None or prepared is None:
        context, prepared, retrieval_status = _retrieve_for_turn(org_id, question, conversation_id)
    return _rag_only_answer(
        org_id,
        question,
        context,
        retrieval_status=retrieval_status,
        prepared=prepared,
    )


def run_unified_agent_turn(org_id: str, conversation_id: str, question: str) -> UnifiedAgentResult:
    message_rows = _load_messages(conversation_id)
    long_term_context, prepared, retrieval_status = _retrieve_for_turn(
        org_id, question, conversation_id, message_rows=message_rows
    )

    route = classify_agent_route(question, history=message_rows)
    if route == "rag_only":
        result = _rag_only_answer(
            org_id,
            question,
            long_term_context,
            retrieval_status=retrieval_status,
            prepared=prepared,
        )
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        logger.info(
            "agent_turn org=%s conversation=%s route=rag_only rewrite=%s queries=%s context=%d",
            org_id,
            conversation_id,
            prepared.rewrite_used,
            len(prepared.search_queries),
            len(long_term_context),
        )
        return result

    try:
        from langchain.agents import AgentExecutor, create_tool_calling_agent
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    except Exception as exc:
        logger.warning("LangChain agent unavailable; using fallback answer path: %s", exc)
        result = _fallback_answer(
            org_id,
            question,
            conversation_id,
            context=long_term_context,
            prepared=prepared,
            retrieval_status=retrieval_status,
        )
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        return result

    llm = _build_chat_model("premium")
    if llm is None:
        logger.warning("No available tool-capable chat model; using fallback answer path")
        result = _fallback_answer(
            org_id,
            question,
            conversation_id,
            context=long_term_context,
            prepared=prepared,
            retrieval_status=retrieval_status,
        )
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        return result

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
                    "Use get_workspace_freshness when data may be stale. "
                    "Use search_workspace_memory for additional KB retrieval mid-turn. "
                    "Use search_connected_sources for live connector data when memory "
                    "is insufficient. "
                    "Use lookup_canonical_records for exact CRM entity lookups. "
                    "Use refresh_* tools to queue background syncs (disclose refresh-in-progress). "
                    "Dashboard tools cover ICP, content, competitive, campaigns, and alignment. "
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

    try:
        agent = create_tool_calling_agent(llm, tools, prompt)
        executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
            max_iterations=8,
        )

        raw = executor.invoke(
            {
                "input": question,
                "chat_history": chat_history,
                "long_term_context": long_term_block,
            }
        )
        answer = str(raw.get("output") or "").strip() or "I couldn't generate a response right now."

        used_tools: list[str] = []
        tool_events: list[dict[str, Any]] = []
        for step in raw.get("intermediate_steps") or []:
            try:
                action, observation = step
                tool_name = str(getattr(action, "tool", ""))
                if tool_name:
                    used_tools.append(tool_name)
                    tool_events.append(
                        {
                            "tool": tool_name,
                            "observation_preview": str(observation)[:400],
                        }
                    )
            except Exception:
                continue

        citations = _collect_citations(answer, long_term_context)
        _finalize_turn(org_id, conversation_id, answer, citations)
        logger.info(
            "agent_turn org=%s conversation=%s route=tools rewrite=%s tools=%s context=%d",
            org_id,
            conversation_id,
            prepared.rewrite_used,
            sorted(set(used_tools)),
            len(long_term_context),
        )
        return UnifiedAgentResult(
            answer=answer,
            citations=citations,
            used_tools=sorted(set(used_tools)),
            tool_events=tool_events,
            route="tools",
            retrieved_context=long_term_context,
            prepared_query=prepared,
        )
    except Exception as exc:
        logger.exception("Unified agent execution failed; falling back: %s", exc)
        result = _fallback_answer(
            org_id,
            question,
            conversation_id,
            context=long_term_context,
            prepared=prepared,
            retrieval_status=retrieval_status,
        )
        _finalize_turn(org_id, conversation_id, result.answer, result.citations)
        return result
