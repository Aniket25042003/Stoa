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
  /** Radians per second */
  speed: number;
  phase: number;
};

/** Elliptical orbits aligned with decorative rings — planets move along these paths */
const ORBITS: OrbitNode[] = [
  { id: "research", label: "Research", sub: "Discovers market signals", Icon: Search, rx: 102, ry: 48, speed: 0.38, phase: 0 },
  { id: "master", label: "Master Agent", sub: "Orchestrates strategy", Icon: Sparkles, rx: 150, ry: 72, speed: -0.3, phase: 1.2 },
  { id: "reasoning", label: "Reasoning", sub: "Scores ICP + channels", Icon: Telescope, rx: 198, ry: 94, speed: 0.26, phase: 2.45 },
  { id: "writing", label: "Writing", sub: "Builds execution narrative", Icon: PenLine, rx: 242, ry: 114, speed: -0.22, phase: 4 },
];

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
    <div className="relative overflow-hidden rounded-[2rem] border border-outline-variant/60 bg-slate-deep px-4 py-8 text-white shadow-card md:px-8 md:py-10">
      <div className="pointer-events-none absolute inset-0 opacity-[0.22] [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.07)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-[22%] h-48 w-48 -translate-x-1/2 rounded-full bg-primary/25 blur-3xl" />
      <div className="relative">
        <p className="text-center font-display text-4xl font-bold tracking-[-0.03em]">Radial Orbital Timeline</p>
        <p className="mt-2 text-center text-sm text-white/70">
          Master plan at the center — four stages orbit on their own rings, like planets around a star.
        </p>
      </div>

      <div className="relative mt-6 overflow-hidden rounded-2xl border border-white/10 bg-black/25 p-2 md:p-4">
        <svg viewBox="0 0 640 460" className="w-full" role="img" aria-label="Orbital diagram with Master Plan at center and four orbiting stages">
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
            const lx = (rdx / rlen) * 26;
            const ly = (rdy / rlen) * 26;
            const Icon = node.Icon;
            return (
              <g key={node.id} transform={`translate(${px}, ${py})`}>
                <circle r="16" fill="rgb(117 119 255 / 45%)" />
                <circle r="11" fill="rgb(12 16 30)" stroke="rgb(192 193 255 / 35%)" strokeWidth="1" />
                <foreignObject x={-8} y={-8} width={16} height={16}>
                  <div className="flex h-4 w-4 items-center justify-center text-[rgb(200,201,255)]">
                    <Icon className="h-3.5 w-3.5" strokeWidth={2} aria-hidden />
                  </div>
                </foreignObject>
                <g transform={`translate(${lx}, ${ly})`}>
                  <text x={14} y={3} className="fill-white text-[12px] font-semibold">
                    {node.label}
                  </text>
                  <text x={14} y={17} className="fill-white/58 text-[10px]">
                    {node.sub}
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
