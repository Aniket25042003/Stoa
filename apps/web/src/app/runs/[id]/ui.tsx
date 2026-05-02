"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
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

const ACTIVITY_MESSAGES = {
  planning: ["Reading your approved master plan", "Preparing the agent hierarchy", "Loading shared Redis context"],
  queued: ["Waiting for a worker to pick up the run", "Preparing the GTM pipeline", "Getting the agent team ready"],
  research: [
    "Researching Reddit discussions",
    "Checking X/Twitter market signals",
    "Searching the web for problem and competitor signals",
    "Looking for competitor positioning and pricing clues",
    "Reviewing sources before the research parent asks for approval",
  ],
  reasoning: [
    "Building ICP and persona hypotheses",
    "Synthesizing pain points from the research bundle",
    "Drafting positioning and messaging angles",
    "Ranking launch channels and experiment ideas",
    "Checking whether reasoning is strong enough for main-agent approval",
  ],
  writing: [
    "Drafting the GTM strategy document",
    "Turning research and reasoning into a clear narrative",
    "Adding citations and assumptions",
    "Reviewing the report for actionability",
    "Preparing the final Markdown and PDF-ready output",
  ],
  completed: ["Pipeline completed. The report is ready."],
  failed: ["The run failed. Check the latest event for details."],
  awaiting_plan_approval: ["Waiting for your approval before starting any agents."],
} as const;

type ActivityPhase = keyof typeof ACTIVITY_MESSAGES;

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
    (async () => {
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
    <div>
      <p>
        Status: <strong>{status}</strong>
      </p>
      <section className="card" aria-live="polite">
        <strong>Current backend activity</strong>
        <p style={{ marginBottom: "0.25rem" }}>{currentActivity}</p>
        {latestEvent ? (
          <p style={{ color: "var(--muted)", marginTop: 0 }}>
            Latest event: [{latestEvent.phase ?? "system"}] {latestEvent.agent ?? "agent"} - {latestEvent.message ?? "Working"}
          </p>
        ) : (
          <p style={{ color: "var(--muted)", marginTop: 0 }}>Waiting for the first backend event.</p>
        )}
      </section>
      {status === "awaiting_plan_approval" && (
        <section className="card">
          <h2>User approval required</h2>
          <p style={{ color: "var(--muted)" }}>
            Review the main agent&apos;s master plan. You can request edits; the main agent will regenerate the plan before any layer starts.
          </p>
          <pre style={{ maxHeight: 360, whiteSpace: "pre-wrap" }}>{JSON.stringify(masterPlan, null, 2)}</pre>
          <label htmlFor="plan-feedback">Plan edits or updates</label>
          <textarea
            id="plan-feedback"
            rows={5}
            value={planFeedback}
            onChange={(e) => setPlanFeedback(e.target.value)}
            placeholder="Example: focus more on SMB founders, skip X research unless Reddit and web are inconclusive, add competitor pricing analysis..."
          />
          <p>
            <button type="button" onClick={revisePlan} disabled={planBusy || !planFeedback.trim()}>
              Regenerate plan with edits
            </button>{" "}
            <button type="button" onClick={approvePlan} disabled={planBusy || !masterPlan}>
              Approve plan and start agents
            </button>
          </p>
        </section>
      )}
      <h2>Live events</h2>
      <pre style={{ maxHeight: 280 }}>
        {events
          .map((e) => `[${e.phase ?? ""}] ${e.agent ?? ""}: ${e.message ?? JSON.stringify(e)}`)
          .join("\n")}
      </pre>
      <h2>Sources</h2>
      {sources.length === 0 ? (
        <p style={{ color: "var(--muted)" }}>No persisted research sources yet.</p>
      ) : (
        <div>
          {sources.map((s) => (
            <div className="card" key={s.id}>
              <strong>{s.source_type}</strong>{" "}
              {s.source_url ? (
                <a href={s.source_url} target="_blank" rel="noreferrer">
                  {s.title || s.source_url}
                </a>
              ) : (
                <span>{s.title || "Untitled source"}</span>
              )}
              <p style={{ color: "var(--muted)" }}>{s.excerpt}</p>
            </div>
          ))}
        </div>
      )}
      <h2>Report</h2>
      {markdown ? (
        <>
          <p>
            <button type="button" onClick={downloadPdf}>
              Download PDF
            </button>
          </p>
          <pre style={{ whiteSpace: "pre-wrap" }}>{markdown}</pre>
        </>
      ) : (
        <p style={{ color: "var(--muted)" }}>Report will appear when the run completes…</p>
      )}
    </div>
  );
}
