"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

const pulseStatuses = new Set(["running", "awaiting_plan_approval", "queued"]);

export function StatusPill({ status }: { status: string }) {
  const pulse = pulseStatuses.has(status);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full border border-mist bg-cream px-3 py-1 font-mono text-[11px] uppercase tracking-wider text-ink"
      )}
    >
      {pulse ? (
        <motion.span
          className="inline-block h-2 w-2 rounded-full bg-slate"
          animate={{ opacity: [1, 0.35, 1], scale: [1, 1.15, 1] }}
          transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
        />
      ) : (
        <span className="inline-block h-2 w-2 rounded-full bg-mist" />
      )}
      {status}
    </span>
  );
}
