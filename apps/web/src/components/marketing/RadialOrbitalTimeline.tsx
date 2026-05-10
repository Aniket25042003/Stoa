"use client";

import { Search, Sparkles, Telescope, PenLine } from "lucide-react";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const nodes = [
  { label: "Master Agent", sub: "Orchestrates strategy", x: 465, y: 120, icon: Sparkles },
  { label: "Research", sub: "Discovers market signals", x: 125, y: 190, icon: Search },
  { label: "Reasoning", sub: "Scores ICP + channels", x: 145, y: 375, icon: Telescope },
  { label: "Writing", sub: "Builds execution narrative", x: 500, y: 380, icon: PenLine },
];

export function RadialOrbitalTimeline() {
  const reduceMotion = useReducedMotion();

  return (
    <div className="relative overflow-hidden rounded-[2rem] border border-outline-variant/60 bg-slate-deep px-4 py-8 text-white shadow-card md:px-8 md:py-10">
      <div className="absolute inset-0 opacity-30 [background-image:linear-gradient(to_right,rgb(255_255_255_/_0.08)_1px,transparent_1px),linear-gradient(to_bottom,rgb(255_255_255_/_0.08)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="absolute left-1/2 top-[22%] h-48 w-48 -translate-x-1/2 rounded-full bg-primary/25 blur-3xl" />
      <div className="relative">
        <p className="text-center font-display text-4xl font-bold tracking-[-0.03em]">Radial Orbital Timeline</p>
        <p className="mt-2 text-center text-sm text-white/70">Massive nodes, moving layers, and an interactive star-map flow.</p>
      </div>

      <div className="relative mt-6 overflow-hidden rounded-2xl border border-white/10 bg-black/20 p-2 md:p-4">
        <svg viewBox="0 0 640 460" className="w-full">
          <g className={reduceMotion ? "" : "origin-center motion-safe:animate-[spin_30s_linear_infinite]"}>
            <ellipse cx="320" cy="250" rx="250" ry="118" fill="none" stroke="rgb(99 102 241 / 40%)" strokeWidth="1.5" />
            <ellipse cx="320" cy="250" rx="200" ry="95" fill="none" stroke="rgb(99 102 241 / 32%)" strokeWidth="1.5" />
            <ellipse cx="320" cy="250" rx="150" ry="72" fill="none" stroke="rgb(99 102 241 / 28%)" strokeWidth="1.5" />
            <ellipse cx="320" cy="250" rx="102" ry="48" fill="none" stroke="rgb(139 92 246 / 35%)" strokeWidth="1.5" />
          </g>

          <circle cx="320" cy="250" r="50" fill="rgb(192 193 255 / 20%)" />
          <circle cx="320" cy="250" r="34" fill="rgb(139 92 246 / 35%)" />
          <text x="320" y="246" textAnchor="middle" className="fill-white text-[13px] font-bold">
            Master
          </text>
          <text x="320" y="263" textAnchor="middle" className="fill-white text-[13px] font-bold">
            Plan
          </text>

          {nodes.map((node) => {
            const Icon = node.icon;
            return (
              <g key={node.label}>
                <circle cx={node.x} cy={node.y} r="14" fill="rgb(117 119 255 / 55%)" />
                <circle cx={node.x} cy={node.y} r="10" fill="rgb(12 16 30)" />
                <foreignObject x={node.x - 8} y={node.y - 8} width="16" height="16">
                  <Icon className="h-4 w-4 text-inverse-primary" />
                </foreignObject>
                <text x={node.x + 18} y={node.y - 2} className="fill-white text-[13px] font-semibold">
                  {node.label}
                </text>
                <text x={node.x + 18} y={node.y + 13} className="fill-white/60 text-[11px]">
                  {node.sub}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
