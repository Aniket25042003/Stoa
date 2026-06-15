"use client";

import { motion } from "framer-motion";
import { VideoBackground } from "@/components/marketing/immersive/VideoBackground";
import { WaitlistForm } from "@/components/marketing/immersive/WaitlistForm";

export default function WaitlistPage() {
  return (
    <div className="relative flex min-h-[calc(100vh-65px)] flex-col justify-center overflow-hidden px-4 py-12 md:px-6">
      <VideoBackground
        src="/videos/marketing/hero-loop.mp4"
        poster="/images/marketing/waitlist-backdrop.webp"
        posterMobile="/images/marketing/hero-orb-mobile.webp"
        overlayClassName="bg-gradient-to-b from-mkt-surface/70 via-mkt-surface/88 to-mkt-surface"
      />

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
