"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

const layers = [
  { title: "Main agent", sub: "User-approved plan + supervision" },
  { title: "Research", sub: "Reddit · X · Web · Competitors" },
  { title: "Reasoning", sub: "ICP · Positioning · Channels" },
  { title: "Writing", sub: "GTM doc + PDF" },
];

export function AgentHierarchyDiagram({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <div className={cn("relative rounded-2xl border border-mist bg-cream/90 p-6 md:p-8", className)}>
      <div className="absolute left-6 top-6 rounded-full border border-slate bg-cream px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-slate">
        User gate
      </div>
      <div className="mt-10 flex flex-col items-center gap-4">
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="w-full max-w-sm rounded-xl border-2 border-slate bg-cream px-4 py-3 text-center shadow-glow"
        >
          <p className="text-sm font-semibold text-ink">Master plan</p>
          <p className="text-xs text-ink/65">Approved before any sub-agent runs</p>
        </motion.div>
        <div className="h-6 w-px bg-mist" />
        {layers.map((layer, idx) => (
          <div key={layer.title} className="flex w-full flex-col items-center gap-2">
            <motion.div
              initial={reduce ? false : { opacity: 0, y: 16 }}
              whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.08 * (idx + 1) }}
              className="w-full max-w-md rounded-xl border border-mist bg-cream px-4 py-3 text-center"
            >
              <p className="text-sm font-semibold text-ink">{layer.title}</p>
              <p className="text-xs text-slate">{layer.sub}</p>
            </motion.div>
            {idx < layers.length - 1 ? <div className="h-5 w-px bg-mist" /> : null}
          </div>
        ))}
      </div>
    </div>
  );
}
