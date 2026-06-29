"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { X } from "lucide-react";
import { AgentChatCanvas } from "@/components/agent/AgentChatCanvas";
import { ContextRail } from "@/components/agent/ContextRail";
import { ConversationSidebar } from "@/components/agent/ConversationSidebar";
import { DeleteThreadDialog } from "@/components/agent/DeleteThreadDialog";
import type { AgentMessage, ConversationSummary } from "@/components/agent/types";
import { agentStatusFromEvent, isAgentKeepaliveEvent, isPinnedAgentStatus, nextAgentWaitingMessage } from "@/lib/agent-status";
import { STOA_WORKING_STATUS } from "@/lib/stoa-brand";
import { apiFetch } from "@/lib/api";
import { prepareInsightText } from "@/lib/intelligence-content";
import { consumeSse } from "@/lib/sse";
import { cn } from "@/lib/cn";

export function AgentWorkspace() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const urlConversationId = searchParams.get("c");

  const conversationIdRef = useRef<string | null>(urlConversationId);
  const askingRef = useRef(false);
  const waitingMessageIndexRef = useRef(0);

  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversationsLoading, setConversationsLoading] = useState(true);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(urlConversationId);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [usedTools, setUsedTools] = useState<string[]>([]);
  const [dashboard, setDashboard] = useState<Record<string, unknown> | null>(null);
  const [mobileHistoryOpen, setMobileHistoryOpen] = useState(false);
  const [mobileContextOpen, setMobileContextOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<ConversationSummary | null>(null);
  const [deletingThread, setDeletingThread] = useState(false);

  const refreshConversations = useCallback(async () => {
    const res = await apiFetch("/v1/conversations");
    if (res.ok) {
      const body = await res.json();
      setConversations(body.conversations ?? []);
    }
    setConversationsLoading(false);
  }, []);

  const loadConversation = useCallback(async (conversationId: string) => {
    const res = await apiFetch(`/v1/conversations/${conversationId}`);
    if (!res.ok) return;
    const body = await res.json();
    const loaded: AgentMessage[] = (body.messages ?? []).map(
      (m: { id: string; role: string; content: string; citations?: string[] }) => ({
        id: m.id,
        role: m.role === "user" || m.role === "assistant" ? m.role : "system",
        content: m.role === "assistant" ? prepareInsightText(m.content) : m.content,
        citations: m.citations,
      }),
    );
    setMessages(loaded);
  }, []);

  function syncConversationId(conversationId: string | null) {
    conversationIdRef.current = conversationId;
    setActiveConversationId(conversationId);
  }

  useEffect(() => {
    void refreshConversations();
    void (async () => {
      const res = await apiFetch("/v1/dashboard/summary");
      if (res.ok) setDashboard(await res.json());
    })();
  }, [refreshConversations]);

  useEffect(() => {
    const prompt = searchParams.get("q");
    if (prompt) setQuestion(prompt);
  }, [searchParams]);

  useEffect(() => {
    if (!urlConversationId) return;
    syncConversationId(urlConversationId);
    if (!askingRef.current) {
      void loadConversation(urlConversationId);
    }
  }, [urlConversationId, loadConversation]);

  const setConversationInUrl = useCallback(
    (conversationId: string | null) => {
      const params = new URLSearchParams(searchParams.toString());
      if (conversationId) params.set("c", conversationId);
      else params.delete("c");
      params.delete("q");
      const qs = params.toString();
      router.replace(qs ? `/agent?${qs}` : "/agent");
    },
    [router, searchParams],
  );

  function handleSelectConversation(id: string | null) {
    syncConversationId(id);
    setConversationInUrl(id);
    setMobileHistoryOpen(false);
    if (id) void loadConversation(id);
    else {
      setMessages([]);
      setQuestion("");
      setStatus(null);
      setUsedTools([]);
    }
  }

  function handleNewChat() {
    handleSelectConversation(null);
  }

  async function handleDeleteThread(deleteMemory: boolean) {
    if (!threadToDelete || deletingThread) return;
    setDeletingThread(true);
    const deletedId = threadToDelete.id;
    const params = deleteMemory ? "?delete_memory=true" : "";
    const res = await apiFetch(`/v1/conversations/${deletedId}${params}`, { method: "DELETE" });
    setDeletingThread(false);
    if (!res.ok) {
      setStatus("Could not delete thread. Please try again.");
      return;
    }
    setThreadToDelete(null);
    if (conversationIdRef.current === deletedId) {
      handleSelectConversation(null);
    }
    await refreshConversations();
  }

  const ask = useCallback(
    async (prompt?: string) => {
      const q = (prompt ?? question).trim();
      if (!q || askingRef.current) return;

      askingRef.current = true;
      setAsking(true);
      setStatus(STOA_WORKING_STATUS);
      waitingMessageIndexRef.current = 0;
      setUsedTools([]);
      setQuestion("");

      const userMsg: AgentMessage = {
        id: `local-user-${Date.now()}`,
        role: "user",
        content: q,
      };
      setMessages((prev) => [...prev, userMsg]);

      const existingId = conversationIdRef.current;
      const res = await apiFetch("/v1/conversations/ask", {
        method: "POST",
        body: JSON.stringify(
          existingId ? { question: q, conversation_id: existingId } : { question: q },
        ),
      });

      if (!res.ok) {
        setStatus("Request failed. Please try again.");
        setAsking(false);
        askingRef.current = false;
        return;
      }

      const body = await res.json();
      const convId = body.conversation_id as string;
      syncConversationId(convId);
      setConversationInUrl(convId);

      const ctrl = new AbortController();
      try {
        await consumeSse(
          `/v1/conversations/${convId}/events`,
          (event) => {
            if (isAgentKeepaliveEvent(event)) {
              setStatus((prev) =>
                isPinnedAgentStatus(prev)
                  ? prev
                  : nextAgentWaitingMessage(waitingMessageIndexRef),
              );
              return;
            }
            const statusMessage = agentStatusFromEvent(event);
            if (statusMessage) {
              setStatus(statusMessage);
            }
            if (event.status === "tool_summary" && Array.isArray(event.used_tools)) {
              setUsedTools(event.used_tools as string[]);
            }
            if (event.status === "tool_call" && typeof event.tool === "string") {
              setUsedTools((prev) =>
                prev.includes(event.tool as string) ? prev : [...prev, event.tool as string],
              );
            }
            if (event.status === "completed" && typeof event.answer === "string") {
              const assistantMsg: AgentMessage = {
                id: `local-assistant-${Date.now()}`,
                role: "assistant",
                content: prepareInsightText(event.answer),
                citations: Array.isArray(event.citations) ? (event.citations as string[]) : undefined,
                reveal: true,
              };
              setMessages((prev) => [...prev, assistantMsg]);
              setStatus(null);
              setAsking(false);
              askingRef.current = false;
              void refreshConversations();
              ctrl.abort();
            }
            if (event.status === "failed") {
              setStatus("STOA couldn't finish. Please retry.");
              setAsking(false);
              askingRef.current = false;
              ctrl.abort();
            }
          },
          ctrl.signal,
        );
      } catch {
        if (ctrl.signal.aborted) return;
        setAsking(false);
        askingRef.current = false;
        setStatus((prev) => prev ?? "Stream closed. Select the thread to reload messages.");
      }
    },
    [question, refreshConversations, setConversationInUrl],
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden flex-col lg:flex-row">
      <ConversationSidebar
        conversations={conversations}
        activeId={activeConversationId}
        loading={conversationsLoading}
        onSelect={handleSelectConversation}
        onNewChat={handleNewChat}
        onDeleteRequest={setThreadToDelete}
        className={cn("h-full lg:flex", mobileHistoryOpen ? "flex" : "hidden")}
      />

      <AgentChatCanvas
        messages={messages}
        question={question}
        onQuestionChange={setQuestion}
        onSubmit={() => void ask()}
        asking={asking}
        status={status}
        usedTools={usedTools}
        onOpenHistory={() => setMobileHistoryOpen(true)}
        showHistoryToggle
      />

      <ContextRail summary={dashboard as Parameters<typeof ContextRail>[0]["summary"]} />

      <button
        type="button"
        onClick={() => setMobileContextOpen(true)}
        className="fixed bottom-20 right-4 z-30 rounded-sm border border-mkt-ink/[0.08] bg-mkt-surface-elevated px-3 py-2 text-xs font-medium text-mkt-muted shadow-sm lg:hidden"
      >
        Context
      </button>

      {mobileHistoryOpen ? (
        <button
          type="button"
          className="fixed inset-0 z-20 bg-mkt-ink/20 lg:hidden"
          onClick={() => setMobileHistoryOpen(false)}
          aria-label="Close threads"
        />
      ) : null}

      {mobileContextOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-mkt-ink/20"
            onClick={() => setMobileContextOpen(false)}
            aria-label="Close context"
          />
          <div className="absolute inset-x-0 bottom-0 max-h-[75vh] overflow-hidden rounded-t-lg border border-mkt-ink/[0.06] bg-mkt-surface shadow-lg">
            <div className="flex items-center justify-between border-b border-mkt-ink/[0.06] px-4 py-3">
              <p className="text-sm font-medium text-mkt-ink">Context</p>
              <button type="button" onClick={() => setMobileContextOpen(false)} aria-label="Close">
                <X className="h-5 w-5 text-mkt-muted" />
              </button>
            </div>
            <ContextRail
              summary={dashboard as Parameters<typeof ContextRail>[0]["summary"]}
              overlay
              className="max-h-[calc(75vh-3rem)]"
            />
          </div>
        </div>
      ) : null}

      <DeleteThreadDialog
        conversation={threadToDelete}
        deleting={deletingThread}
        onCancel={() => setThreadToDelete(null)}
        onDeleteThreadOnly={() => void handleDeleteThread(false)}
        onDeleteWithMemory={() => void handleDeleteThread(true)}
      />
    </div>
  );
}
