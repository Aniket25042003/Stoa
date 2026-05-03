"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ACTIVITY_MESSAGES } from "@/lib/activity-messages";
import { cn } from "@/lib/cn";

export function LiveActivityDemo({ className }: { className?: string }) {
  const messages = useMemo(() => Object.values(ACTIVITY_MESSAGES).flat(), []);
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setIndex((i) => (i + 1) % messages.length), 2200);
    return () => clearInterval(t);
  }, [messages.length]);

  const msg = messages[index % messages.length];

  return (
    <div
      className={cn(
        "grid gap-8 rounded-2xl border border-mist bg-cream/90 p-6 md:grid-cols-2 md:p-10",
        className
      )}
    >
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-slate">Live activity</p>
        <h3 className="mt-2 text-2xl font-semibold tracking-tight text-ink md:text-3xl">What founders see while agents work</h3>
        <p className="mt-3 text-sm leading-relaxed text-ink/75">
          The same rotating status copy you get on a real run — research, reasoning, and writing phases stay legible
          while the pipeline streams events.
        </p>
        <div className="mt-6 rounded-xl border border-mist bg-cream p-4 font-mono text-xs text-ink/80">
          <p className="text-slate">Product input</p>
          <p className="mt-2 leading-relaxed">
            &quot;AI-native CRM for seed teams…&quot; <span className="text-mist">(sample)</span>
          </p>
        </div>
      </div>
      <div className="flex flex-col justify-center">
        <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate">Current backend activity</p>
        <motion.div
          key={msg}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mt-3 rounded-2xl border border-slate/40 bg-ink px-5 py-4 text-cream shadow-glow"
        >
          <p className="text-base font-medium leading-snug">{msg}</p>
          <p className="mt-2 font-mono text-[11px] text-cream/60">Mirrors run detail UI</p>
        </motion.div>
      </div>
    </div>
  );
}
