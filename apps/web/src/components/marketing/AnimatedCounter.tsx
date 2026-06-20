/**
 * @file apps/web/src/components/marketing/AnimatedCounter.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "framer-motion";

/**
 * Handles animated counter behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function AnimatedCounter({
  value,
  duration = 1.5,
  suffix = "",
}: {
  value: number;
  duration?: number;
  suffix?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!isInView) return;
    
    const end = value;
    if (end === 0) return;
    
    const totalTicks = Math.max(Math.floor((duration * 1000) / 16), 10); // ~60fps
    const increment = end / totalTicks;
    let tick = 0;

    const timer = setInterval(() => {
      tick++;
      if (tick >= totalTicks) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(increment * tick));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value, duration, isInView]);

  return (
    <span ref={ref} className="tabular-nums">
      {count}
      {suffix}
    </span>
  );
}
