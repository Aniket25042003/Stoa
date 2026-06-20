/**
 * @file apps/web/src/components/marketing/immersive/LoadingGate.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BrandLogo } from "@/components/product/BrandLogo";
import { notifyMarketingMediaReady } from "@/lib/marketing-media";

/**
 * Handles loading gate behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function LoadingGate() {
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const seen = sessionStorage.getItem("stoa_gate_seen");
    if (reducedMotion || seen) {
      setLoading(false);
      notifyMarketingMediaReady();
      return;
    }

    const duration = 1400; // 1.4 seconds
    const intervalTime = 20;
    const totalSteps = duration / intervalTime;
    const increment = 100 / totalSteps;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const next = prev + increment;
        if (next >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setLoading(false);
            sessionStorage.setItem("stoa_gate_seen", "true");
            notifyMarketingMediaReady();
          }, 300);
          return 100;
        }
        return next;
      });
    }, intervalTime);

    return () => clearInterval(interval);
  }, []);

  return (
    <AnimatePresence>
      {loading && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          className="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-[#F8F6F2]"
        >
          <div className="flex flex-col items-center max-w-xs w-full px-6">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="mb-6 flex items-center justify-center"
            >
              <BrandLogo variant="icon" size="lg" priority />
            </motion.div>

            <div className="w-full h-[2px] bg-[#14141A]/5 relative overflow-hidden rounded-full">
              <motion.div
                className="absolute left-0 top-0 bottom-0 bg-[#4F46E5]"
                style={{ width: `${progress}%` }}
              />
            </div>
            
            <span className="mt-2.5 font-mono text-[9px] tracking-widest text-[#6B6F7D] font-bold">
              {Math.min(100, Math.floor(progress))}%
            </span>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
