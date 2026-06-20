/**
 * @file apps/web/src/components/motion/CollapsibleDevLog.tsx
 * @layer Application Source
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ChevronDown } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/cn";

const codePanel =
  "rounded-2xl border border-outline-variant/55 bg-slate-deep p-4 font-mono text-xs leading-6 text-white/78";

/**
 * Handles collapsible dev log behavior for this part of the Stoa application.
 *
 * @param title - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function CollapsibleDevLog({
  title = "Technical log",
  lines,
  className,
}: {
  title?: string;
  lines: string[];
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const reduce = useReducedMotion();

  if (lines.length === 0) return null;

  return (
    <section className={cn("rounded-3xl p-5 card-glass md:p-6", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-3 text-left"
        aria-expanded={open}
      >
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-variant">
          {title}
        </span>
        <ChevronDown
          className={cn("h-4 w-4 shrink-0 text-on-surface-variant transition-transform", open && "rotate-180")}
        />
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            initial={reduce ? false : { height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={reduce ? undefined : { height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <pre className={cn("mt-4 max-h-[280px] overflow-auto whitespace-pre-wrap", codePanel)}>
              {lines.join("\n")}
            </pre>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </section>
  );
}
