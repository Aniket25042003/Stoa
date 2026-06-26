from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from stoa_core.agent.route import classify_agent_route
from stoa_core.alignment.aggregate import build_alignment_summary
from stoa_core.alignment.friction import collect_friction_signals
from stoa_core.analytics.aggregate import build_summary_metrics
from stoa_core.db.supabase import get_supabase_admin
from stoa_core.enrichment.conversation import maybe_checkpoint_conversation
from stoa_core.intelligence.structured import aggregate_crm_stats
from stoa_core.llm.router import load_config
from stoa_core.rag.answer import answer_question
from stoa_core.rag.query_prepare import PreparedQuery, retrieve_context_prepared

logger = logging.getLogger(__name__)

SHORT_TERM_CHAR_BUDGET = 14000
SHORT_TERM_RECENT_MESSAGES = 28

CONVERSATION_MEMORY_KIND = "conversation_memory"

AGENT_MEMORY_KINDS = [
    "document",
    "company_profile",
    "icp_profile",
    "crm_account",
    "crm_contact",
    "crm_deal",
    "call_transcript",
    "support_ticket",
    "review",
    "product_analytics_summary",
    "competitive_snapshot",
    "campaign_asset",
    "campaign_metrics",
    "content_asset",
    CONVERSATION_MEMORY_KIND,
]


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


