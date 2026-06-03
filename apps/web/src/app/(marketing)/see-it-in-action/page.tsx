"use client";

import { useState } from "react";
import Link from "next/link";
import { RevealOnScroll } from "@/components/marketing/RevealOnScroll";
import { SectionHeader } from "@/components/marketing/SectionHeader";
import { BRAND_SUBHEAD, BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

const steps = [
  {
    title: "Tell us about your company",
    body: "Add the basics once: who you serve, what you sell, and the goals you want to conquer next.",
  },
  {
    title: "Get a strategy that fits",
    body: "Start from a custom strategy blueprint built for your unique market angle, then refine it as your product grows.",
  },
  {
    title: "Refine through conversation",
    body: "Explore directions, query positioning ideas, or request channel suggestions in your strategy workspace.",
  },
  {
    title: "Set your creative direction",
    body: "Establish brand voice parameters, visual style preferences, and creative constraints to guide campaign outputs.",
  },
  {
    title: "Create campaigns that land",
    body: "Generate high-conversion campaign copy, structured creative briefs, script drafts, and custom distribution schedules.",
  },
  {
    title: "Scale across brands",
    body: "Stoa keeps workspaces and contexts separate so you can easily manage a portfolio of distinct brands.",
  },
];

const STEP_LOGS = [
  [
    "SYS: Booting intake node...",
    "INGEST: Parsing company brief & profile...",
    "INGEST: Key metrics mapped: B2B, dev-tools, high growth.",
    "STATUS: Brand profile compiled and indexed."
  ],
  [
    "SYS: Scanning market routing options...",
    "ROUTER: Evaluated 18 channels.",
    "ROUTER: Selected: github/trending, hn/show, tech_blogs.",
    "STATUS: Strategy blueprint compiled successfully."
  ],
  [
    "SYS: Opening context workspace stream...",
    "STREAM: Ready to ingest conversation signals.",
    "STREAM: Tuning parameters: temperature=0.15, cost=optimal.",
    "STATUS: Interactive workspace stream active."
  ],
  [
    "SYS: Loading creative guideline compiler...",
    "COMPILE: Target tone set to 'technical, minimalist, hyper-efficient'.",
    "COMPILE: Layout constraints locked to sharp grid aesthetics.",
    "STATUS: Creative direction guidelines validated."
  ],
  [
    "SYS: Generating launch-ready campaign templates...",
    "BUILD: campaign.json compiled (organic_thrust: 0.95).",
    "BUILD: strategy.md compiled (open-core transparency).",
    "STATUS: Launch assets synthesized."
  ],
  [
    "SYS: Multiplexing brand contexts...",
    "ISOLATION: Tenant context #4 locked and isolated.",
    "ISOLATION: Checking boundary protection... 100% SECURE.",
    "STATUS: Separate tenant workspaces online."
  ]
];

const atAGlance = [
  "Secure sign-in",
  "Separate context for every brand",
  "Strategy blueprints & campaign drafts",
  "Unified brand voice continuity",
  "Clean separate workspaces",
];

export default function SeeItInActionPage() {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const activeLogs = hoveredIdx !== null ? STEP_LOGS[hoveredIdx] : [
    "SYS: System idle. Awaiting step selection...",
    "SYS: Heartbeat active · 180ms latency.",
    "SYS: Hover over any step on the right to simulate compilation logs."
  ];

  return (
    <div className="container-page py-16 md:py-24">
      <RevealOnScroll>
        <SectionHeader
          eyebrow="THE STOA WAY"
          title="From brand context to strategy and campaign execution."
          lead={`${BRAND_TAGLINE} ${BRAND_SUBHEAD}`}
        />
      </RevealOnScroll>

      {/* Mobile "At a Glance" Widget */}
      <div className="mt-10 border border-outline-variant bg-surface-container-lowest p-5 lg:hidden font-mono text-xs text-on-surface">
        <p className="text-[10px] text-primary font-bold uppercase tracking-wider">[AT_A_GLANCE]</p>
        <ul className="mt-3 space-y-2 text-on-surface-variant">
          {atAGlance.map((line) => (
            <li key={line} className="flex gap-2">
              <span className="mt-1.5 h-1.5 w-1.5 bg-primary" />
              {line}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-16 lg:grid lg:grid-cols-[0.9fr_1.1fr] lg:gap-16">
        
        {/* Sticky Dashboard Panel (Left) */}
        <aside className="relative mb-12 lg:mb-0">
          <div className="sticky top-28 hidden overflow-hidden border border-outline-variant bg-surface-container-lowest p-6 shadow-card lg:block font-mono text-xs">
            <div className="flex items-center justify-between border-b border-outline-variant/60 pb-2 mb-4 bg-surface-container-lowest select-none">
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 bg-primary" />
                <span className="h-2 w-2 bg-secondary" />
                <span className="h-2 w-2 bg-outline-variant" />
                <span className="ml-1.5 text-[9px] text-on-surface-variant">stoa@compiler:~</span>
              </div>
              <span className="text-[9px] text-primary font-bold">
                {hoveredIdx !== null ? `STEP_${hoveredIdx + 1}_LOGS` : "SYSTEM_IDLE"}
              </span>
            </div>

            {/* Live simulation logs */}
            <div className="bg-surface border border-outline-variant/40 p-4 h-56 flex flex-col gap-1.5 overflow-y-auto leading-relaxed select-none">
              {activeLogs.map((log, index) => {
                let colorClass = "text-on-surface-variant";
                if (log.startsWith("SYS:")) colorClass = "text-secondary";
                if (log.startsWith("STATUS:")) colorClass = "text-emerald-400 font-semibold";
                if (log.startsWith("INGEST:") || log.startsWith("COMPILE:")) colorClass = "text-primary/95";
                
                return (
                  <div key={index} className={cn("flex gap-2.5 items-start", colorClass)}>
                    <span className="text-outline-variant/60">{(index + 1).toString().padStart(2, "0")}</span>
                    <span>{log}</span>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 border-t border-outline-variant/40 pt-4 text-on-surface-variant font-mono select-none">
              <p className="text-[10px] text-secondary font-bold uppercase tracking-widest">[METRICS_OVERVIEW]</p>
              <ul className="mt-3 space-y-2 text-[11px] leading-relaxed">
                {atAGlance.map((line) => (
                  <li key={line} className="flex items-center gap-2">
                    <span className="h-1 w-1 bg-primary" />
                    {line}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </aside>

        {/* Steps List (Right) */}
        <div className="space-y-6">
          {steps.map((s, i) => {
            const isHovered = hoveredIdx === i;
            return (
              <RevealOnScroll key={s.title} delay={0.04 * i}>
                <article 
                  onMouseEnter={() => setHoveredIdx(i)}
                  onMouseLeave={() => setHoveredIdx(null)}
                  className={cn(
                    "relative border p-6 transition-all duration-300 font-mono text-xs select-none",
                    isHovered 
                      ? "border-primary bg-primary/5 shadow-glow" 
                      : "border-outline-variant/60 bg-surface/20 text-on-surface-variant hover:border-secondary hover:text-on-surface"
                  )}
                >
                  {/* Decorative High-tech Corner Crosses */}
                  <div className="absolute top-0 left-0 w-1.5 h-1.5 border-t border-l border-primary/40" />
                  <div className="absolute top-0 right-0 w-1.5 h-1.5 border-t border-r border-primary/40" />
                  <div className="absolute bottom-0 left-0 w-1.5 h-1.5 border-b border-l border-primary/40" />
                  <div className="absolute bottom-0 right-0 w-1.5 h-1.5 border-b border-r border-primary/40" />

                  <span className="text-[10px] text-primary font-bold uppercase tracking-wider">
                    [STEP {String(i + 1).padStart(2, "0")}]
                  </span>
                  <h2 className="mt-3 font-display text-lg font-bold tracking-tight text-on-surface uppercase">
                    {s.title}
                  </h2>
                  <p className="mt-2 text-[11px] leading-relaxed text-on-surface-variant">
                    {s.body}
                  </p>
                </article>
              </RevealOnScroll>
            );
          })}
        </div>

      </div>

      <RevealOnScroll>
        <div className="mt-20 border border-outline-variant p-8 text-center bg-surface-container-lowest font-mono">
          <span className="text-[10px] text-primary font-bold uppercase tracking-wider">[READY_TO_DEPLOY]</span>
          <p className="mt-3 font-display text-2xl font-bold text-on-surface uppercase">Try it now</p>
          <p className="mt-2 text-xs text-on-surface-variant">{BRAND_SUBHEAD}</p>
          <Link href="/waitlist" className="btn-primary mt-6 px-6 py-2.5 text-xs font-bold uppercase tracking-wider font-mono">
            GET_STARTED.SH
          </Link>
        </div>
      </RevealOnScroll>
    </div>
  );
}
