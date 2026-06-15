"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { useDeferredMarketingMedia } from "@/hooks/useDeferredMarketingMedia";

interface Capability {
  id: string;
  word: string;
  title: string;
  description: string;
  videoSrc: string;
  posterSrc: string;
}

const CAPABILITIES: Capability[] = [
  {
    id: "strategy",
    word: "Strategy",
    title: "Read the room",
    description: "Customer and market signals, distilled for your team.",
    videoSrc: "/videos/marketing/capability-strategy-loop.mp4",
    posterSrc: "/images/marketing/capability-strategy.webp",
  },
  {
    id: "campaigns",
    word: "Campaigns",
    title: "Ship campaigns",
    description: "Strategy, briefs, and creative — connected end to end.",
    videoSrc: "/videos/marketing/capability-campaigns-loop.mp4",
    posterSrc: "/images/marketing/capability-campaigns.webp",
  },
  {
    id: "competitive",
    word: "Competitive Edge",
    title: "Stay ahead",
    description: "Competitive moves surfaced before they become noise.",
    videoSrc: "/videos/marketing/capability-competitive-loop.mp4",
    posterSrc: "/images/marketing/capability-competitive.webp",
  },
];

export function CapabilityPanel() {
  const [activeWordIdx, setActiveWordIdx] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveWordIdx((prev) => (prev + 1) % CAPABILITIES.length);
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-20 md:px-8">
      <div className="mb-16 flex flex-col items-center justify-center text-center">
        <div className="relative flex h-8 w-full justify-center overflow-hidden">
          <div className="flex items-center justify-center gap-2 text-xs uppercase tracking-[0.25em] text-mkt-muted md:gap-4">
            {CAPABILITIES.map((cap, idx) => (
              <span key={cap.id} className="flex items-center gap-2 md:gap-4">
                <span
                  className={cn(
                    "font-dm-sans transition-all duration-500",
                    idx === activeWordIdx ? "scale-105 font-bold text-mkt-accent" : "opacity-40"
                  )}
                >
                  {cap.word}
                </span>
                {idx < CAPABILITIES.length - 1 && <span className="opacity-20">·</span>}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-8 md:grid-cols-3">
        {CAPABILITIES.map((cap, i) => (
          <CapabilityCard key={cap.id} capability={cap} index={i} />
        ))}
      </div>
    </div>
  );
}

function CapabilityCard({ capability, index }: { capability: Capability; index: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaReady = useDeferredMarketingMedia();
  const [useFallback, setUseFallback] = useState(false);

  useEffect(() => {
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reducedMotion) {
      setUseFallback(true);
      return;
    }

    if (!mediaReady) return;

    const video = videoRef.current;
    if (!video) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          video.play().catch(() => setUseFallback(true));
        } else {
          video.pause();
        }
      },
      { threshold: 0.15 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [mediaReady]);

  return (
    <motion.div
      ref={containerRef}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-100px" }}
      transition={{ duration: 0.7, delay: index * 0.15, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -6, rotateX: 2, rotateY: -2 }}
      style={{ transformStyle: "preserve-3d", perspective: 1200 }}
      className="group relative flex flex-col overflow-hidden rounded-sm border border-mkt-ink/5 bg-mkt-surface/40 p-4 transition-all duration-300 hover:border-mkt-accent/25 hover:shadow-[0_20px_50px_-20px_rgba(79,70,229,0.12)]"
    >
      <div className="relative mb-6 aspect-[4/3] w-full overflow-hidden rounded-sm border border-mkt-ink/5 bg-mkt-surface">
        {useFallback || !mediaReady ? (
          <img
            src={capability.posterSrc}
            alt={capability.title}
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
        ) : (
          <video
            ref={videoRef}
            src={capability.videoSrc}
            poster={capability.posterSrc}
            preload="none"
            muted
            loop
            playsInline
            className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105"
          />
        )}
      </div>

      <div className="flex flex-1 flex-col px-1">
        <span className="mb-2 font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
          Chapter 0{index + 1}
        </span>
        <h3 className="font-syne mb-2.5 text-xl font-bold tracking-tight text-mkt-ink">
          {capability.title}
        </h3>
        <p className="font-dm-sans text-sm leading-relaxed text-mkt-muted">
          {capability.description}
        </p>
      </div>
    </motion.div>
  );
}
