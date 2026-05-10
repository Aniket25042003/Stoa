"use client";

import { AnimatePresence, motion } from "framer-motion";
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
    <div className={cn("border-b border-outline-variant/50 last:border-b-0", open && "bg-primary/[0.06] dark:bg-white/[0.04]")}>
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-center justify-between gap-4 py-6 text-left font-display text-base font-bold tracking-[-0.01em] text-on-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
      >
        {question}
        <motion.span animate={{ rotate: open ? 45 : 0 }} className="font-mono text-xl text-primary">
          +
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
            className="overflow-hidden"
          >
            <p className="pb-6 pr-8 text-sm leading-7 text-on-surface-variant">{answer}</p>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
