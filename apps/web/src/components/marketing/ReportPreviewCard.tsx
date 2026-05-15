"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

const excerpt = `# Growth Plan - Acme

## Executive summary
- ICP: Seed-stage B2B founders replacing spreadsheets with AI workflows
- Wedge: onboarding in under 10 minutes with a guided template library
- Launch: founder communities + targeted outbound to design partners

## Positioning
For technical founders who need repeatable growth narrative, nexara keeps strategy and marketing execution in one living workspace.

## Marketing brief
- Hook: replace scattered spreadsheets with a repeatable operating rhythm
- Channel focus: founder communities, partner posts, and warm outbound
- Creative angle: launch faster without losing strategic clarity
`;

export function ReportPreviewCard({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={cn("relative overflow-hidden rounded-3xl card-glass", className)}
      whileHover={reduce ? undefined : { y: -6, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 24 }}
    >
      <div className="flex items-center justify-between gap-3 border-b border-outline-variant/50 px-5 py-4">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-error" />
          <span className="h-2.5 w-2.5 rounded-full bg-secondary-container" />
          <span className="h-2.5 w-2.5 rounded-full bg-primary-container" />
        </div>
        <span className="font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary">plan.md</span>
      </div>
      <pre className="max-h-[360px] overflow-hidden p-6 font-mono text-[12px] leading-7 text-on-surface/86 [mask-image:linear-gradient(to_bottom,black_72%,transparent)]">
        {excerpt}
      </pre>
    </motion.div>
  );
}
