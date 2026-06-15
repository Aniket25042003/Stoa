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
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(79,70,229,0.1)_0%,rgba(250,248,244,0.55)_40%,transparent_75%)]" />

      {!showCanvas && (
        <img
          src={fallbackSrc}
          alt=""
          className="absolute inset-0 m-auto h-[min(340px,72%)] w-auto max-w-[min(340px,72%)] rounded-2xl object-cover opacity-100 shadow-[0_24px_80px_rgba(79,70,229,0.12)] brightness-[1.12] contrast-[1.02]"
        />
      )}

      {showCanvas && (
        <Canvas
          dpr={Math.min(dpr, 2)}
          camera={{ position: [0, 0.08, 5.4], fov: 32 }}
          gl={{
            alpha: true,
            antialias: true,
            powerPreference: "high-performance",
            stencil: false,
            toneMappingExposure: 1.28,
          }}
          style={{ background: "transparent" }}
          className="h-full w-full"
        >
          <Suspense fallback={null}>
            <ambientLight intensity={0.95} color="#faf8f4" />
            <hemisphereLight intensity={0.65} color="#ffffff" groundColor="#f0ece4" />
            <directionalLight
              position={[4, 6, 5]}
              intensity={1.1}
              color="#fffef8"
            />
            <directionalLight position={[-4, 3, -2]} intensity={0.45} color="#eef0ff" />
            <directionalLight position={[0, 2, 4]} intensity={0.55} color="#ffffff" />
            <pointLight position={[0, 2.5, 3]} intensity={0.35} color="#ffffff" />
            <ProductOrbScene scrollProgress={scrollProgress} activeSection={activeSection} />
          </Suspense>
        </Canvas>
      )}
    </div>
  );
}
