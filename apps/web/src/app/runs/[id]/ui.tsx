"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "./stream";

type EventRow = { message?: string; agent?: string; phase?: string; detail?: Record<string, unknown> };
type SourceRow = {
  id: string;
  source_type: string;
  source_url?: string | null;
  title?: string | null;
  excerpt?: string | null;
  metadata?: Record<string, unknown>;
};

export function RunDetail({ runId, accessToken }: { runId: string; accessToken: string }) {
  const [status, setStatus] = useState<string>("…");
  const [events, setEvents] = useState<EventRow[]>([]);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceRow[]>([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const r = await apiFetch(`/v1/runs/${runId}`, { accessToken });
      if (r.ok) {
        const body = await r.json();
        if (!cancelled) setStatus(body.run?.status ?? "?");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [runId, accessToken]);

  useEffect(() => {
    const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
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
  }, [runId, accessToken]);

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
        if (!cancelled) setStatus(body.run?.status ?? "?");
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

  return (
    <div>
      <p>
        Status: <strong>{status}</strong>
      </p>
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
