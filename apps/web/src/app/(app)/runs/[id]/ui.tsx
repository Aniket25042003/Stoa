"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { ACTIVITY_MESSAGES, PHASE_LABELS } from "@/lib/activity-messages";
import { StatusPill } from "@/components/app-shell/StatusPill";
import { ActivitySurface } from "@/components/motion/ActivitySurface";
import { CollapsibleDevLog } from "@/components/motion/CollapsibleDevLog";
import { PipelinePhaseVisualizer } from "@/components/motion/PipelinePhaseVisualizer";
import { StaggerInView } from "@/components/motion/StaggerInView";
import { formatDevLogLine, resolveActivityPhase, type EventRow } from "@/lib/pipeline-phases";
import { safeExternalHref } from "@/lib/safe-url";
import { consumeRunSse } from "./stream";

type RunRow = { status?: string; master_plan?: Record<string, unknown> };
type SourceRow = {
  id: string;
  source_type: string;
  source_url?: string | null;
  title?: string | null;
  excerpt?: string | null;
  metadata?: Record<string, unknown>;
};

const card = "rounded-3xl p-5 shadow-soft card-glass md:p-6";
const btn = "btn-secondary px-4 py-2 text-sm disabled:opacity-50";
const btnPrimary = "btn-primary px-4 py-2 text-sm disabled:opacity-50";
const codePanel = "rounded-2xl border border-outline-variant/55 bg-slate-deep p-4 font-mono text-xs leading-6 text-white/78";

