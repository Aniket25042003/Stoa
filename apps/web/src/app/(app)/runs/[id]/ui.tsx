"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ACTIVITY_MESSAGES, type ActivityPhase } from "@/lib/activity-messages";
import { StatusPill } from "@/components/app-shell/StatusPill";
import { consumeSse } from "./stream";

type EventRow = { message?: string; agent?: string; phase?: string; detail?: Record<string, unknown> };
type RunRow = { status?: string; master_plan?: Record<string, unknown> };
type SourceRow = {
  id: string;
  source_type: string;
  source_url?: string | null;
  title?: string | null;
  excerpt?: string | null;
  metadata?: Record<string, unknown>;
};

function activityPhase(status: string, events: EventRow[]): ActivityPhase {
  if (status === "awaiting_plan_approval") return "awaiting_plan_approval";
  if (status === "completed") return "completed";
  if (status === "failed") return "failed";
  const latestPhase = events.at(-1)?.phase;
  if (latestPhase === "planning" || latestPhase === "research" || latestPhase === "reasoning" || latestPhase === "writing") {
    return latestPhase;
  }
  if (status === "queued") return "queued";
  return "research";
}

const card = "rounded-3xl p-5 shadow-soft card-glass md:p-6";
const btn = "btn-secondary px-4 py-2 text-sm disabled:opacity-50";
const btnPrimary = "btn-primary px-4 py-2 text-sm disabled:opacity-50";
const codePanel = "rounded-2xl border border-outline-variant/55 bg-slate-deep p-4 font-mono text-xs leading-6 text-white/78";

export function RunDetail({ runId, accessToken }: { runId: string; accessToken: string }) {
  const [status, setStatus] = useState<string>("...");
  const [events, setEvents] = useState<EventRow[]>([]);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);
  const [masterPlan, setMasterPlan] = useState<Record<string, unknown> | null>(null);
  const [planFeedback, setPlanFeedback] = useState("");
  const [planBusy, setPlanBusy] = useState(false);
  const [activityIndex, setActivityIndex] = useState(0);
  const currentActivityPhase = activityPhase(status, events);
  const currentActivityMessages = ACTIVITY_MESSAGES[currentActivityPhase];
  const currentActivity = currentActivityMessages[activityIndex % currentActivityMessages.length];
  const latestEvent = events.at(-1);
  const pollInFlight = useRef(false);

  const refreshSnapshot = useCallback(
    async (includeArtifacts = true) => {
      const requests = includeArtifacts
        ? Promise.all([
            apiFetch(`/v1/runs/${runId}`, { accessToken }),
            apiFetch(`/v1/runs/${runId}/report`, { accessToken }),
            apiFetch(`/v1/runs/${runId}/sources`, { accessToken }),
          ])
        : Promise.all([apiFetch(`/v1/runs/${runId}`, { accessToken })]);

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
    [runId, accessToken]
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
    const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
    if (status === "..." || status === "awaiting_plan_approval") return;
    if (!base) return;
    const ac = new AbortController();
    const url = `${base}/v1/runs/${runId}/events`;
    void (async () => {
      try {
        await consumeSse(
          url,
          accessToken,
          (data) => {
            setEvents((prev) => [...prev, data as EventRow]);
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
  }, [runId, accessToken, status]);

  useEffect(() => {
    if (status === "..." || status === "awaiting_plan_approval") return;
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
    if (status !== "queued" && status !== "running") {
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
    const res = await apiFetch(`/v1/runs/${runId}/report.pdf`, { accessToken });
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
        accessToken,
        body: JSON.stringify({ feedback: planFeedback }),
      });
      if (res.ok) {
        const body = await res.json();
        setMasterPlan(body.master_plan ?? null);
        setStatus(body.status ?? "awaiting_plan_approval");
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
        accessToken,
      });
      if (res.ok) {
        const body = await res.json();
        setStatus(body.status ?? "queued");
      }
    } finally {
      setPlanBusy(false);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-mono text-xs font-semibold uppercase tracking-[0.12em] text-on-surface-variant">Status</span>
        <StatusPill status={status} />
      </div>

      <section className={`${card} ai-insight-card`} aria-live="polite">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <p className="eyebrow text-[10px]">Current backend activity</p>
          <div className="h-1 w-28 overflow-hidden rounded-full bg-surface-container-high">
            <div className="h-full w-3/4 animate-shimmer rounded-full progress-shimmer" />
          </div>
        </div>
        <p className="mt-3 font-display text-xl font-bold tracking-[-0.02em] text-on-surface">{currentActivity}</p>
        {latestEvent ? (
          <p className="mt-3 font-mono text-xs text-on-surface-variant">
            Latest: [{latestEvent.phase ?? "system"}] {latestEvent.agent ?? "agent"} - {latestEvent.message ?? "Working"}
          </p>
        ) : (
          <p className="mt-3 text-sm text-on-surface-variant">Waiting for the first backend event.</p>
        )}
      </section>

      {status === "awaiting_plan_approval" && (
        <section className={card}>
          <h2 className="font-display text-2xl font-bold tracking-[-0.03em] text-on-surface">User approval required</h2>
          <p className="mt-3 text-sm leading-7 text-on-surface-variant">
            Review the main agent&apos;s master plan. You can request edits; the main agent will regenerate the plan before any layer starts.
          </p>
          <pre className={`mt-5 max-h-[360px] overflow-auto whitespace-pre-wrap ${codePanel}`}>{JSON.stringify(masterPlan, null, 2)}</pre>
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

      <section className={card}>
        <h2 className="font-display text-xl font-bold tracking-[-0.02em] text-on-surface">Live events</h2>
        <pre className={`mt-4 max-h-[280px] overflow-auto ${codePanel}`}>
          {events.map((e) => `[${e.phase ?? ""}] ${e.agent ?? ""}: ${e.message ?? JSON.stringify(e)}`).join("\n")}
        </pre>
      </section>

      <section className={card}>
        <h2 className="font-display text-xl font-bold tracking-[-0.02em] text-on-surface">Sources</h2>
        {sources.length === 0 ? (
          <p className="mt-3 text-sm text-on-surface-variant">No persisted research sources yet.</p>
        ) : (
          <div className="mt-5 space-y-3">
            {sources.map((s) => (
              <div key={s.id} className="rounded-2xl border border-outline-variant/55 bg-surface-container-low/75 p-5 backdrop-blur-md">
                <strong className="font-mono text-xs uppercase tracking-[0.12em] text-primary">{s.source_type}</strong>{" "}
                {s.source_url ? (
                  <a href={s.source_url} target="_blank" rel="noreferrer" className="font-semibold text-on-surface underline-offset-4 hover:text-primary hover:underline">
                    {s.title || s.source_url}
                  </a>
                ) : (
                  <span className="font-semibold text-on-surface">{s.title || "Untitled source"}</span>
                )}
                <p className="mt-2 text-sm leading-7 text-on-surface-variant">{s.excerpt}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className={card}>
        <h2 className="font-display text-xl font-bold tracking-[-0.02em] text-on-surface">Report</h2>
        {markdown ? (
          <div className="mt-5 space-y-4">
            <button type="button" className={btnPrimary} onClick={() => void downloadPdf()}>
              Download PDF
            </button>
            <pre className={`whitespace-pre-wrap ${codePanel}`}>{markdown}</pre>
          </div>
        ) : (
          <p className="mt-3 text-sm text-on-surface-variant">Report will appear when the run completes...</p>
        )}
      </section>
    </div>
  );
}
