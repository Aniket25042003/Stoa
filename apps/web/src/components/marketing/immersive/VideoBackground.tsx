/**
 * @file apps/web/src/components/marketing/immersive/VideoBackground.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";
import { useDeferredMarketingMedia } from "@/hooks/useDeferredMarketingMedia";

interface VideoBackgroundProps {
  src: string;
  poster: string;
  posterMobile?: string;
  className?: string;
  overlayClassName?: string;
  /** Wait for LoadingGate before attaching video src (default: true). */
  deferUntilReady?: boolean;
}

/**
 * Handles resolve poster behavior for this part of the Stoa application.
 *
 * @param poster - Input value used to render UI or execute the workflow.
 * @param posterMobile - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function resolvePoster(poster: string, posterMobile?: string): string {
  if (!posterMobile) return poster;
  if (typeof window !== "undefined" && window.innerWidth < 768) {
    return posterMobile;
  }
  return poster;
}

/**
 * Handles video background behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function VideoBackground({
  src,
  poster,
  posterMobile,
  className,
  overlayClassName,
  deferUntilReady = true,
}: VideoBackgroundProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const mediaReady = useDeferredMarketingMedia();
  const [useFallback, setUseFallback] = useState(false);
  const [activePoster, setActivePoster] = useState(poster);
  const shouldLoadVideo = !deferUntilReady || mediaReady;

  useEffect(() => {
    const updatePoster = () => setActivePoster(resolvePoster(poster, posterMobile));
    updatePoster();
    window.addEventListener("resize", updatePoster, { passive: true });
    return () => window.removeEventListener("resize", updatePoster);
  }, [poster, posterMobile]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (mediaQuery.matches) {
      setUseFallback(true);
      return;
    }

    if (!shouldLoadVideo) return;

    const video = videoRef.current;
    if (!video) return;

    const playPromise = video.play();
    if (playPromise !== undefined) {
      playPromise.catch((err) => {
        console.warn("Autoplay prevented or failed, fallback to poster.", err);
        setUseFallback(true);
      });
    }
  }, [src, shouldLoadVideo]);

  return (
    <div className={cn("absolute inset-0 -z-10 overflow-hidden", className)}>
      {useFallback || !shouldLoadVideo ? (
        <img
          src={activePoster}
          alt=""
          className="h-full w-full object-cover"
          aria-hidden="true"
        />
      ) : (
        <video
          ref={videoRef}
          src={src}
          poster={activePoster}
          preload="none"
          autoPlay
          muted
          loop
          playsInline
          className="h-full w-full object-cover"
          aria-hidden="true"
        />
      )}
      <div className={cn("absolute inset-0 bg-transparent", overlayClassName)} aria-hidden="true" />
    </div>
  );
}
