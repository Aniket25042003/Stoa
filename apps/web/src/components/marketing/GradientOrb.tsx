/**
 * @file apps/web/src/components/marketing/GradientOrb.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

/**
 * Handles gradient orb behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function GradientOrb({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      aria-hidden
      className={cn(
        "pointer-events-none absolute left-1/2 top-[-18%] h-[min(760px,92vw)] w-[min(760px,92vw)] -translate-x-1/2 rounded-full bg-[radial-gradient(circle_at_32%_30%,rgb(255_107_53_/_0.28),transparent_34%),radial-gradient(circle_at_66%_40%,rgb(196_162_101_/_0.22),transparent_36%),radial-gradient(circle_at_50%_55%,rgb(245_230_200_/_0.7),transparent_48%)] blur-3xl",
        className
      )}
      animate={
        reduce
          ? undefined
          : {
              x: ["-4%", "4%", "-2%", "0%"],
              y: ["0%", "5%", "-2%", "0%"],
              scale: [1, 1.04, 0.98, 1],
            }
      }
      transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}
