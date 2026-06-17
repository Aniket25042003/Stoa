"use client";

import { cn } from "@/lib/cn";

export type DataHubToastVariant = "success" | "error";

export function DataHubToast({
  message,
  variant = "success",
}: {
  message: string | null;
  variant?: DataHubToastVariant;
}) {
  if (!message) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "mb-6 flex items-start gap-3 rounded-sm border px-4 py-3 shadow-[0_4px_20px_rgba(20,20,26,0.06)]",
        variant === "error"
          ? "border-mkt-accent-warm/30 bg-mkt-accent-warm/[0.08]"
          : "border-mkt-accent/25 bg-mkt-surface"
      )}
    >
      <span
        aria-hidden
        className={cn(
          "mt-1.5 h-2 w-2 shrink-0 rounded-full",
          variant === "error" ? "bg-mkt-accent-warm" : "bg-mkt-accent"
        )}
      />
      <p className="font-dm-sans text-sm leading-relaxed text-mkt-ink">{message}</p>
    </div>
  );
}
