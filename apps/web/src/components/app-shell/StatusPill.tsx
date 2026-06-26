/**
 * @file apps/web/src/components/app-shell/StatusPill.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { formatJobStatusLabel } from "@/lib/user-facing-copy";

const pulseStatuses = new Set(["planning", "running", "awaiting_plan_approval", "queued"]);

/**
 * Handles status pill behavior for this part of the Stoa application.
 *
 * @param status - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function StatusPill({ status }: { status: string }) {
  const pulse = pulseStatuses.has(status);
  const completed = status === "completed";
  const failed = status === "failed";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-wider",
        failed
          ? "border-red-200 bg-red-50 text-red-700"
          : completed
            ? "border-mkt-border bg-mkt-surface-elevated text-mkt-ink"
            : "border-mkt-border bg-mkt-surface text-mkt-muted"
      )}
    >
      {pulse ? (
        <motion.span
          className="inline-block h-2 w-2 rounded-full bg-mkt-accent"
          animate={{ opacity: [1, 0.35, 1], scale: [1, 1.18, 1] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        />
      ) : (
        <span
          className={cn(
            "inline-block h-2 w-2 rounded-full",
            failed ? "bg-red-600" : completed ? "bg-mkt-accent" : "bg-mkt-subtle"
          )}
        />
      )}
      {formatJobStatusLabel(status)}
    </span>
  );
}
