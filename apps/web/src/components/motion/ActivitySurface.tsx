/**
 * @file apps/web/src/components/motion/ActivitySurface.tsx
 * @layer Application Source
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect, useRef } from "react";
import type { ActivityPhase } from "@/lib/activity-messages";
import { activitySurfaceVariant } from "@/lib/pipeline-phases";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/cn";

/**
 * Handles activity surface behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ActivitySurface({
  phase,
  className,
  compact = false,
}: {
  phase: ActivityPhase;
  className?: string;
  compact?: boolean;
}) {
  const variant = activitySurfaceVariant(phase);
  const reduced = useReducedMotion();
  const height = compact ? "h-36" : "h-48 md:h-56";

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border border-outline-variant/45 bg-surface-container-low/80",
        height,
        className
      )}
      aria-hidden
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/8 via-transparent to-secondary/10" />
      {variant === "planning" || variant === "queued" || variant === "awaiting_plan_approval" ? (
        <PlanningVisual reduced={reduced} />
      ) : null}
      {variant === "research" ? <ResearchVisual reduced={reduced} /> : null}
      {variant === "reasoning" ? <ReasoningVisual reduced={reduced} /> : null}
      {variant === "writing" ? <WritingVisual reduced={reduced} /> : null}
      {variant === "completed" ? <CompletedVisual /> : null}
      {variant === "failed" ? <FailedVisual /> : null}
    </div>
  );
}

/**
 * Handles planning visual behavior for this part of the Stoa application.
 *
 * @param reduced - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function PlanningVisual({ reduced }: { reduced: boolean }) {
  return (
    <>
      <div className={cn("absolute inset-0 opacity-40", !reduced && "hero-dashboard-grid")} />
      <div className="absolute inset-6 rounded-xl border border-outline-variant/30 bg-surface-container-lowest/40" />
    </>
  );
}

/**
 * Handles research visual behavior for this part of the Stoa application.
 *
 * @param reduced - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function ResearchVisual({ reduced }: { reduced: boolean }) {
  return (
    <>
      <div className="absolute inset-0 opacity-30 hero-dashboard-grid" />
      {!reduced ? (
        <div className="absolute inset-x-0 top-0 h-1/2 overflow-hidden">
          <div className="h-px w-full bg-gradient-to-r from-transparent via-primary/60 to-transparent animate-scan" />
        </div>
      ) : null}
      <div className="absolute bottom-6 left-6 right-6 flex h-20 items-end justify-between gap-1.5">
        {[0.35, 0.55, 0.75, 0.5, 0.9, 0.65].map((h, i) => (
          <div
            key={i}
            className="flex-1 rounded-t-md bg-gradient-to-t from-primary/50 to-secondary/40 origin-bottom"
            style={{
              height: `${h * 100}%`,
              animation: reduced ? undefined : `bar-rise 1.2s ease-out ${i * 0.08}s both`,
            }}
          />
        ))}
      </div>
    </>
  );
}

/**
 * Handles reasoning visual behavior for this part of the Stoa application.
 *
 * @param reduced - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function ReasoningVisual({ reduced }: { reduced: boolean }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (reduced) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const nodes = [
      { x: 0.2, y: 0.35 },
      { x: 0.5, y: 0.2 },
      { x: 0.78, y: 0.4 },
      { x: 0.35, y: 0.72 },
      { x: 0.68, y: 0.78 },
    ];
    let frame = 0;
    let t = 0;

    const draw = () => {
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (w === 0 || h === 0) {
        frame = requestAnimationFrame(draw);
        return;
      }
      canvas.width = w;
      canvas.height = h;
      ctx.clearRect(0, 0, w, h);

      const pulse = 0.35 + 0.15 * Math.sin(t * 2);
      ctx.strokeStyle = `rgb(255 107 53 / ${pulse})`;
      ctx.lineWidth = 1;
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          if ((i + j) % 2 === 0) continue;
          ctx.beginPath();
          ctx.moveTo(nodes[i].x * w, nodes[i].y * h);
          ctx.lineTo(nodes[j].x * w, nodes[j].y * h);
          ctx.stroke();
        }
      }

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        const r = 4 + 2 * Math.sin(t * 3 + i);
        ctx.beginPath();
        ctx.arc(n.x * w, n.y * h, r, 0, Math.PI * 2);
        ctx.fillStyle = i % 2 === 0 ? "rgba(255, 107, 53, 0.7)" : "rgba(196, 162, 101, 0.6)";
        ctx.fill();
      }

      t += 0.016;
      frame = requestAnimationFrame(draw);
    };

    frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [reduced]);

  return (
    <>
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      {!reduced ? (
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_40%,rgb(255_107_53_/_0.12),transparent_55%)]" />
      ) : null}
    </>
  );
}

/**
 * Handles writing visual behavior for this part of the Stoa application.
 *
 * @param reduced - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function WritingVisual({ reduced }: { reduced: boolean }) {
  const lines = [0.92, 0.78, 0.85, 0.65, 0.88];
  return (
    <div className="absolute inset-8 flex flex-col justify-center gap-3">
      {lines.map((w, i) => (
        <div
          key={i}
          className="progress-shimmer h-2 rounded-full"
          style={{
            width: `${w * 100}%`,
            animation: reduced ? undefined : `shimmer 2.4s linear infinite`,
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  );
}

/**
 * Handles completed visual behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function CompletedVisual() {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="h-16 w-16 rounded-full border-2 border-primary bg-primary/15 shadow-glow" />
    </div>
  );
}

/**
 * Handles failed visual behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function FailedVisual() {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <div className="h-14 w-14 rounded-full border-2 border-error/50 bg-error-container/40" />
    </div>
  );
}
