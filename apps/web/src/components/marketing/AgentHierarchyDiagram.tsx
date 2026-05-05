"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

const layers = [
  { title: "Main agent", sub: "User-approved plan + supervision", progress: "100%" },
  { title: "Research", sub: "Web, crawler, competitor evidence", progress: "82%" },
  { title: "Reasoning", sub: "ICP, positioning, channel fit", progress: "64%" },
  { title: "Writing", sub: "GTM narrative + PDF export", progress: "48%" },
];

export function AgentHierarchyDiagram({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <div className={cn("relative overflow-hidden rounded-3xl p-6 card-glass md:p-8", className)}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_15%,rgb(99_102_241_/_0.16),transparent_34%)]" />
      <div className="relative flex items-center justify-between gap-4">
        <div className="rounded-full border border-primary/25 bg-primary/10 px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.14em] text-primary">
          User gate
        </div>
        <div className="h-1 w-24 overflow-hidden rounded-full bg-surface-container-high">
          <div className="h-full w-4/5 animate-shimmer rounded-full progress-shimmer" />
        </div>
      </div>
      <div className="relative mt-10 flex flex-col items-center gap-4">
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="w-full max-w-sm rounded-2xl border border-primary/35 bg-white/80 px-5 py-4 text-center shadow-glow backdrop-blur-md"
        >
          <p className="font-display text-base font-bold text-slate-deep">Master plan</p>
          <p className="mt-1 text-xs text-on-surface-variant">Approved before any sub-agent runs</p>
        </motion.div>
        <div className="h-7 w-px bg-gradient-to-b from-primary/55 to-outline-variant" />
        {layers.map((layer, idx) => (
          <div key={layer.title} className="flex w-full flex-col items-center gap-2">
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.08 * (idx + 1) }}
              className="w-full max-w-md rounded-2xl border border-white/70 bg-white/62 px-5 py-4 backdrop-blur-md"
            >
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-display text-sm font-bold text-slate-deep">{layer.title}</p>
                  <p className="mt-1 text-xs text-on-surface-variant">{layer.sub}</p>
                </div>
                <span className="font-mono text-xs font-semibold text-primary">{layer.progress}</span>
              </div>
              <div className="mt-3 h-1 overflow-hidden rounded-full bg-surface-container-high">
                <div className="h-full animate-shimmer rounded-full progress-shimmer" style={{ width: layer.progress }} />
              </div>
            </motion.div>
            {idx < layers.length - 1 ? <div className="h-5 w-px bg-outline-variant" /> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
