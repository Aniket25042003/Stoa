/**
 * @file apps/web/src/components/marketing/HeroDashboardOrbit.tsx
 * @layer Frontend Marketing UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useState, useEffect } from "react";

const getLogsForConfig = (model: string, thrust: number): string[] => {
  if (model === "stoa-core-v2") {
    if (thrust >= 70) {
      return [
        "SYS: Booting Stoa strategy compiler v2.5.0-prod...",
        "INGEST: Mapping workspace metadata & assets...",
        `INGEST: Brand identity vector mapped: tone=energetic, engine_thrust=${thrust}%.`,
        "ANALYZE: Scanning high-virality acquisition channels...",
        "ANALYZE: Priority channels locked: github/trending, hn/show.",
        "SYNTH: Compiling distribution tactics & traffic loops...",
        "SYNTH: Generated 4 strategy capsules for Q3 rollout.",
        "ROUTER: Establishing audience traffic routing rules...",
        `SUCCESS: Strategy bundle built successfully in ${Math.round(200 + thrust * 1.5)}ms.`
      ];
    } else {
      return [
        "SYS: Booting Stoa strategy compiler v2.5.0-prod...",
        "INGEST: Mapping workspace metadata & assets...",
        `INGEST: Brand identity vector mapped: tone=minimal, engine_thrust=${thrust}%.`,
        "ANALYZE: Scanning standard acquisition channels...",
        "ANALYZE: Priority channels locked: technical newsletter sponsor, organic search.",
        "SYNTH: Generating standard content blueprints...",
        "SYNTH: Generated 2 strategy capsules.",
        "ROUTER: Allocating traffic weights...",
        `SUCCESS: Strategy bundle built successfully in ${Math.round(150 + thrust * 1.2)}ms.`
      ];
    }
  } else if (model === "stoa-core-v1") {
    if (thrust >= 70) {
      return [
        "SYS: Booting legacy strategy compiler v1.9.4-compat...",
        "INGEST: Loading raw company context records...",
        `INGEST: Target parameters: compatibility_mode=on, thrust=${thrust}%.`,
        "ANALYZE: Looking up static channel definitions...",
        "ANALYZE: Found B2B direct channels: linkedin, partner outreach.",
        "SYNTH: Generating campaign copy ideas...",
        "SYNTH: Outputted 3 legacy briefs.",
        `SUCCESS: Legacy compilation done in ${Math.round(400 + thrust * 2)}ms.`
      ];
    } else {
      return [
        "SYS: Booting legacy strategy compiler v1.9.4-compat...",
        "INGEST: Loading raw company context records...",
        `INGEST: Target parameters: compatibility_mode=on, thrust=${thrust}%.`,
        "ANALYZE: Looking up static channel definitions...",
        "ANALYZE: Found standard search channel definitions.",
        "SYNTH: Generating static copy templates...",
        `SUCCESS: Legacy compilation done in ${Math.round(300 + thrust * 1.8)}ms.`
      ];
    }
  } else {
    // stoa-high-growth
    if (thrust >= 70) {
      return [
        "SYS: Booting Stoa high-growth compiler v3.0.0-alpha...",
        "INGEST: Mapping aggressive market acquisition vectors...",
        `INGEST: Target profiles: high velocity, thrust=${thrust}%.`,
        "ANALYZE: Scanning developer channels for rapid amplification...",
        "ANALYZE: High growth loops mapped to GitHub trending, Reddit showcases, ProductHunt launch.",
        "SYNTH: Compiling hyper-growth virality blueprints...",
        "SYNTH: Generated 6 high-velocity campaign capsules.",
        "ROUTER: Setting aggressive audience routing rules (priority HIGH)...",
        `SUCCESS: High-growth strategy bundle built in ${Math.round(250 + thrust * 1.6)}ms.`
      ];
    } else {
      return [
        "SYS: Booting Stoa high-growth compiler v3.0.0-alpha...",
        "INGEST: Mapping aggressive market acquisition vectors...",
        `INGEST: Target profiles: steady acceleration, thrust=${thrust}%.`,
        "ANALYZE: Scanning standard amplification loops...",
        "ANALYZE: Target loops locked: dev newsletters, niche forums.",
        "SYNTH: Compiling growth blueprints...",
        "SYNTH: Generated 3 campaign capsules.",
        "ROUTER: Setting audience routing rules...",
        `SUCCESS: Growth strategy bundle built in ${Math.round(200 + thrust * 1.4)}ms.`
      ];
    }
  }
};

/**
 * Handles hero dashboard orbit behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function HeroDashboardOrbit() {
  const [model, setModel] = useState("stoa-core-v2");
  const [virality, setVirality] = useState(85);
  const [copied, setCopied] = useState(false);
  const [logIndex, setLogIndex] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [compiling, setCompiling] = useState(false);
  const [progress, setProgress] = useState(100);

  const command = "npx create-stoa-app@latest";

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const startCompilation = () => {
    setCompiling(true);
    setProgress(0);
    setLogs([]);
    setLogIndex(0);
  };

  // Compile log tick animation
  useEffect(() => {
    if (!compiling) return;

    const activeLogs = getLogsForConfig(model, virality);

    if (progress < 100) {
      const timer = setTimeout(() => {
        setProgress((prev) => Math.min(prev + 4, 100));
      }, 50);
      return () => clearTimeout(timer);
    } else {
      // Log line feed animation
      if (logIndex < activeLogs.length) {
        const timer = setTimeout(() => {
          setLogs((prev) => [...prev, activeLogs[logIndex]]);
          setLogIndex((prev) => prev + 1);
        }, 150 + Math.random() * 200);
        return () => clearTimeout(timer);
      } else {
        setCompiling(false);
      }
    }
  }, [compiling, progress, logIndex, model, virality]);

  // Update logs when config changes (if not compiling)
  useEffect(() => {
    if (!compiling) {
      setLogs(getLogsForConfig(model, virality));
    }
  }, [model, virality, compiling]);

  return (
    <div className="relative mx-auto w-full max-w-4xl">
      {/* Background glow effects */}
      <div className="absolute -inset-4 bg-gradient-to-tr from-primary/10 to-secondary/5 blur-2xl opacity-40" />
      
      {/* Terminal Container */}
      <div className="relative border border-outline-variant bg-surface-container-lowest font-mono text-xs text-on-surface shadow-card overflow-hidden">
        {/* Top Header Bar */}
        <div className="flex items-center justify-between border-b border-outline-variant/60 bg-surface px-4 py-2.5 select-none">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 bg-primary/80" />
            <span className="h-2.5 w-2.5 bg-secondary/80" />
            <span className="h-2.5 w-2.5 bg-outline-variant" />
            <span className="ml-2 text-[10px] text-on-surface-variant tracking-wider uppercase font-semibold">STOA_COMPILER_V2</span>
          </div>
          <div className="text-[10px] text-primary font-bold">
            {compiling ? "STATUS: COMPILING..." : "STATUS: ACTIVE"}
          </div>
        </div>

        {/* Inner layout grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 divide-y md:divide-y-0 md:divide-x divide-outline-variant/60">
          
          {/* Left panel - Controls (4 cols) */}
          <div className="md:col-span-4 p-4 flex flex-col gap-4 bg-surface/30">
            <div>
              <span className="text-[10px] text-secondary font-bold uppercase tracking-wider">Parameters</span>
              <div className="mt-3 flex flex-col gap-3">
                {/* Model Selector */}
                <div>
                  <label className="text-[10px] text-on-surface-variant block mb-1">STRATEGY_ENGINE</label>
                  <select 
                    value={model} 
                    onChange={(e) => setModel(e.target.value)}
                    disabled={compiling}
                    className="w-full bg-surface border border-outline-variant px-2 py-1 text-xs text-on-surface focus:outline-none focus:border-primary disabled:opacity-50"
                  >
                    <option value="stoa-core-v2">stoa-core-v2 (recommended)</option>
                    <option value="stoa-core-v1">stoa-core-v1 (legacy)</option>
                    <option value="stoa-high-growth">stoa-high-growth</option>
                  </select>
                </div>

                {/* Virality target slider */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-[10px] text-on-surface-variant">ENGINE_THRUST</label>
                    <span className="text-[10px] text-primary font-bold">{virality}%</span>
                  </div>
                  <input 
                    type="range" 
                    min="10" 
                    max="100" 
                    value={virality}
                    onChange={(e) => setVirality(Number(e.target.value))}
                    disabled={compiling}
                    className="w-full accent-primary bg-surface h-1 cursor-pointer disabled:opacity-50"
                  />
                </div>
              </div>
            </div>

            <div className="border-t border-outline-variant/40 pt-4 flex flex-col gap-2.5">
              <span className="text-[10px] text-secondary font-bold uppercase tracking-wider">Metrics</span>
              
              <div className="grid grid-cols-2 gap-2">
                <div className="border border-outline-variant/40 bg-surface/40 p-2">
                  <div className="text-[9px] text-on-surface-variant">SYS.LATENCY</div>
                  <div className="text-sm font-bold text-on-surface mt-0.5">180ms</div>
                </div>
                <div className="border border-outline-variant/40 bg-surface/40 p-2">
                  <div className="text-[9px] text-on-surface-variant">INTEGRITY</div>
                  <div className="text-sm font-bold text-emerald-400 mt-0.5">100%</div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="border border-outline-variant/40 bg-surface/40 p-2">
                  <div className="text-[9px] text-on-surface-variant">RESOURCES</div>
                  <div className="text-sm font-bold text-on-surface mt-0.5">14/14</div>
                </div>
                <div className="border border-outline-variant/40 bg-surface/40 p-2">
                  <div className="text-[9px] text-on-surface-variant">COST_EFF</div>
                  <div className="text-sm font-bold text-primary mt-0.5">optimal</div>
                </div>
              </div>
            </div>

            {/* Action Trigger button */}
            <button
              onClick={startCompilation}
              disabled={compiling}
              className="mt-auto w-full border border-primary bg-primary/10 py-2 font-bold uppercase tracking-wider text-primary hover:bg-primary hover:text-surface transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed text-[10px] flex items-center justify-center gap-2"
            >
              {compiling ? (
                <>
                  <span className="h-2 w-2 bg-primary animate-ping rounded-full" />
                  COMPILING STRATEGY...
                </>
              ) : (
                "RUN_COMPILER.SH"
              )}
            </button>
          </div>

          {/* Right panel - Terminal logs stream (8 cols) */}
          <div className="md:col-span-8 p-4 flex flex-col gap-3">
            {/* Quickstart bash line */}
            <div className="flex items-center justify-between border border-outline-variant/40 bg-surface/50 p-2 text-[11px] select-all">
              <div className="flex items-center gap-1.5 overflow-hidden">
                <span className="text-primary font-bold">$</span>
                <span className="truncate text-on-surface-variant">{command}</span>
              </div>
              <button 
                onClick={handleCopy}
                className="text-secondary hover:text-primary transition-colors px-1 text-[10px] font-bold uppercase shrink-0"
              >
                {copied ? "COPIED" : "COPY"}
              </button>
            </div>

            {/* Console output display */}
            <div className="flex-1 bg-surface-dim border border-outline-variant/40 p-3 h-64 overflow-y-auto flex flex-col gap-1.5 text-[11px] leading-relaxed">
              {compiling && (
                <div className="mb-2">
                  <div className="flex justify-between items-center text-[10px] text-on-surface-variant mb-1">
                    <span>BUILD PROGRESS</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full bg-outline-variant/20 h-1 overflow-hidden">
                    <div className="bg-primary h-full transition-all duration-100" style={{ width: `${progress}%` }} />
                  </div>
                </div>
              )}
              
              {logs.map((log, index) => {
                let colorClass = "text-on-surface-variant";
                if (log.startsWith("SYS:")) colorClass = "text-secondary";
                if (log.startsWith("SUCCESS:")) colorClass = "text-emerald-400 font-semibold";
                if (log.startsWith("INGEST:")) colorClass = "text-primary/95";
                
                return (
                  <div key={index} className={`${colorClass} flex gap-2 items-start font-mono`}>
                    <span className="text-outline-variant/60 select-none">{(index + 1).toString().padStart(2, "0")}</span>
                    <span>{log}</span>
                  </div>
                );
              })}

              {!compiling && logs.length === 0 && (
                <div className="text-on-surface-variant italic py-8 text-center select-none">
                  Console idle. Run compiler to generate marketing blueprints.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
