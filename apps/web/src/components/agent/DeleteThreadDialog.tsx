"use client";

import { ProductButton } from "@/components/product";
import type { ConversationSummary } from "@/components/agent/types";

type DeleteThreadDialogProps = {
  conversation: ConversationSummary | null;
  deleting: boolean;
  onCancel: () => void;
  onDeleteThreadOnly: () => void;
  onDeleteWithMemory: () => void;
};

export function DeleteThreadDialog({
  conversation,
  deleting,
  onCancel,
  onDeleteThreadOnly,
  onDeleteWithMemory,
}: DeleteThreadDialogProps) {
  if (!conversation) return null;

  const title = conversation.title || "Untitled";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-mkt-ink/30"
        onClick={deleting ? undefined : onCancel}
        aria-label="Close"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-thread-title"
        className="relative z-10 w-full max-w-md rounded-lg border border-mkt-ink/[0.08] bg-mkt-surface-elevated p-5 shadow-lg"
      >
        <h2 id="delete-thread-title" className="text-base font-semibold text-mkt-ink">
          Delete this thread?
        </h2>
        <p className="mt-2 text-sm text-mkt-muted">
          <span className="font-medium text-mkt-ink">&ldquo;{title}&rdquo;</span> will be removed from your
          thread list along with its messages.
        </p>
        <p className="mt-3 text-sm text-mkt-muted">
          STOA may have saved context from this thread for future answers. Choose whether to keep or remove that
          saved context.
        </p>

        <div className="mt-5 flex flex-col gap-2">
          <ProductButton
            variant="secondary"
            className="w-full justify-center border-mkt-ink/15 text-mkt-ink"
            disabled={deleting}
            onClick={onDeleteThreadOnly}
          >
            {deleting ? "Deleting…" : "Delete thread only"}
          </ProductButton>
          <ProductButton
            variant="primary"
            className="w-full justify-center !bg-red-600 hover:!bg-red-700"
            disabled={deleting}
            onClick={onDeleteWithMemory}
          >
            {deleting ? "Deleting…" : "Delete thread and memory"}
          </ProductButton>
          <ProductButton variant="ghost" className="w-full justify-center" disabled={deleting} onClick={onCancel}>
            Cancel
          </ProductButton>
        </div>
      </div>
    </div>
  );
}
