/**
 * @file apps/web/src/components/marketing/ReportPreviewCard.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useState } from "react";
import { cn } from "@/lib/cn";

const FILES = {
  "strategy.md": `# Strategy Blueprint: Q3 Launch

## Target Segment
- Developers, Technical Founders

## Channels
- HN Launch Show
- GitHub Developer Showcases
- Engineering blogs

## Priorities
- 1. Open-core transparency
- 2. Self-hosting docs`,

  "brief.yaml": `brief:
  objective: "Drive signups for Stoa self-serve engine"
  target_audience: "CTOs & Solo Devs"
  key_metrics:
    - active_nodes
    - cost_per_lead: <$10
  creative_direction:
    tone: "technical, minimalist, hyper-efficient"`,

  "campaign.json": `{
  "campaign": "stoa-q3-rollout",
  "schedule": "2026-06-15",
  "budget_allocation": {
    "organic_vectors": "80%",
    "newsletter_sponsorships": "20%"
  },
  "telemetry": {
    "latency_check": "ok",
    "conversion_thrust": "optimal"
  }
}`
};

type FileKey = keyof typeof FILES;

/**
 * Handles report preview card behavior for this part of the Stoa application.
 *
 * @param className - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ReportPreviewCard({ className }: { className?: string }) {
  const [activeTab, setActiveTab] = useState<FileKey>("strategy.md");

  const activeContent = FILES[activeTab];
  const lines = activeContent.split("\n");

  return (
    <div className={cn("relative overflow-hidden border border-outline-variant bg-surface-container-lowest font-mono text-xs text-on-surface shadow-card flex flex-col", className)}>
      {/* Editor Header */}
      <div className="flex items-center justify-between border-b border-outline-variant/60 bg-surface px-4 py-2 select-none">
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 bg-primary" />
          <span className="h-2 w-2 bg-secondary" />
          <span className="h-2 w-2 bg-outline-variant" />
        </div>
        <span className="text-[10px] text-on-surface-variant font-bold">STOA_WORKSPACE_EDITOR</span>
      </div>

      {/* Editor Tabs */}
      <div className="flex border-b border-outline-variant/60 bg-surface/50 select-none">
        {(Object.keys(FILES) as FileKey[]).map((tab) => {
          const isActive = tab === activeTab;
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "px-4 py-2 text-[10px] border-r border-outline-variant/60 font-semibold cursor-pointer transition-colors",
                isActive
                  ? "bg-surface-dim text-primary border-b-2 border-b-primary"
                  : "text-on-surface-variant/80 hover:text-on-surface hover:bg-surface/20"
              )}
            >
              {tab}
            </button>
          );
        })}
      </div>

      {/* Editor Text Area */}
      <div className="p-4 bg-surface-dim flex-1 flex gap-3 min-h-[220px] select-text overflow-y-auto">
        {/* Line Numbers */}
        <div className="text-outline-variant/60 text-right pr-2 border-r border-outline-variant/20 flex flex-col gap-0.5 select-none font-mono">
          {lines.map((_, idx) => (
            <span key={idx}>{(idx + 1).toString().padStart(2, "0")}</span>
          ))}
        </div>
        
        {/* Code Content */}
        <pre className="text-on-surface text-[11px] leading-normal font-mono overflow-x-auto whitespace-pre flex-1">
          {lines.map((line, idx) => {
            let colorClass = "text-on-surface";
            
            // Basic syntax color overlays based on markdown, yaml, and json structure
            if (activeTab === "strategy.md") {
              if (line.startsWith("#")) colorClass = "text-primary font-bold";
              else if (line.startsWith("-")) colorClass = "text-secondary";
            } else if (activeTab === "brief.yaml") {
              if (line.includes(":")) colorClass = "text-secondary";
              if (line.trim().startsWith("-")) colorClass = "text-primary/90";
            } else if (activeTab === "campaign.json") {
              if (line.includes('"')) colorClass = "text-secondary";
            }
            
            return (
              <div key={idx} className={colorClass}>
                {line}
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
}
