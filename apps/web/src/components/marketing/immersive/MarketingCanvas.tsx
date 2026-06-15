"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { SignalFieldScene } from "./SignalFieldScene";
import { useMarketingWebGL } from "./useMarketingWebGL";
import { useDeferredMarketingMedia } from "@/hooks/useDeferredMarketingMedia";
import { cn } from "@/lib/cn";

type MarketingCanvasProps = {
  variant?: "hero" | "ambient";
  className?: string;
};

export function MarketingCanvas({ variant = "hero", className }: MarketingCanvasProps) {
  const { shouldRenderWebGL, dpr } = useMarketingWebGL();
  const mediaReady = useDeferredMarketingMedia();

  if (!shouldRenderWebGL || !mediaReady) return null;

  const isHero = variant === "hero";

  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 select-none",
        isHero && "z-[5] opacity-[0.72] mix-blend-multiply md:opacity-80",
        variant === "ambient" && "z-[1] opacity-50",
        className
      )}
      aria-hidden="true"
    >
      <Canvas
        dpr={Math.min(dpr, 1.25)}
        camera={{ position: [0, 0, 6.5], fov: 48 }}
        gl={{
          alpha: true,
          antialias: false,
          powerPreference: "high-performance",
          stencil: false,
          depth: true,
        }}
        style={{ background: "transparent" }}
        className="h-full w-full"
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.6} />
          <SignalFieldScene variant={variant} />
        </Suspense>
      </Canvas>
    </div>
  );
}
