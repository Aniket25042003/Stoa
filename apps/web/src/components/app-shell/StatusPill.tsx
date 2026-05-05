"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

const pulseStatuses = new Set(["running", "awaiting_plan_approval", "queued"]);

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
            : "border-outline-variant/60 bg-white/72 text-slate-deep"
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
