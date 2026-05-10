"use client";

import { useEffect, useMemo, useState } from "react";
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
    <div className="ai-insight-card rounded-2xl border border-outline-variant/70 p-5 shadow-soft">
      <div className="flex items-center justify-between gap-4">
        <p className="eyebrow text-[10px]">Sample backend activity</p>
        <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_20px_rgb(73_75_214_/_0.8)]" />
      </div>
      <motion.p
        key={msg}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="mt-3 text-sm font-semibold leading-snug text-on-surface"
      >
        {msg}
      </motion.p>
    </div>
  );
}