def _as_rows(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _get_precomputed_insights(org_id: str, scope: str, *, limit: int = 6) -> list[dict[str, Any]]:
    sb = get_supabase_admin()
    res = (
        sb.table("precomputed_insights")
        .select("key, title, content, citations, created_at")
        .eq("org_id", org_id)
        .eq("scope", scope)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _as_rows(res.data)


def _json(data: dict[str, Any]) -> str:
    return json.dumps(data, default=str)


def _feature_tools(org_id: str) -> list[Any]:
    from langchain_core.tools import StructuredTool

    def icp_customer_research_tool(query: str) -> str:
        """Answer ICP and customer research questions from CRM + intelligence insights."""
        stats = aggregate_crm_stats(org_id)
        insights = _get_precomputed_insights(org_id, "intelligence", limit=8)
        best_segment = (stats.get("top_industries") or [{}])[0]
        payload = {
            "feature": "icp_customer_research",
            "query": query,
            "highlights": {
                "best_customer_segment": best_segment.get("name"),
                "total_deals": stats.get("total_deals", 0),
                "win_rate_percent": stats.get("win_rate_percent"),
                "top_loss_reasons": stats.get("top_loss_reasons", []),
            },
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    def content_bottleneck_tool(query: str) -> str:
        """Return content generation bottlenecks and throughput metrics."""
        sb = get_supabase_admin()
        rows = _as_rows(
            (
                sb.table("content_assets")
                .select(
                    "id, status, asset_type, generation_metadata, created_at, updated_at, error"
                )
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(300)
                .execute()
            ).data
        )

        by_status: dict[str, int] = {}
        by_type: dict[str, int] = {}
        durations: list[float] = []
        failed_examples: list[dict[str, Any]] = []

        for row in rows:
            status = str(row.get("status") or "unknown")
            by_status[status] = by_status.get(status, 0) + 1

            asset_type = str(row.get("asset_type") or "unknown")
            by_type[asset_type] = by_type.get(asset_type, 0) + 1

            metadata = row.get("generation_metadata") or {}
            if isinstance(metadata, dict):
                raw = metadata.get("generation_time_seconds")
                if isinstance(raw, int | float):
                    durations.append(float(raw))

            if status == "failed" and len(failed_examples) < 5:
                failed_examples.append(
                    {
                        "id": row.get("id"),
                        "error": row.get("error"),
                        "created_at": row.get("created_at"),
                    }
                )

        avg_duration = round(sum(durations) / len(durations), 2) if durations else None
        payload = {
            "feature": "content_bottleneck",
            "query": query,
            "metrics": {
                "total_assets": len(rows),
                "status_breakdown": by_status,
                "asset_type_breakdown": by_type,
                "avg_generation_time_seconds": avg_duration,
                "failed_examples": failed_examples,
            },
        }
        return _json(payload)

    def competitive_intelligence_tool(query: str) -> str:
        """Return competitor coverage and latest competitive alerts."""
        sb = get_supabase_admin()
        competitors = _as_rows(
            (
                sb.table("competitors")
                .select("id, name, website_url, pricing_url, last_scanned_at")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(100)
                .execute()
            ).data
        )
        alerts = _as_rows(
            (
                sb.table("competitive_alerts")
                .select("id, summary, severity, categories, created_at, competitor_id")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            ).data
        )

        severity_counts: dict[str, int] = {}
        for a in alerts:
            sev = str(a.get("severity") or "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        payload = {
            "feature": "competitive_intelligence",
            "query": query,
            "metrics": {
                "tracked_competitors": len(competitors),
                "recent_alerts": len(alerts),
                "alerts_by_severity": severity_counts,
                "latest_alerts": alerts[:10],
            },
        }
        return _json(payload)

    def launch_orchestration_tool(query: str) -> str:
        """Return launch orchestration status based on campaign pipeline state."""
        sb = get_supabase_admin()
        campaigns = _as_rows(
            (
                sb.table("campaigns")
                .select("id, brief, status, created_at, updated_at, error")
                .eq("org_id", org_id)
                .order("created_at", desc=True)
                .limit(120)
                .execute()
            ).data
        )

        status_counts: dict[str, int] = {}
        for c in campaigns:
            status = str(c.get("status") or "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        payload = {
            "feature": "launch_orchestration",
            "query": query,
            "metrics": {
                "campaign_count": len(campaigns),
                "status_breakdown": status_counts,
                "latest_campaigns": campaigns[:8],
            },
            "note": (
                "Use the dedicated campaigns flow for creation/execution operations; "
                "this tool focuses on orchestration intelligence and status visibility."
            ),
        }
        return _json(payload)

    def campaign_analysis_tool(query: str) -> str:
        """Return campaign/channel performance insights and comparisons."""
        metrics = build_summary_metrics(org_id)
        insights = _get_precomputed_insights(org_id, "campaign_analysis", limit=8)
        payload = {
            "feature": "campaign_analysis",
            "query": query,
            "metrics": metrics,
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    def sales_marketing_alignment_tool(query: str) -> str:
        """Return sales-marketing alignment metrics, friction signals, and insights."""
        summary = build_alignment_summary(org_id)
        friction = collect_friction_signals(org_id)
        insights = _get_precomputed_insights(org_id, "alignment", limit=8)
        payload = {
            "feature": "sales_marketing_alignment",
            "query": query,
            "alignment": summary,
            "friction": friction,
            "insights": [
                {
                    "key": i.get("key"),
                    "title": i.get("title"),
                    "answer": (i.get("content") or {}).get("answer"),
                    "citations": i.get("citations") or [],
                }
                for i in insights
            ],
        }
        return _json(payload)

    return [
        StructuredTool.from_function(icp_customer_research_tool),
        StructuredTool.from_function(content_bottleneck_tool),
        StructuredTool.from_function(competitive_intelligence_tool),
        StructuredTool.from_function(launch_orchestration_tool),
        StructuredTool.from_function(campaign_analysis_tool),
        StructuredTool.from_function(sales_marketing_alignment_tool),
    ]


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
        maybe_checkpoint_conversation(org_id, conversation_id)
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
        maybe_checkpoint_conversation(org_id, conversation_id)
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
        maybe_checkpoint_conversation(org_id, conversation_id)
        return result

    tools = _feature_tools(org_id)
    chat_history = _build_short_term_history(conversation_id)
    long_term_block = "\n".join(
        f"[{c.get('ref')}] {c.get('text', '')[:260]}" for c in long_term_context
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are Stoa's unified GTM Agent. You can call six tools: "
                    "ICP/customer research, content bottleneck, competitive intelligence, "
                    "launch orchestration, campaign analysis, and sales-marketing alignment. "
                    "Choose only the tools needed, combine outputs, and "
                    "produce actionable answers. "
                    "Prefer quantitative metrics and include evidence refs when available. "
                    "If data is insufficient, say so clearly and suggest the next best action."
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
            max_iterations=6,
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
        maybe_checkpoint_conversation(org_id, conversation_id)
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
        maybe_checkpoint_conversation(org_id, conversation_id)
        return result
