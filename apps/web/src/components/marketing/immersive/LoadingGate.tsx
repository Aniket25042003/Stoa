"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { notifyMarketingMediaReady } from "@/lib/marketing-media";

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
              className="h-20 w-20 mb-6 flex items-center justify-center"
            >
              <img
                src="/images/marketing/loading-brand-mark.webp"
                alt="Stoa logo mark"
                className="h-full w-full object-contain"
              />
            </motion.div>
            
            <h2 className="font-syne text-sm font-bold tracking-[0.2em] text-[#14141A] mb-4 uppercase">
              STOA
            </h2>
            
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
