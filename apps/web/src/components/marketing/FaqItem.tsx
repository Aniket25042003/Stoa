/**
 * @file apps/web/src/components/marketing/FaqItem.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/cn";

export function FaqItem({
  question,
  answer,
  open,
  onToggle,
}: {
  question: string;
  answer: string;
  open: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border-b border-mkt-ink/[0.06] last:border-b-0">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className={cn(
          "flex w-full items-center justify-between gap-4 py-5 text-left sm:py-6",
          "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mkt-accent"
        )}
      >
        <span className="min-w-0 pr-2 text-base font-medium text-mkt-ink sm:text-lg">
          {question}
        </span>
        <motion.span
          animate={{ rotate: open ? 45 : 0 }}
          transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="shrink-0 text-xl font-light text-mkt-muted"
        >
          +
        </motion.span>
      </button>
      {open ? (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          className="overflow-hidden"
        >
          <p className="pb-5 pr-2 text-sm leading-7 text-mkt-muted sm:pb-6 sm:pr-8">
            {answer}
          </p>
        </motion.div>
      ) : null}
    </div>
  );
}
