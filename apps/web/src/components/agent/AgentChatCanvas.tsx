"use client";

import { useEffect, useRef } from "react";
import { History, Send } from "lucide-react";
import { ProductBadge, ProductButton, ProductTextarea } from "@/components/product";
import type { AgentMessage } from "@/components/agent/types";
import { cn } from "@/lib/cn";

type AgentChatCanvasProps = {
  messages: AgentMessage[];
  question: string;
  onQuestionChange: (value: string) => void;
  onSubmit: () => void;
  asking: boolean;
  status: string | null;
  usedTools: string[];
  onOpenHistory?: () => void;
  showHistoryToggle?: boolean;
};

export function AgentChatCanvas({
  messages,
  question,
  onQuestionChange,
  onSubmit,
  asking,
  status,
  usedTools,
  onOpenHistory,
  showHistoryToggle,
}: AgentChatCanvasProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status, asking]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!asking && question.trim()) onSubmit();
    }
  }

  const isEmpty = messages.length === 0 && !asking && !status;

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-1 flex-col">
      {showHistoryToggle ? (
        <div className="flex shrink-0 items-center border-b border-mkt-ink/[0.06] px-4 py-2 lg:hidden">
          <button
            type="button"
            onClick={onOpenHistory}
            className="inline-flex items-center gap-2 text-sm font-medium text-mkt-muted"
          >
            <History className="h-4 w-4" />
            Threads
          </button>
        </div>
      ) : null}

      <div className="mkt-scrollbar-none min-h-0 flex-1 overflow-y-auto px-4 py-4 md:px-6">
        {isEmpty ? (
          <div className="mx-auto flex max-w-2xl flex-col items-center justify-center py-8 text-center">
            <h2 className="font-syne text-xl font-semibold uppercase tracking-tight text-mkt-ink md:text-2xl">
              What do you want to know about your GTM?
            </h2>
            <p className="mt-2 max-w-md text-sm text-mkt-muted">
              Ask follow-up questions in the same thread. Start a new thread only when you use New chat.
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-3xl space-y-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn(
                  "px-4 py-3 text-sm leading-relaxed",
                  msg.role === "user" ? "agent-message-user ml-8" : "agent-message-assistant mr-8",
                )}
              >
                <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-mkt-subtle">
                  {msg.role === "user" ? "You" : "Agent"}
                </p>
                <p className="whitespace-pre-wrap text-mkt-ink">{msg.content}</p>
                {msg.citations?.length ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {msg.citations.map((c) => (
                      <ProductBadge key={c} variant="accent">
                        {c}
                      </ProductBadge>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}

            {asking || status ? (
              <div className="agent-message-assistant mr-8 px-4 py-3 text-sm text-mkt-muted">
                <p className="mb-1 text-[10px] font-medium uppercase tracking-wider text-mkt-subtle">
                  Agent
                </p>
                <p>{status ?? "Thinking…"}</p>
                {usedTools.length > 0 ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {usedTools.map((tool) => (
                      <ProductBadge key={tool} variant="accent">
                        {tool}
                      </ProductBadge>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <div className="shrink-0 border-t border-mkt-ink/[0.06] bg-mkt-surface-elevated px-4 py-3 md:px-6">
        <div className="mx-auto flex max-w-3xl gap-2">
          <ProductTextarea
            value={question}
            onChange={(e) => onQuestionChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a follow-up in this thread…"
            rows={2}
            className="min-h-[48px] flex-1 resize-none"
            disabled={asking}
          />
          <ProductButton
            onClick={onSubmit}
            disabled={asking || !question.trim()}
            className="self-end"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </ProductButton>
        </div>
      </div>
    </div>
  );
}
