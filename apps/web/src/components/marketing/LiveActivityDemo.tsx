"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { ActivitySurface } from "@/components/motion/ActivitySurface";
import { PipelinePhaseVisualizer } from "@/components/motion/PipelinePhaseVisualizer";
import { ACTIVITY_MESSAGES, PHASE_LABELS, type ActivityPhase } from "@/lib/activity-messages";
import { BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

const DEMO_PHASES: ActivityPhase[] = ["planning", "research", "reasoning", "writing"];

const friendlyPhases = ["Profile", "Plan", "Brand", "Campaign"];

export function LiveActivityDemo({ className }: { className?: string }) {
  const [phaseIdx, setPhaseIdx] = useState(0);
  const [msgIdx, setMsgIdx] = useState(0);
  const phase = DEMO_PHASES[phaseIdx % DEMO_PHASES.length];
  const messages = ACTIVITY_MESSAGES[phase];
  const msg = messages[msgIdx % messages.length];
  const phaseLabel = PHASE_LABELS[phase];

  useEffect(() => {
    const t = setInterval(() => {
      setPhaseIdx((i) => (i + 1) % DEMO_PHASES.length);
      setMsgIdx(0);
    }, 4000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    const t = setInterval(() => setMsgIdx((i) => i + 1), 2200);
    return () => clearInterval(t);
  }, [phase]);

  const activeBar = phaseIdx % friendlyPhases.length;

  return (
    <div className={cn("relative overflow-hidden rounded-3xl p-6 card-glass md:p-10", className)}>
      <div className="absolute right-0 top-0 h-64 w-64 translate-x-1/3 -translate-y-1/3 rounded-full bg-violet-pulse/18 blur-3xl" />
      <div className="relative grid gap-10 md:grid-cols-[0.9fr_1.1fr] md:items-center">
        <div>
          <p className="eyebrow">Live activity</p>
          <h3 className="mt-3 font-display text-3xl font-bold leading-tight tracking-[-0.03em] text-on-surface md:text-4xl">
            {BRAND_TAGLINE}
          </h3>
          <p className="mt-4 text-sm leading-7 text-on-surface-variant">
            Follow company setup, plan updates, brand decisions, and campaign work in one shelter—without losing context.
          </p>
          <div className="mt-7 grid grid-cols-4 gap-2">
            {friendlyPhases.map((label, i) => (
              <div key={label} className="rounded-xl border border-outline-variant/50 bg-surface-container-low/70 p-3 backdrop-blur-md">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-on-surface-variant">{label}</p>
                <div className="mt-3 h-1 rounded-full bg-surface-container-high">
                  <motion.div
                    className={cn("h-full rounded-full", i <= activeBar ? "progress-shimmer" : "bg-outline-variant")}
                    animate={i <= activeBar ? { width: "100%" } : { width: "12%" }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="relative rounded-3xl bg-slate-deep p-5 text-white shadow-card">
          <div className="absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-inverse-primary to-transparent" />
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Current workspace activity</p>
          <div className="mt-4">
            <PipelinePhaseVisualizer phase={phase} />
          </div>
          <div className="mt-4">
            <ActivitySurface phase={phase} compact />
          </div>
          <motion.div
            key={`${phase}-${msg}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="mt-4 rounded-2xl border border-white/10 bg-white/6 px-5 py-4 backdrop-blur-md"
          >
            <p className="text-base font-semibold leading-snug">{msg}</p>
            <p className="mt-3 font-mono text-[11px] text-white/48">{phaseLabel}</p>
          </motion.div>
          <div className="mt-5 rounded-2xl border border-white/10 bg-white/4 p-4 font-mono text-xs text-white/70">
            <p className="text-inverse-primary">Product input</p>
            <p className="mt-2 leading-relaxed">&quot;AI-native CRM for seed teams...&quot;</p>
          </div>
        </div>
      </div>
    </div>
  );
}
