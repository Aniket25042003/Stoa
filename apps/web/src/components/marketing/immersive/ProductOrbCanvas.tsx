"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import { ProductOrbScene } from "./ProductOrbScene";
import { useMarketingWebGL } from "./useMarketingWebGL";
import { useDeferredMarketingMedia } from "@/hooks/useDeferredMarketingMedia";
import { CORE_FALLBACK_POSTER, ORB_FACE_IMAGES } from "@/lib/landingFeatures";
import { cn } from "@/lib/cn";

type ProductOrbCanvasProps = {
  scrollProgress: number;
  activeSection: number;
  className?: string;
};

export function ProductOrbCanvas({
  scrollProgress,
  activeSection,
  className,
}: ProductOrbCanvasProps) {
  const { shouldRenderWebGL, dpr } = useMarketingWebGL();
  const mediaReady = useDeferredMarketingMedia();

  const showCanvas = shouldRenderWebGL && mediaReady;
  const fallbackSrc = ORB_FACE_IMAGES[activeSection] ?? CORE_FALLBACK_POSTER;

  return (
    <div className={cn("relative h-full w-full select-none", className)} aria-hidden="true">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(79,70,229,0.08)_0%,rgba(242,240,235,0.35)_42%,transparent_72%)]" />

      {!showCanvas && (
        <img
          src={fallbackSrc}
          alt=""
          className="absolute inset-0 m-auto h-[min(340px,72%)] w-auto max-w-[min(340px,72%)] rounded-2xl object-cover opacity-100 shadow-[0_24px_80px_rgba(79,70,229,0.14)] brightness-[1.04] contrast-[0.98]"
        />
      )}

      {showCanvas && (
        <Canvas
          dpr={Math.min(dpr, 2)}
          camera={{ position: [0, 0.08, 5.4], fov: 32 }}
          shadows
          gl={{
            alpha: true,
            antialias: true,
            powerPreference: "high-performance",
            stencil: false,
          }}
          style={{ background: "transparent" }}
          className="h-full w-full"
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.72} color="#f8f6f2" />
            <hemisphereLight intensity={0.5} color="#ffffff" groundColor="#ebe7df" />
            <directionalLight
              position={[4, 6, 5]}
              intensity={1.65}
              castShadow
              shadow-mapSize={[1024, 1024]}
              color="#fffef8"
            />
            <directionalLight position={[-4, 3, -2]} intensity={0.55} color="#eef0ff" />
            <directionalLight position={[0, -2, 4]} intensity={0.35} color="#f2f0eb" />
            <pointLight position={[0, 2.5, 3]} intensity={0.48} color="#ffffff" />
            <pointLight position={[-2, 0, 2]} intensity={0.22} color="#E85D4C" />
            <ProductOrbScene scrollProgress={scrollProgress} activeSection={activeSection} />
          </Suspense>
        </Canvas>
      )}
    </div>
  );
}
