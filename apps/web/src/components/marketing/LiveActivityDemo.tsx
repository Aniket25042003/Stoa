/**
 * @file apps/web/src/components/marketing/LiveActivityDemo.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect, useState } from "react";
import { BRAND_TAGLINE } from "@/lib/brand";
import { cn } from "@/lib/cn";

interface Step {
  id: string;
  num: string;
  name: string;
  desc: string;
  logs: string[];
}

const STEPS: Step[] = [
  {
    id: "intake",
    num: "01",
    name: "INTAKE CONTEXT",
    desc: "Ingests brand wiki, documents, and competitor signals.",
    logs: [
      "INGEST: Parsing campaign_brief.txt...",
      "INGEST: Found target audience segment: technical founders",
      "INGEST: Indexing workspace competitor_signals.json...",
      "INGEST: Workspace indexing completed successfully."
    ]
  },
  {
    id: "vectoring",
    num: "02",
    name: "CHANNEL MAP",
    desc: "Identifies organic acquisition channels with maximum conversion potential.",
    logs: [
      "ANALYZE: Scanning target acquisition vectors...",
      "ANALYZE: Priority paths detected: GitHub Showcases, HN Launches",
      "ANALYZE: High conversions detected on engineering blogs."
    ]
  },
  {
    id: "compile",
    num: "03",
    name: "STRATEGY COMPILE",
    desc: "Synthesizes tactical strategic roadmap and content blueprints.",
    logs: [
      "SYNTH: Compiling distribution strategy blueprints...",
      "SYNTH: Vector mapped: open_core_transparency (conversion_est: 2.4x)",
      "SYNTH: Generating traffic loops & metrics logs..."
    ]
  },
  {
    id: "routing",
    num: "04",
    name: "ROUTE RULES",
    desc: "Configures automatic audience routing rules and launch schedules.",
    logs: [
      "ROUTER: Establishing priority queues...",
      "ROUTER: Configured path github/developer-showcase -> THRUST: 0.95",
      "ROUTER: Strategy bundle compiled. Ready for deployment."
    ]
  }
];

/**
 * Handles live activity demo behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function LiveActivityDemo({ className }: { className?: string }) {
  const [stepIdx, setStepIdx] = useState(0);
  const [visibleLogs, setVisibleLogs] = useState<string[]>([]);
  const [logIdx, setLogIdx] = useState(0);

  const activeStep = STEPS[stepIdx];

  // Rotate through steps
  useEffect(() => {
    const timer = setInterval(() => {
      setStepIdx((prev) => (prev + 1) % STEPS.length);
      setLogIdx(0);
      setVisibleLogs([]);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  // Animate printing of logs for the active step
  useEffect(() => {
    if (logIdx < activeStep.logs.length) {
      const logTimer = setTimeout(() => {
        setVisibleLogs((prev) => [...prev, activeStep.logs[logIdx]]);
        setLogIdx((prev) => prev + 1);
      }, 800 + Math.random() * 600);
      return () => clearTimeout(logTimer);
    }
  }, [stepIdx, logIdx, activeStep]);

  return (
    <div className={cn("relative overflow-hidden border border-outline-variant bg-surface-container-lowest p-6 md:p-10", className)}>
      <div className="absolute right-0 top-0 h-64 w-64 translate-x-1/3 -translate-y-1/3 rounded-full bg-primary/10 blur-3xl" />
      
      <div className="relative grid gap-10 lg:grid-cols-12 items-center">
        {/* Left column - Description & Horizontal Steps */}
        <div className="lg:col-span-5 flex flex-col gap-6">
          <div>
            <span className="text-[10px] text-primary font-bold uppercase tracking-wider font-mono">[STOA IN ACTION]</span>
            <h3 className="mt-2 font-display text-2xl font-bold leading-tight tracking-tight text-on-surface md:text-3xl">
              {BRAND_TAGLINE}
            </h3>
            <p className="mt-3 text-xs leading-relaxed text-on-surface-variant font-mono">
              Build strategy, map traffic acquisition channels, and draft launch tactical roadmaps in a unified compiler.
            </p>
          </div>

          {/* Interactive Steps List */}
          <div className="flex flex-col gap-3 font-mono">
            {STEPS.map((step, idx) => {
              const isActive = idx === stepIdx;
              const isPast = idx < stepIdx;
              return (
                <div 
                  key={step.id} 
                  className={cn(
                    "border p-3 transition-colors duration-300 text-xs",
                    isActive 
                      ? "border-primary bg-primary/5" 
                      : "border-outline-variant/60 bg-surface/20"
                  )}
                >
                  <div className="flex justify-between items-center">
                    <span className={cn("font-bold", isActive ? "text-primary" : "text-on-surface-variant")}>
                      [{step.num}] {step.name}
                    </span>
                    <span className="text-[10px]">
                      {isActive && <span className="text-primary animate-pulse">RUNNING</span>}
                      {isPast && <span className="text-emerald-400">DONE</span>}
                      {!isActive && !isPast && <span className="text-on-surface-variant/40">QUEUED</span>}
                    </span>
                  </div>
                  <p className="mt-1 text-[10px] text-on-surface-variant/80">{step.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right column - Mock Console Display */}
        <div className="lg:col-span-7 relative border border-outline-variant bg-surface-dim p-4 font-mono text-xs text-on-surface shadow-card overflow-hidden">
          <div className="flex items-center justify-between border-b border-outline-variant/50 pb-2 mb-3 select-none">
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 bg-primary" />
              <span className="h-2 w-2 bg-secondary" />
              <span className="h-2 w-2 bg-outline-variant" />
              <span className="ml-1.5 text-[9px] text-on-surface-variant">stoa@compiler-logs:~</span>
            </div>
            <div className="text-[9px] text-secondary font-bold uppercase">STDOUT_STREAM</div>
          </div>

          {/* Steps checklist overlay */}
          <div className="mb-4 flex flex-col gap-1.5 text-[11px] border-b border-outline-variant/30 pb-3">
            {STEPS.map((step, idx) => {
              const isActive = idx === stepIdx;
              const isPast = idx < stepIdx;
              let marker = "[ ]";
              let colorClass = "text-on-surface-variant/40";
              
              if (isPast) {
                marker = "[✔]";
                colorClass = "text-emerald-400";
              } else if (isActive) {
                marker = "[>]";
                colorClass = "text-primary font-bold";
              }
              
              return (
                <div key={step.id} className={cn("flex gap-2.5 items-center", colorClass)}>
                  <span>{marker}</span>
                  <span>{step.name}</span>
                </div>
              );
            })}
          </div>

          {/* Dynamic live scrolling logs */}
          <div className="h-44 overflow-y-auto flex flex-col gap-1 text-[10px] bg-surface/50 p-2.5 border border-outline-variant/30 select-all">
            {visibleLogs.map((log, index) => {
              let textClass = "text-on-surface-variant";
              if (log.startsWith("SUCCESS:")) textClass = "text-emerald-400 font-semibold";
              if (log.startsWith("INGEST:")) textClass = "text-secondary";
              if (log.startsWith("ANALYZE:")) textClass = "text-primary/90";
              if (log.startsWith("SYNTH:")) textClass = "text-secondary";
              if (log.startsWith("ROUTER:")) textClass = "text-primary/90";
              
              return (
                <div key={index} className="flex gap-2 items-start leading-relaxed font-mono">
                  <span className="text-outline-variant/60 select-none">{(index + 1).toString().padStart(2, "0")}</span>
                  <span className={textClass}>{log}</span>
                </div>
              );
            })}
            
            {visibleLogs.length < activeStep.logs.length && (
              <div className="flex gap-2 items-center text-primary/80 animate-pulse select-none">
                <span className="text-outline-variant/60">{(visibleLogs.length + 1).toString().padStart(2, "0")}</span>
                <span>COMPILE_PROGRESS: Loading lines...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
