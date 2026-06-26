"use client";

import { Plus, Trash2 } from "lucide-react";
import { ProductButton } from "@/components/product";
import type { ConversationSummary } from "@/components/agent/types";
import { cn } from "@/lib/cn";

type ConversationSidebarProps = {
  conversations: ConversationSummary[];
  activeId: string | null;
  loading: boolean;
  onSelect: (id: string | null) => void;
  onNewChat: () => void;
  onDeleteRequest?: (conversation: ConversationSummary) => void;
  className?: string;
};

export function ConversationSidebar({
  conversations,
  activeId,
  loading,
  onSelect,
  onNewChat,
  onDeleteRequest,
  className,
}: ConversationSidebarProps) {
  return (
    <aside
      className={cn(
        "flex h-full w-full shrink-0 flex-col border-b border-mkt-ink/[0.06] bg-mkt-surface-elevated lg:w-[var(--agent-sidebar-width)] lg:border-b-0 lg:border-r",
        className,
      )}
    >
      <div className="flex items-center justify-between gap-2 border-b border-mkt-ink/[0.06] px-4 py-3">
        <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">Threads</p>
        <ProductButton variant="secondary" className="!px-2 !py-1.5 text-xs" onClick={onNewChat}>
          <Plus className="h-3.5 w-3.5" />
          New
        </ProductButton>
      </div>

      <div className="mkt-scrollbar-none flex-1 overflow-y-auto p-2">
        {loading ? (
          <p className="px-2 py-3 text-xs text-mkt-muted">Loading threads…</p>
        ) : conversations.length === 0 ? (
          <p className="px-2 py-3 text-xs text-mkt-muted">No conversations yet. Ask your first question.</p>
        ) : (
          <ul className="space-y-0.5">
            {conversations.map((conv) => {
              const active = conv.id === activeId;
              return (
                <li key={conv.id} className="group relative">
                  <button
                    type="button"
                    onClick={() => onSelect(conv.id)}
                    className={cn(
                      "w-full rounded-sm py-2.5 pl-3 pr-9 text-left text-sm transition-colors",
                      active
                        ? "bg-mkt-accent/[0.08] font-medium text-mkt-accent"
                        : "text-mkt-muted hover:bg-mkt-ink/[0.03] hover:text-mkt-ink",
                    )}
                  >
                    <span className="line-clamp-2">{conv.title || "Untitled"}</span>
                  </button>
                  {onDeleteRequest ? (
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onDeleteRequest(conv);
                      }}
                      className={cn(
                        "absolute right-1 top-1/2 -translate-y-1/2 rounded-sm p-1.5 text-mkt-subtle transition-colors",
                        "opacity-0 group-hover:opacity-100 focus:opacity-100",
                        "hover:bg-red-50 hover:text-red-600",
                        active && "hover:bg-red-100",
                      )}
                      aria-label={`Delete thread ${conv.title || "Untitled"}`}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  ) : null}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </aside>
  );
}
