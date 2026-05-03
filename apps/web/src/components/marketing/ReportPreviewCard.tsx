"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/cn";

const excerpt = `# GTM Strategy — Acme

## Executive summary
- ICP: Seed-stage B2B founders replacing spreadsheets with AI workflows
- Wedge: onboarding in under 10 minutes with a guided template library
- Launch: founder communities + web crawl signals + targeted outbound to design partners

## Positioning
**For** technical founders **who** need repeatable GTM narrative **we** ship a living strategy doc **unlike** static consultants **because** agents refresh research every run.

…`;

export function ReportPreviewCard({ className }: { className?: string }) {
  const reduce = useReducedMotion();
  return (
    <motion.div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-mist/90 bg-cream/95 shadow-sm backdrop-blur-sm",
        className
      )}
      whileHover={reduce ? undefined : { y: -4, boxShadow: "var(--shadow-glow)" }}
      transition={{ type: "spring", stiffness: 260, damping: 22 }}
    >
      <div className="flex items-center gap-2 border-b border-mist px-4 py-3">
        <span className="h-2 w-2 rounded-full bg-mist" />
        <span className="h-2 w-2 rounded-full bg-mist" />
        <span className="h-2 w-2 rounded-full bg-mist" />
        <span className="ml-2 font-mono text-[10px] uppercase tracking-widest text-slate">report.md</span>
      </div>
      <pre className="max-h-[320px] overflow-hidden p-6 font-mono text-[11px] leading-relaxed text-ink/85 [mask-image:linear-gradient(to_bottom,black_70%,transparent)]">
        {excerpt}
      </pre>
    </motion.div>
  );
}
