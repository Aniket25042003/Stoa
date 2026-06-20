/**
 * @file apps/web/src/components/marketing/SeeItInActionWalkthrough.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React, Framer Motion
 */
"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { useScrollSpy } from "@/hooks/useScrollSpy";
import { cn } from "@/lib/cn";

export type WalkthroughStep = {
  module: string;
  title: string;
  body: string;
  detail: string;
  inputs: string[];
  outputs: string[];
  logs: string[];
};

const STICKY_TOP_PX = 116;
const STICKY_TOP = "7.25rem";

/**
 * Handles log tone behavior for this part of the Stoa application.
 *
 * @param log - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function logTone(log: string) {
  if (log.startsWith("STATUS")) return "text-emerald-600";
  if (log.startsWith("SYS")) return "text-mkt-accent-warm";
  if (
    log.startsWith("INGEST") ||
    log.startsWith("COMPILE") ||
    log.startsWith("BUILD") ||
    log.startsWith("ROUTER") ||
    log.startsWith("STREAM") ||
    log.startsWith("ISOLATION")
  ) {
    return "text-mkt-accent";
  }
  return "text-mkt-muted";
}

/**
 * Handles detail list behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function DetailList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="font-dm-sans text-[8px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
        {label}
      </p>
      <ul className="mt-2 space-y-1.5">
        {items.map((item) => (
          <li key={item} className="flex gap-2 font-dm-sans text-[11px] leading-snug text-mkt-ink/80">
            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-mkt-accent/60" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/**
 * Handles compiler panel behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function CompilerPanel({
  step,
  stepIndex,
  totalSteps,
  visibleLogCount,
}: {
  step: WalkthroughStep;
  stepIndex: number;
  totalSteps: number;
  visibleLogCount: number;
}) {
  const visibleLogs = step.logs.slice(0, visibleLogCount);

  return (
    <div className="flex max-h-[calc(100vh-8.5rem)] flex-col rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/95 shadow-[0_16px_48px_-24px_rgba(79,70,229,0.12)]">
      <div className="flex items-center justify-between border-b border-mkt-ink/[0.06] bg-mkt-surface px-5 py-3">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-mkt-accent-warm/80" />
          <span className="h-2 w-2 rounded-full bg-mkt-accent/80" />
          <span className="h-2 w-2 rounded-full bg-mkt-ink/15" />
          <span className="ml-2 font-dm-sans text-[9px] font-semibold uppercase tracking-wider text-mkt-muted">
            stoa@compiler
          </span>
        </div>
        <span className="font-dm-sans text-[9px] font-bold uppercase tracking-wider text-mkt-accent">
          Step {String(stepIndex + 1).padStart(2, "0")} / {String(totalSteps).padStart(2, "0")}
        </span>
      </div>

      <div className="border-b border-mkt-ink/[0.06] px-5 py-4">
        <div className="mb-3 flex items-center gap-2">
          {Array.from({ length: totalSteps }, (_, i) => (
            <span
              key={i}
              className={cn(
                "h-1 flex-1 rounded-full transition-colors duration-300",
                i <= stepIndex ? "bg-mkt-accent" : "bg-mkt-ink/10"
              )}
            />
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={stepIndex}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            <span className="inline-flex rounded-sm border border-mkt-accent/25 bg-mkt-accent/[0.06] px-2 py-0.5 font-dm-sans text-[8px] font-bold uppercase tracking-[0.18em] text-mkt-accent">
              {step.module}
            </span>
            <p className="mt-3 font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-accent-warm">
              Now running
            </p>
            <h3 className="mt-1.5 font-syne text-xl font-extrabold uppercase leading-tight tracking-tight text-mkt-ink">
              {step.title}
            </h3>
            <p className="mt-2 font-dm-sans text-sm leading-relaxed text-mkt-muted">{step.body}</p>
            <p className="mt-3 font-dm-sans text-xs leading-relaxed text-mkt-ink/70">{step.detail}</p>
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="grid grid-cols-2 gap-4 border-b border-mkt-ink/[0.06] px-5 py-4">
        <AnimatePresence mode="wait">
          <motion.div
            key={`${stepIndex}-io`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="contents"
          >
            <DetailList label="Inputs" items={step.inputs} />
            <DetailList label="Outputs" items={step.outputs} />
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="flex min-h-0 flex-col bg-mkt-surface/60 px-5 py-4">
        <p className="mb-3 font-dm-sans text-[8px] font-bold uppercase tracking-[0.2em] text-mkt-muted">
          Live compilation stream
        </p>
        <div className="flex max-h-48 flex-col gap-2 overflow-y-auto font-dm-sans text-[11px] leading-relaxed">
          <AnimatePresence mode="wait">
            <motion.div
              key={`${stepIndex}-logs`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-2"
            >
              {visibleLogs.map((log, index) => (
                <motion.div
                  key={`${stepIndex}-${index}`}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.22 }}
                  className={cn("flex gap-2.5", logTone(log))}
                >
                  <span className="text-mkt-ink/25">{(index + 1).toString().padStart(2, "0")}</span>
                  <span>{log}</span>
                </motion.div>
              ))}
              {visibleLogCount < step.logs.length ? (
                <div className="flex gap-2.5 text-mkt-accent/70">
                  <span className="text-mkt-ink/25">
                    {(visibleLogCount + 1).toString().padStart(2, "0")}
                  </span>
                  <span className="animate-pulse">Streaming compilation output…</span>
                </div>
              ) : null}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

/**
 * Handles see it in action walkthrough behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function SeeItInActionWalkthrough({
  steps,
  atAGlance,
}: {
  steps: WalkthroughStep[];
  atAGlance: string[];
}) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const stepsColumnRef = useRef<HTMLDivElement>(null);
  const [stepsColumnHeight, setStepsColumnHeight] = useState(0);

  const { activeIndex, setItemRef } = useScrollSpy(steps.length, {
    offsetTop: STICKY_TOP_PX,
  });
  const displayIndex = hoveredIdx ?? activeIndex;
  const activeStep = steps[displayIndex];

  const [visibleLogCount, setVisibleLogCount] = useState(0);

  useEffect(() => {
    const column = stepsColumnRef.current;
    if (!column) return;

    const syncHeight = () => setStepsColumnHeight(column.offsetHeight);
    syncHeight();

    const observer = new ResizeObserver(syncHeight);
    observer.observe(column);
    return () => observer.disconnect();
  }, [steps.length]);

  useEffect(() => {
    setVisibleLogCount(0);
    const logs = activeStep.logs;
    if (logs.length === 0) return;

    let count = 0;
    const timers: ReturnType<typeof setTimeout>[] = [];

    const revealNext = () => {
      count += 1;
      setVisibleLogCount(count);
      if (count < logs.length) {
        timers.push(setTimeout(revealNext, 320));
      }
    };

    timers.push(setTimeout(revealNext, 150));
    return () => timers.forEach(clearTimeout);
  }, [displayIndex, activeStep.logs]);

  return (
    <>
      <div className="mt-10 rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/90 p-5 lg:hidden">
        <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em] text-mkt-accent">
          At a glance
        </p>
        <ul className="mt-3 space-y-2 font-dm-sans text-sm text-mkt-muted">
          {atAGlance.map((line) => (
            <li key={line} className="flex gap-2.5">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-mkt-accent" />
              {line}
            </li>
          ))}
        </ul>
      </div>

      <section className="mt-16 lg:grid lg:grid-cols-[minmax(0,0.95fr)_minmax(0,1.05fr)] lg:items-start lg:gap-12">
        <div
          className="relative hidden lg:block"
          style={stepsColumnHeight > 0 ? { minHeight: stepsColumnHeight } : undefined}
        >
          <div className="sticky z-10" style={{ top: STICKY_TOP }}>
            <CompilerPanel
              step={activeStep}
              stepIndex={displayIndex}
              totalSteps={steps.length}
              visibleLogCount={visibleLogCount}
            />
          </div>
        </div>

        <div ref={stepsColumnRef} className="relative min-w-0 pb-8">
          {steps.map((step, i) => {
            const isActive = displayIndex === i;
            const isPast = displayIndex > i;
            const isLast = i === steps.length - 1;

            return (
              <article
                key={step.title}
                ref={setItemRef(i)}
                onMouseEnter={() => setHoveredIdx(i)}
                onMouseLeave={() => setHoveredIdx(null)}
                className={cn("scroll-mt-[7.25rem]", !isLast && "mb-4 lg:mb-5")}
              >
                <div
                  className={cn(
                    "w-full rounded-sm border p-5 transition-all duration-500 md:p-6",
                    isActive
                      ? "border-mkt-accent/35 bg-mkt-accent/[0.04] shadow-[0_12px_40px_-20px_rgba(79,70,229,0.2)]"
                      : isPast
                        ? "border-mkt-ink/[0.05] bg-mkt-surface/50 opacity-70"
                        : "border-mkt-ink/[0.06] bg-mkt-surface/70 opacity-85"
                  )}
                >
                  <span
                    className={cn(
                      "font-dm-sans text-[9px] font-bold uppercase tracking-[0.2em]",
                      isActive ? "text-mkt-accent" : "text-mkt-muted"
                    )}
                  >
                    Step {String(i + 1).padStart(2, "0")}
                  </span>
                  <h2 className="mt-2 font-syne text-lg font-extrabold uppercase leading-tight tracking-tight text-mkt-ink md:text-xl">
                    {step.title}
                  </h2>
                  <p className="mt-2 max-w-xl font-dm-sans text-sm leading-relaxed text-mkt-muted">
                    {step.body}
                  </p>

                  <div className="mt-4 rounded-sm border border-mkt-ink/[0.06] bg-mkt-surface/80 p-4 lg:hidden">
                    <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-accent">
                      Live output
                    </p>
                    <div className="mt-3 space-y-2 font-dm-sans text-[11px] leading-relaxed">
                      {step.logs.map((log, index) => (
                        <div key={index} className={cn("flex gap-2", logTone(log))}>
                          <span className="text-mkt-ink/25">{(index + 1).toString().padStart(2, "0")}</span>
                          <span>{log}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}
