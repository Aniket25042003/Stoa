"use client";

import { useState } from "react";

const INPUTS = [
  { id: "brief", name: "campaign_brief.txt", size: "4.2kb", type: "text/plain", data: "Goal: Introduce Stoa to dev-focused founders" },
  { id: "signals", name: "competitor_signals.json", size: "12.8kb", type: "application/json", data: "Competitors: Hydra, Codag. Target channels: GitHub, HN" },
  { id: "docs", name: "workspace_wiki.md", size: "8.5kb", type: "text/markdown", data: "Core product features: High performance engine, minimal latency" },
  { id: "metrics", name: "acquisition_history.csv", size: "2.1kb", type: "text/csv", data: "Past conversions: Organic leads 42% higher on technical blogs" },
];

const OUTPUT_YAML = `---
strategy:
  target_audience: "technical_founders"
  routing:
    - path: "github/developer-showcase"
      thrust: 0.95
      priority: HIGH
    - path: "hn/launch-thread"
      thrust: 0.82
      priority: HIGH
  tactics:
    - vector: "open_core_transparency"
      conversion_est: "2.4x"
    - vector: "telemetry_monitors"
      conversion_est: "1.8x"
  metadata:
    compiled_by: "stoa-core-v2"
    integrity: 1.00
    latency: "180ms"`;

export function RadialOrbitalTimeline() {
  const [activeInput, setActiveInput] = useState<string>("brief");

  return (
    <div className="relative overflow-hidden border border-outline-variant bg-surface-container-lowest p-6 text-on-surface shadow-card">
      {/* Subtle CRT line scanner overlay */}
      <div className="pointer-events-none absolute inset-0 opacity-[0.15] [background-image:linear-gradient(to_bottom,rgb(255_255_255_/_0.07)_1px,transparent_1px)] [background-size:100%_4px]" />
      
      <div className="mb-6">
        <span className="text-[10px] text-primary font-bold uppercase tracking-wider font-mono">Pipeline Funnel</span>
        <h2 className="mt-1 font-display text-2xl font-bold tracking-tight sm:text-3xl text-on-surface">
          Unstructured Intake to Strategic Blueprint
        </h2>
        <p className="mt-1 text-xs text-on-surface-variant font-mono">
          Feed raw logs, competitor telemetry, and documents. Compile a structured strategy roadmap.
        </p>
      </div>

      {/* Funnel Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        
        {/* Left Side: Unstructured Inputs (4 Cols) */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <div className="text-[10px] font-mono text-secondary uppercase tracking-widest mb-1">
            [Input Data Slots]
          </div>
          {INPUTS.map((item) => {
            const isActive = activeInput === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveInput(item.id)}
                className={`w-full text-left p-3 border font-mono transition-all duration-200 select-none cursor-pointer ${
                  isActive
                    ? "border-primary bg-primary/5 text-on-surface"
                    : "border-outline-variant/60 bg-surface/20 text-on-surface-variant hover:border-secondary hover:text-on-surface"
                }`}
              >
                <div className="flex justify-between items-center text-xs">
                  <span className={isActive ? "text-primary font-bold" : ""}>
                    {item.name}
                  </span>
                  <span className="text-[10px] text-secondary">{item.size}</span>
                </div>
                <div className="mt-1 text-[10px] truncate opacity-60">
                  {item.data}
                </div>
              </button>
            );
          })}
        </div>

        {/* Middle Side: SVG Interactive Flow (3 Cols) */}
        <div className="lg:col-span-3 h-48 lg:h-64 flex items-center justify-center relative">
          <svg
            className="w-full h-full overflow-visible"
            viewBox="0 0 200 240"
            preserveAspectRatio="none"
          >
            {/* Input Paths converging to center */}
            {/* Paths: Left points are Y=30, 90, 150, 210. Right point is Y=120 */}
            <path d="M 0 30 Q 80 30, 140 120" fill="none" stroke="var(--outline)" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.45" />
            <path d="M 0 90 Q 80 90, 140 120" fill="none" stroke="var(--outline)" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.45" />
            <path d="M 0 150 Q 80 150, 140 120" fill="none" stroke="var(--outline)" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.45" />
            <path d="M 0 210 Q 80 210, 140 120" fill="none" stroke="var(--outline)" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.45" />
            
            {/* Funnel Merge Neck */}
            <path d="M 140 120 L 200 120" fill="none" stroke="var(--outline)" strokeWidth="2" opacity="0.7" />

            {/* Glowing flowing particles along the active path */}
            {activeInput === "brief" && (
              <circle r="4.5" fill="#FF571A">
                <animateMotion
                  path="M 0 30 Q 80 30, 140 120 L 200 120"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
            )}
            {activeInput === "signals" && (
              <circle r="4.5" fill="#FF571A">
                <animateMotion
                  path="M 0 90 Q 80 90, 140 120 L 200 120"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
            )}
            {activeInput === "docs" && (
              <circle r="4.5" fill="#FF571A">
                <animateMotion
                  path="M 0 150 Q 80 150, 140 120 L 200 120"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
            )}
            {activeInput === "metrics" && (
              <circle r="4.5" fill="#FF571A">
                <animateMotion
                  path="M 0 210 Q 80 210, 140 120 L 200 120"
                  dur="1.5s"
                  repeatCount="indefinite"
                />
              </circle>
            )}

            {/* Funnel Center compiling junction circle */}
            <g transform="translate(140, 120)">
              <circle r="12" fill="var(--surface)" stroke="var(--outline)" strokeWidth="2" />
              <circle r="6" fill="#FF571A" className="animate-ping" />
            </g>
          </svg>
        </div>

        {/* Right Side: Compiled Structured Output (5 Cols) */}
        <div className="lg:col-span-5 flex flex-col h-full gap-3">
          <div className="text-[10px] font-mono text-secondary uppercase tracking-widest mb-1 flex justify-between items-center">
            <span>[Output Strategic Capsule]</span>
            <span className="text-[9px] text-emerald-400 font-bold tracking-normal uppercase border border-emerald-400/30 bg-emerald-400/10 px-1.5 py-0.5 select-none">
              Compiled OK
            </span>
          </div>

          <div className="flex-1 bg-surface border border-outline-variant/60 p-4 font-mono text-[11px] leading-relaxed relative overflow-hidden h-[260px] flex flex-col">
            {/* Syntax line counts */}
            <div className="flex-1 overflow-y-auto select-all flex gap-3 text-on-surface-variant">
              <div className="text-outline-variant/60 text-right select-none pr-1 border-r border-outline-variant/20 flex flex-col gap-0.5 font-mono">
                {OUTPUT_YAML.split("\n").map((_, idx) => (
                  <span key={idx}>{(idx + 1).toString().padStart(2, "0")}</span>
                ))}
              </div>
              <pre className="text-on-surface text-[10px] overflow-x-auto whitespace-pre font-mono flex-1">
                {OUTPUT_YAML.split("\n").map((line, idx) => {
                  let colorClass = "text-on-surface";
                  if (line.trim().startsWith("-")) colorClass = "text-primary/90";
                  if (line.includes(":")) {
                    const key = line.substring(0, line.indexOf(":"));
                    return (
                      <div key={idx}>
                        <span className="text-secondary">{key}:</span>
                        <span className="text-on-surface">{line.substring(line.indexOf(":") + 1)}</span>
                      </div>
                    );
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
        </div>

      </div>
    </div>
  );
}
