/**
 * @file apps/web/src/components/marketing/AgentHierarchyDiagram.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

const layers = [
  { title: "Strategy engine", sub: "User-approved plan + synthesis" },
  { title: "Market intelligence", sub: "Competitor landscape + search scan" },
  { title: "Strategic analysis", sub: "Positioning angles + channel matches" },
  { title: "Content creation", sub: "Asset drafts + narrative campaigns" },
];

/**
 * Handles agent hierarchy diagram behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AgentHierarchyDiagram({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <div className={cn("relative overflow-hidden rounded-3xl p-6 card-glass md:p-8", className)}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_15%,rgb(255_107_53_/_0.16),transparent_34%)]" />
      <div className="relative flex items-center justify-between gap-4">
        <div className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary">
          Your approval
        </div>
      </div>
      <div className="relative mt-10 flex flex-col items-center gap-4">
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="w-full max-w-sm rounded-2xl border border-primary/35 bg-surface-container-low/80 px-5 py-4 text-center shadow-glow backdrop-blur-md"
        >
          <p className="font-display text-base font-bold text-on-surface">Your strategy</p>
          <p className="mt-1 text-xs text-on-surface-variant">Approved before campaign generation begins</p>
        </motion.div>
        <div className="h-7 w-px bg-gradient-to-b from-primary/55 to-outline-variant" />
        {layers.map((layer, idx) => (
          <div key={layer.title} className="flex w-full flex-col items-center gap-2">
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.08 * (idx + 1) }}
              className="w-full max-w-md rounded-2xl border border-outline-variant/70 bg-surface-container-low/70 px-5 py-4 backdrop-blur-md"
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-display text-sm font-bold text-on-surface">{layer.title}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{layer.sub}</p>
                </div>
              </div>
            </motion.div>
            {idx < layers.length - 1 ? <div className="h-5 w-px bg-outline-variant" /> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
