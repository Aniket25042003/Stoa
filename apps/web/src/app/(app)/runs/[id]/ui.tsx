"use client";

import { useEffect, useState } from "react";
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

const card = "rounded-2xl border border-mist bg-cream/95 p-5 shadow-sm md:p-6";
const btn =
  "rounded-lg border border-mist bg-cream px-4 py-2 text-sm font-semibold text-ink transition-colors hover:border-slate/50 disabled:opacity-50";
const btnPrimary = "rounded-lg bg-slate px-4 py-2 text-sm font-semibold text-cream shadow-glow transition-opacity hover:opacity-90 disabled:opacity-50";

export function RunDetail({ runId, accessToken }: { runId: string; accessToken: string }) {
  const [status, setStatus] = useState<string>("…");
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
      const r = await apiFetch(`/v1/runs/${runId}`, { accessToken });
      if (r.ok) {
        const body = await r.json();
        if (!cancelled) {
          const run = body.run as RunRow | undefined;
          setStatus(run?.status ?? "?");
          setMasterPlan(run?.master_plan ?? null);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [runId, accessToken]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
    if (status === "…" || status === "awaiting_plan_approval") return;
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
    let cancelled = false;
    const t = setInterval(async () => {
      const [reportRes, sourcesRes, runRes] = await Promise.all([
        apiFetch(`/v1/runs/${runId}/report`, { accessToken }),
        apiFetch(`/v1/runs/${runId}/sources`, { accessToken }),
        apiFetch(`/v1/runs/${runId}`, { accessToken }),
      ]);
      if (reportRes.ok) {
        const body = await reportRes.json();
        if (body.markdown && !cancelled) {
          setMarkdown(body.markdown);
        }
      }
      if (sourcesRes.ok) {
        const body = await sourcesRes.json();
        if (!cancelled) setSources(body.sources ?? []);
      }
      if (runRes.ok) {
        const body = await runRes.json();
        if (!cancelled) {
          const run = body.run as RunRow | undefined;
          setStatus(run?.status ?? "?");
          setMasterPlan(run?.master_plan ?? null);
        }
      }
    }, 4000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, [runId, accessToken]);

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
        <span className="text-sm text-ink/70">Status</span>
        <StatusPill status={status} />
      </div>

      <section className={card} aria-live="polite">
        <p className="font-mono text-[10px] uppercase tracking-[0.25em] text-slate">Current backend activity</p>
        <p className="mt-2 text-base font-medium text-ink">{currentActivity}</p>
        {latestEvent ? (
          <p className="mt-2 font-mono text-xs text-ink/60">
            Latest: [{latestEvent.phase ?? "system"}] {latestEvent.agent ?? "agent"} — {latestEvent.message ?? "Working"}
          </p>
        ) : (
          <p className="mt-2 text-sm text-ink/55">Waiting for the first backend event.</p>
        )}
      </section>

      {status === "awaiting_plan_approval" && (
        <section className={card}>
          <h2 className="text-xl font-semibold text-ink">User approval required</h2>
          <p className="mt-2 text-sm text-ink/70">
            Review the main agent&apos;s master plan. You can request edits; the main agent will regenerate the plan before any layer starts.
          </p>
          <pre className="mt-4 max-h-[360px] overflow-auto rounded-xl border border-mist bg-cream p-4 font-mono text-xs text-ink/85 whitespace-pre-wrap">
            {JSON.stringify(masterPlan, null, 2)}
          </pre>
          <label htmlFor="plan-feedback" className="mt-4 block text-xs font-medium uppercase tracking-wide text-slate">
            Plan edits or updates
          </label>
          <textarea
            id="plan-feedback"
            rows={5}
            value={planFeedback}
            onChange={(e) => setPlanFeedback(e.target.value)}
            placeholder="Example: focus more on SMB founders, skip X research unless Reddit and web are inconclusive..."
            className="mt-2 w-full rounded-lg border border-mist bg-cream px-3 py-2.5 text-sm text-ink focus:border-slate focus:outline-none focus:ring-2 focus:ring-slate/25"
          />
          <div className="mt-4 flex flex-wrap gap-3">
            <button type="button" className={btn} onClick={() => void revisePlan()} disabled={planBusy || !planFeedback.trim()}>
              Regenerate plan with edits
            </button>
            <button type="button" className={btnPrimary} onClick={() => void approvePlan()} disabled={planBusy || !masterPlan}>
              Approve plan and start agents
            </button>
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-semibold text-ink">Live events</h2>
        <pre className="mt-3 max-h-[280px] overflow-auto rounded-xl border border-mist bg-cream p-4 font-mono text-xs text-ink/85">
          {events.map((e) => `[${e.phase ?? ""}] ${e.agent ?? ""}: ${e.message ?? JSON.stringify(e)}`).join("\n")}
        </pre>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-ink">Sources</h2>
        {sources.length === 0 ? (
          <p className="mt-2 text-sm text-ink/60">No persisted research sources yet.</p>
        ) : (
          <div className="mt-4 space-y-3">
            {sources.map((s) => (
              <div key={s.id} className={card}>
                <strong className="text-ink">{s.source_type}</strong>{" "}
                {s.source_url ? (
                  <a href={s.source_url} target="_blank" rel="noreferrer" className="text-slate underline-offset-2 hover:underline">
                    {s.title || s.source_url}
                  </a>
                ) : (
                  <span className="text-ink/80">{s.title || "Untitled source"}</span>
                )}
                <p className="mt-2 text-sm text-ink/65">{s.excerpt}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="text-lg font-semibold text-ink">Report</h2>
        {markdown ? (
          <div className="mt-4 space-y-4">
            <button type="button" className={btnPrimary} onClick={() => void downloadPdf()}>
              Download PDF
            </button>
            <pre className="whitespace-pre-wrap rounded-xl border border-mist bg-cream p-4 font-mono text-xs text-ink/85">{markdown}</pre>
          </div>
        ) : (
          <p className="mt-2 text-sm text-ink/60">Report will appear when the run completes…</p>
        )}
      </section>
    </div>
  );
}
