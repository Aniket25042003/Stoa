/**
 * @file apps/web/src/components/app-shell/StatusPill.tsx
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

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
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[11px] font-semibold uppercase tracking-[0.12em]",
        failed
          ? "border-error/25 bg-error-container text-error"
          : completed
            ? "border-primary/20 bg-primary/10 text-primary"
            : "border-outline-variant/60 bg-surface-container-low/80 text-on-surface"
      )}
    >
      {pulse ? (
        <motion.span
          className="inline-block h-2 w-2 rounded-full bg-primary shadow-[0_0_16px_rgb(73_75_214_/_0.75)]"
          animate={{ opacity: [1, 0.35, 1], scale: [1, 1.18, 1] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        />
      ) : (
        <span className={cn("inline-block h-2 w-2 rounded-full", failed ? "bg-error" : completed ? "bg-primary" : "bg-outline")} />
      )}
      {status}
    </span>
  );
}
