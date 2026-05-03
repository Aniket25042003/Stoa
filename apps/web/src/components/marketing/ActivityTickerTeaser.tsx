"use client";

import { useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import { ACTIVITY_MESSAGES } from "@/lib/activity-messages";

export function ActivityTickerTeaser() {
  const messages = useMemo(() => Object.values(ACTIVITY_MESSAGES).flat(), []);
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((x) => (x + 1) % messages.length), 2200);
    return () => clearInterval(t);
  }, [messages.length]);
  const msg = messages[i % messages.length];

  return (
    <div className="rounded-xl border border-mist bg-cream/90 p-5">
      <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate">Sample backend activity</p>
      <motion.p
        key={msg}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mt-3 text-sm font-medium leading-snug text-ink"
      >
        {msg}
      </motion.p>
    </div>
  );
}