export function RunDetail({ runId }: { runId: string }) {
  const [status, setStatus] = useState<string>("...");
  const [events, setEvents] = useState<EventRow[]>([]);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [masterPlan, setMasterPlan] = useState<Record<string, unknown> | null>(null);
  const [planFeedback, setPlanFeedback] = useState("");
  const [planBusy, setPlanBusy] = useState(false);
  const [planExpanded, setPlanExpanded] = useState(false);
  const [activityIndex, setActivityIndex] = useState(0);
  const reduce = useReducedMotion();
  const currentActivityPhase = resolveActivityPhase(status, events);
  const currentActivityMessages = ACTIVITY_MESSAGES[currentActivityPhase];
  const currentActivity = currentActivityMessages[activityIndex % currentActivityMessages.length];
  const phaseLabel = PHASE_LABELS[currentActivityPhase];
  const pollInFlight = useRef(false);
  const showPipeline =
    status !== "awaiting_plan_approval" && status !== "planning" && status !== "...";

  const refreshSnapshot = useCallback(
    async (includeArtifacts = true) => {
      const requests = includeArtifacts
        ? Promise.all([
            apiFetch(`/v1/runs/${runId}`),
            apiFetch(`/v1/runs/${runId}/report`),
            apiFetch(`/v1/runs/${runId}/sources`),
          ])
        : Promise.all([apiFetch(`/v1/runs/${runId}`)]);

      const [runRes, reportRes, sourcesRes] = await requests;

      if (runRes?.ok) {
        const body = await runRes.json();
        const run = body.run as RunRow | undefined;
        setStatus(run?.status ?? "?");
        setMasterPlan(run?.master_plan ?? null);
      }

      if (includeArtifacts && reportRes?.ok) {
        const body = await reportRes.json();
        setMarkdown(body.markdown ?? null);
      }

      if (includeArtifacts && sourcesRes?.ok) {
        const body = await sourcesRes.json();
        setSources(body.sources ?? []);
      }
    },
    [runId]
  );

  useEffect(() => {
    setActivityIndex(0);
  }, [currentActivityPhase]);

  useEffect(() => {
    if (status !== "queued" && status !== "running") return;
    const t = setInterval(() => setActivityIndex((i) => i + 1), 2200);
    return () => clearInterval(t);
  }, [status]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        await refreshSnapshot(true);
      } catch {
        if (!cancelled) {
          setStatus((prev) => prev);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refreshSnapshot]);

  useEffect(() => {
    if (status === "..." || status === "awaiting_plan_approval") return;
    const ac = new AbortController();
    void (async () => {
      try {
        await consumeRunSse(
          `/v1/runs/${runId}/events`,
          (data) => {
            setEvents((prev) => [...prev, data as EventRow]);
            if (data.message === "Master plan ready for approval") {
              setStatus((prev) => (prev === "planning" ? "awaiting_plan_approval" : prev));
              void refreshSnapshot(false);
            }
            if (data.message === "Pipeline completed") {
              setStatus("completed");
              ac.abort();
            }
            if (typeof data.message === "string" && data.message.startsWith("Failed")) {
              setStatus("failed");
            }
          },
          ac.signal
        );
      } catch {
        /* stream ended or network */
      }
    })();
    return () => ac.abort();
  }, [runId, status, refreshSnapshot]);

  useEffect(() => {
    if (status === "...") return;
    let cancelled = false;

    const tick = async () => {
      if (pollInFlight.current) return;
      pollInFlight.current = true;
      try {
        await refreshSnapshot(true);
      } catch {
        /* ignore transient polling failures */
      } finally {
        pollInFlight.current = false;
      }
    };

    void tick();
    if (status !== "planning" && status !== "queued" && status !== "running") {
      return () => {
        cancelled = true;
      };
    }

    const t = setInterval(() => {
      if (!cancelled) {
        void tick();
      }
    }, 15000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [status, refreshSnapshot]);

  async function downloadPdf() {
    const res = await apiFetch(`/v1/runs/${runId}/report.pdf`, { });
    if (!res.ok) return;
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `gtm-report-${runId}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function revisePlan() {
    if (!planFeedback.trim()) return;
    setPlanBusy(true);
    try {
      const res = await apiFetch(`/v1/runs/${runId}/plan/revise`, {
        method: "POST",
        body: JSON.stringify({ feedback: planFeedback }),
      });
      if (res.ok) {
        const body = await res.json();
        setMasterPlan(body.master_plan ?? null);
        setStatus(body.status ?? "planning");
        setPlanFeedback("");
      }
    } finally {
      setPlanBusy(false);
    }
  }

  async function approvePlan() {
    setPlanBusy(true);
    try {
      const res = await apiFetch(`/v1/runs/${runId}/plan/approve`, {
        method: "POST",
      });
      if (res.ok) {
        const body = await res.json();
        setStatus(body.status ?? "queued");
      }
    } finally {
      setPlanBusy(false);
    }
  }

  const devLogLines = events.map(formatDevLogLine);

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-variant">Status</span>
        <StatusPill status={status} />
      </div>

      <section className={`${card} ai-insight-card`} aria-live="polite">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="eyebrow text-[10px]">Current workspace activity</p>
          <div className="h-1 w-28 overflow-hidden rounded-full bg-surface-container-high">
            <div className="h-full w-3/4 animate-shimmer rounded-full progress-shimmer" />
          </div>
        </div>

        {showPipeline ? (
          <div className="mt-5">
            <PipelinePhaseVisualizer phase={currentActivityPhase} events={events} />
          </div>
        ) : null}

        <div className="mt-5">
          <ActivitySurface phase={currentActivityPhase} />
        </div>

        <p className="mt-5 font-display text-xl font-bold tracking-[-0.02em] text-on-surface">{currentActivity}</p>
        <p className="mt-2 text-sm text-on-surface-variant">{phaseLabel}</p>
      </section>

      {status === "planning" && (
        <section className={card}>
          <h2 className="font-display text-2xl font-bold tracking-[-0.03em] text-on-surface">Master plan is being drafted</h2>
          <p className="mt-3 text-sm leading-7 text-on-surface-variant">
            Your GTM plan is being prepared for approval. This page will update when the plan is ready.
          </p>
          <div className="mt-5">
            <ActivitySurface phase="planning" />
          </div>
        </section>
      )}

      {status === "awaiting_plan_approval" && (
        <section className={card}>
          <h2 className="font-display text-2xl font-bold tracking-[-0.03em] text-on-surface">User approval required</h2>
          <p className="mt-3 text-sm leading-7 text-on-surface-variant">
            Review the main agent&apos;s master plan. You can request edits; the main agent will regenerate the plan before any layer starts.
          </p>
          <button
            type="button"
            className="mt-5 text-sm font-semibold text-primary hover:underline"
            onClick={() => setPlanExpanded((v) => !v)}
            aria-expanded={planExpanded}
          >
            {planExpanded ? "Hide plan details" : "View plan details"}
          </button>
          <AnimatePresence initial={false}>
            {planExpanded ? (
              <motion.div
                initial={reduce ? false : { height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={reduce ? undefined : { height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <pre className={`mt-3 max-h-[360px] overflow-auto whitespace-pre-wrap ${codePanel}`}>
                  {JSON.stringify(masterPlan, null, 2)}
                </pre>
              </motion.div>
            ) : null}
          </AnimatePresence>
          <label htmlFor="plan-feedback" className="mt-5 block eyebrow text-[11px]">
            Plan edits or updates
          </label>
          <textarea
            id="plan-feedback"
            rows={5}
            value={planFeedback}
            onChange={(e) => setPlanFeedback(e.target.value)}
            placeholder="Example: focus more on SMB founders, skip deep crawl unless web search and competitor SERP are inconclusive..."
            className="mt-2 input-field px-3 py-3 text-sm"
          />
          <div className="mt-5 flex flex-wrap gap-3">
            <button type="button" className={btn} onClick={() => void revisePlan()} disabled={planBusy || !planFeedback.trim()}>
              Regenerate plan with edits
            </button>
            <button type="button" className={btnPrimary} onClick={() => void approvePlan()} disabled={planBusy || !masterPlan}>
              Approve plan and start agents
            </button>
          </div>
        </section>
      )}

      <CollapsibleDevLog lines={devLogLines} />

      <section className={card}>
        <h2 className="font-display text-xl font-bold tracking-[-0.02em] text-on-surface">Sources</h2>
        {sources.length === 0 ? (
          <p className="mt-3 text-sm text-on-surface-variant">No persisted research sources yet.</p>
        ) : (
          <div className="mt-5 space-y-3">
            {sources.map((s, i) => (
              <StaggerInView key={s.id} delay={i * 0.06}>
                <div className="rounded-2xl border border-outline-variant/55 bg-surface-container-low/75 p-5 backdrop-blur-md">
                  <strong className="font-mono text-xs uppercase tracking-[0.12em] text-primary">{s.source_type}</strong>{" "}
                  {safeExternalHref(s.source_url ?? "") ? (
                    <a
                      href={safeExternalHref(s.source_url ?? "")}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-on-surface underline-offset-4 hover:text-primary hover:underline"
                    >
                      {s.title || s.source_url}
                    </a>
                  ) : (
                    <span className="font-semibold text-on-surface">{s.title || "Untitled source"}</span>
                  )}
                  <p className="mt-2 text-sm leading-7 text-on-surface-variant">{s.excerpt}</p>
                </div>
              </StaggerInView>
            ))}
          </div>
        )}
      </section>

      <section className={card}>
        <h2 className="font-display text-xl font-bold tracking-[-0.02em] text-on-surface">Report</h2>
        <AnimatePresence mode="wait">
          {markdown ? (
            <motion.div
              key="report"
              initial={reduce ? false : { opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-5 space-y-4"
            >
              <button type="button" className={btnPrimary} onClick={() => void downloadPdf()}>
                Download PDF
              </button>
              <pre className={`whitespace-pre-wrap ${codePanel}`}>{markdown}</pre>
            </motion.div>
          ) : (
            <motion.p key="empty" className="mt-3 text-sm text-on-surface-variant">
              Report will appear when the run completes...
            </motion.p>
          )}
        </AnimatePresence>
      </section>
    </div>
  );
}
