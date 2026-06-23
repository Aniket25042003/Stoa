"use client";

import { motion } from "framer-motion";
import { WaitlistForm } from "@/components/marketing/v3/WaitlistForm";

export default function WaitlistPage() {
  return (
    <div className="relative flex min-h-[calc(100vh-5rem)] flex-col justify-center overflow-hidden bg-mkt-surface px-4 py-12 md:px-6 mkt-section-pad">
      <div className="pointer-events-none absolute inset-0 mkt-dot-grid opacity-40" aria-hidden />

      <main className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 items-center justify-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          className="flex w-full justify-center"
        >
          <WaitlistForm />
        </motion.div>
      </main>
    </div>
  );
}
