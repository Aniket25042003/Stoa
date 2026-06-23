"use client";

import { useId, useLayoutEffect, useRef, useState } from "react";
import { cn } from "@/lib/cn";

const NAV_OFFSET_PX = 118;

type StretchedHeroGridProps = {
  endId: string;
  className?: string;
};

export function StretchedHeroGrid({ endId, className }: StretchedHeroGridProps) {
  const uid = useId().replace(/:/g, "");
  const ref = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(900);

  const gridA = `${uid}-grid-a`;
  const gridB = `${uid}-grid-b`;
  const fadeY = `${uid}-fade-y`;
  const mask = `${uid}-mask`;

  useLayoutEffect(() => {
    const measure = () => {
      const grid = ref.current;
      const end = document.getElementById(endId);
      const zone = grid?.parentElement;
      if (!grid || !end || !zone) return;

      const zoneTop = zone.getBoundingClientRect().top + window.scrollY;
      const endBottom = end.getBoundingClientRect().bottom + window.scrollY;
      setHeight(Math.max(480, endBottom - zoneTop + NAV_OFFSET_PX));
    };

    measure();

    const ro = new ResizeObserver(measure);
    ro.observe(document.documentElement);
    if (ref.current?.parentElement) {
      ro.observe(ref.current.parentElement);
    }

    window.addEventListener("resize", measure);
    return () => {
      ro.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, [endId]);

  return (
    <div
      ref={ref}
      className={cn("pointer-events-none absolute inset-x-0 z-0 overflow-hidden", className)}
      style={{ top: -NAV_OFFSET_PX, height }}
      aria-hidden
    >
      <svg className="absolute inset-0 h-full w-full" preserveAspectRatio="none" aria-hidden>
        <defs>
          <pattern id={gridA} width="44" height="44" patternUnits="userSpaceOnUse" patternTransform="rotate(32)">
            <line
              x1="0"
              y1="0"
              x2="0"
              y2="44"
              stroke="rgba(10,10,10,0.22)"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          </pattern>
          <pattern id={gridB} width="44" height="44" patternUnits="userSpaceOnUse" patternTransform="rotate(148)">
            <line
              x1="0"
              y1="0"
              x2="0"
              y2="44"
              stroke="rgba(10,10,10,0.22)"
              strokeWidth="1"
              vectorEffect="non-scaling-stroke"
            />
          </pattern>
          <linearGradient id={fadeY} x1="0" y1="0" x2="0" y2="1">
            <stop offset="2%" stopColor="white" stopOpacity="0" />
            <stop offset="7%" stopColor="white" stopOpacity="0.2" />
            <stop offset="12%" stopColor="white" stopOpacity="0.35" />
            <stop offset="42%" stopColor="white" stopOpacity="1" />
            <stop offset="62%" stopColor="white" stopOpacity="1" />
            <stop offset="84%" stopColor="white" stopOpacity="0.35" />
            <stop offset="94%" stopColor="white" stopOpacity="0.2" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </linearGradient>
          <mask id={mask}>
            <rect width="100%" height="100%" fill={`url(#${fadeY})`} />
          </mask>
        </defs>
        <rect width="100%" height="100%" fill={`url(#${gridA})`} mask={`url(#${mask})`} />
        <rect width="100%" height="100%" fill={`url(#${gridB})`} mask={`url(#${mask})`} />
      </svg>
    </div>
  );
}
