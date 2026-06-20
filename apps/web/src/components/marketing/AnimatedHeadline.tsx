/**
 * @file apps/web/src/components/marketing/AnimatedHeadline.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

/**
 * Handles animated headline behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AnimatedHeadline({ text, className }: { text: string; className?: string }) {
  const reduce = useReducedMotion();
  const words = text.split(" ");
  if (reduce) {
    return <h1 className={className}>{text}</h1>;
  }
  return (
    <h1 className={cn("flex flex-wrap gap-x-3 gap-y-1", className)}>
      {words.map((w, i) => (
        <motion.span
          key={`${w}-${i}`}
          className="inline-block"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 120, damping: 18, delay: i * 0.06 }}
        >
          {w}
        </motion.span>
      ))}
    </h1>
  );
}
