"use client";

import { Search, Sparkles, Telescope, PenLine } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const CX = 320;
const CY = 250;

type OrbitNode = {
  id: string;
  label: string;
  sub: string;
  Icon: LucideIcon;
  rx: number;
  ry: number;
  speed: number;
  phase: number;
};

const ORBITS: OrbitNode[] = [
  { id: "research", label: "Research", sub: "Discovers market signals", Icon: Search, rx: 102, ry: 48, speed: 0.38, phase: 0 },
  { id: "master", label: "Master Agent", sub: "Orchestrates strategy", Icon: Sparkles, rx: 150, ry: 72, speed: -0.3, phase: 1.2 },
  { id: "reasoning", label: "Reasoning", sub: "Scores ICP + channels", Icon: Telescope, rx: 198, ry: 94, speed: 0.26, phase: 2.45 },
  { id: "writing", label: "Writing", sub: "Builds execution narrative", Icon: PenLine, rx: 232, ry: 108, speed: -0.22, phase: 4 },
];

/** Extra radial gap so label cards sit outside the planet + orbit stroke (reduces overlap while orbiting) */
const LABEL_RADIAL_PAD = 44;

export function RadialOrbitalTimeline() {
  const reduceMotion = useReducedMotion();
  const [elapsedSec, setElapsedSec] = useState(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (reduceMotion) return;
    let frame = 0;
    const loop = (now: number) => {
      if (startRef.current === null) startRef.current = now;
      const t = (now - startRef.current) / 1000;
      setElapsedSec(t);
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(frame);
      startRef.current = null;
    };
  }, [reduceMotion]);

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-outline-variant/60 bg-slate-deep px-3 py-6 text-white shadow-card sm:px-4 md:px-8 md:py-10">
      <div className="pointer-events-none absolute inset-0 opacity-[0.22] [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.07)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-[22%] h-48 w-48 -translate-x-1/2 rounded-full bg-primary/25 blur-3xl" />
      <div className="relative px-1">
        <p className="text-center font-display text-2xl font-bold tracking-[-0.03em] sm:text-3xl md:text-4xl">Radial Orbital Timeline</p>
        <p className="mt-2 text-center text-xs text-white/70 sm:text-sm">
          Master plan at the center — four stages orbit on their own rings, like planets around a star.
        </p>
      </div>

      <div className="relative mt-4 min-h-[280px] w-full overflow-x-auto overflow-y-hidden sm:min-h-[320px] md:mt-6 md:min-h-0">
        <svg
          viewBox="0 0 640 460"
          className="min-w-[min(100%,520px)] w-full max-w-full sm:min-w-0"
          role="img"
          aria-label="Orbital diagram with Master Plan at center and four orbiting stages"
          preserveAspectRatio="xMidYMid meet"
        >
          <ellipse cx={CX} cy={CY} rx="250" ry="118" fill="none" stroke="rgb(99 102 241 / 32%)" strokeWidth="1.2" />
          <ellipse cx={CX} cy={CY} rx="200" ry="95" fill="none" stroke="rgb(99 102 241 / 28%)" strokeWidth="1.2" />
          <ellipse cx={CX} cy={CY} rx="150" ry="72" fill="none" stroke="rgb(99 102 241 / 24%)" strokeWidth="1.2" />
          <ellipse cx={CX} cy={CY} rx="102" ry="48" fill="none" stroke="rgb(139 92 246 / 30%)" strokeWidth="1.2" />

          <circle cx={CX} cy={CY} r="50" fill="rgb(192 193 255 / 18%)" />
          <circle cx={CX} cy={CY} r="34" fill="rgb(139 92 246 / 38%)" />
          <text x={CX} y={CY - 4} textAnchor="middle" className="fill-white text-[13px] font-bold">
            Master
          </text>
          <text x={CX} y={CY + 12} textAnchor="middle" className="fill-white text-[13px] font-bold">
            Plan
          </text>

          {ORBITS.map((node) => {
            const theta = reduceMotion ? node.phase : node.phase + node.speed * elapsedSec;
            const px = CX + node.rx * Math.cos(theta);
            const py = CY + node.ry * Math.sin(theta);
            const rdx = px - CX;
            const rdy = py - CY;
            const rlen = Math.hypot(rdx, rdy) || 1;
            const ux = rdx / rlen;
            const uy = rdy / rlen;
            const Icon = node.Icon;
            const labelFx = ux * LABEL_RADIAL_PAD;
            const labelFy = uy * LABEL_RADIAL_PAD;
            const cardW = 188;
            const cardH = 56;
            /* Mirror card horizontal placement so it stays on-screen and clears the center */
            const cardX = ux >= 0 ? 6 : -cardW - 6;
            const cardY = uy >= 0 ? -cardH / 2 : -cardH / 2;

            return (
              <g key={node.id} transform={`translate(${px}, ${py})`}>
                <circle r="17" fill="rgb(117 119 255 / 40%)" />
                <circle r="12" fill="rgb(12 16 30)" stroke="rgb(192 193 255 / 40%)" strokeWidth="1" />
                <g transform={`translate(${labelFx}, ${labelFy})`}>
                  <foreignObject x={cardX} y={cardY} width={cardW} height={cardH}>
                    <div className="flex h-full items-start gap-2 rounded-lg border border-white/10 bg-black/40 px-2 py-1.5 shadow-lg backdrop-blur-md">
                      <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-white/10">
                        <Icon className="h-4 w-4 text-[rgb(200,201,255)]" strokeWidth={2} aria-hidden />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-[11px] font-semibold leading-tight text-white">{node.label}</p>
                        <p className="mt-0.5 text-[10px] leading-snug text-white/55">{node.sub}</p>
                      </div>
                    </div>
                  </foreignObject>
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
