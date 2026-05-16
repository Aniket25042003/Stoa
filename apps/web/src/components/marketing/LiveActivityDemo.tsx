"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ACTIVITY_MESSAGES } from "@/lib/activity-messages";
import { BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

const phases = ["Profile", "Plan", "Brand", "Campaign"];

export function LiveActivityDemo({ className }: { className?: string }) {
  const messages = useMemo(() => Object.values(ACTIVITY_MESSAGES).flat(), []);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setIndex((i) => (i + 1) % messages.length), 2200);
    return () => clearInterval(t);
  }, [messages.length]);

  const msg = messages[index % messages.length];

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
            {phases.map((phase, i) => (
              <div key={phase} className="rounded-xl border border-outline-variant/50 bg-surface-container-low/70 p-3 backdrop-blur-md">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.12em] text-on-surface-variant">{phase}</p>
                <div className="mt-3 h-1 rounded-full bg-surface-container-high">
                  <div className={cn("h-full rounded-full", i <= index % phases.length ? "progress-shimmer animate-shimmer" : "bg-outline-variant")} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="relative rounded-3xl bg-slate-deep p-5 text-white shadow-card">
          <div className="absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-inverse-primary to-transparent" />
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.16em] text-inverse-primary">Current workspace activity</p>
          <motion.div
            key={msg}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35 }}
            className="mt-4 rounded-2xl border border-white/10 bg-white/6 px-5 py-4 backdrop-blur-md"
          >
            <p className="text-base font-semibold leading-snug">{msg}</p>
            <p className="mt-3 font-mono text-[11px] text-white/48">Company workspace update</p>
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
