"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { consumeRunSse } from "@/app/(app)/runs/[id]/stream";
import { safeExternalHref } from "@/lib/safe-url";
import { ActivitySurface } from "@/components/motion/ActivitySurface";
import { CollapsibleDevLog } from "@/components/motion/CollapsibleDevLog";
import { MarketingPhaseVisualizer } from "@/components/motion/MarketingPhaseVisualizer";
import {
  formatMarketingDevLog,
  MARKETING_STATUS_MESSAGES,
  resolveMarketingStep,
  type MarketingEventPayload,
} from "@/lib/marketing-activity-phases";

type Msg = { id: string; role: string; content: string; agent?: string | null; created_at?: string };
type Artifact = { id: string; kind: string; title: string; storage_path?: string | null; mime_type?: string | null };

export function MarketingChat({
  chatId,
  companyId: _companyId,
}: {
  chatId: string;
  companyId: string;
}) {
  void _companyId;
  const [messages, setMessages] = useState<Msg[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [rawEvents, setRawEvents] = useState<MarketingEventPayload[]>([]);
  const acRef = useRef<AbortController | null>(null);
  const reduce = useReducedMotion();

  const activityStep = resolveMarketingStep(busy, rawEvents);
  const statusLine = MARKETING_STATUS_MESSAGES[activityStep];
  const devLogLines = rawEvents.map(formatMarketingDevLog);

  const surfacePhase = useMemo(() => {
    if (activityStep === "review") return "reasoning" as const;
    if (activityStep === "create") return "writing" as const;
    if (activityStep === "route") return "research" as const;
    if (activityStep === "done") return "completed" as const;
    if (activityStep === "failed") return "failed" as const;
    return "queued" as const;
  }, [activityStep]);

  const refresh = useCallback(async () => {
    const res = await apiFetch(`/v1/chats/${chatId}`);
    if (!res.ok) return;
    const body = await res.json();
    setMessages(body.messages ?? []);
    setArtifacts(body.artifacts ?? []);
  }, [chatId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    return () => {
      acRef.current?.abort();
    };
  }, []);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    setRawEvents([]);
    try {
      const res = await apiFetch(`/v1/chats/${chatId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content: text }),
      });
      if (!res.ok) throw new Error(await res.text());
      await refresh();
      acRef.current?.abort();
      acRef.current = new AbortController();
      await consumeRunSse(
        `/v1/chats/${chatId}/events`,
        (data) => {
          const payload = data as MarketingEventPayload;
          setRawEvents((prev) => [...prev.slice(-40), payload]);
          const m = typeof payload.message === "string" ? payload.message : "";
          if (m === "Pipeline completed") void refresh();
        },
        acRef.current.signal
      );
      await refresh();
    } catch (e) {
      setRawEvents((p) => [...p, { message: String(e) }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-4 rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-5">
        <div className="max-h-[480px] space-y-3 overflow-y-auto pr-1">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                layout={!reduce}
                initial={reduce ? false : { opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className={
                  m.role === "user"
                    ? "ml-8 rounded-2xl bg-primary/15 px-4 py-3 text-sm text-on-surface"
                    : "mr-8 rounded-2xl border border-outline-variant/40 bg-surface-container/90 px-4 py-3 text-sm text-on-surface"
                }
              >
                {m.role !== "user" ? (
                  <span className="mb-1 block font-mono text-[10px] uppercase tracking-wider text-primary">{m.agent || m.role}</span>
                ) : null}
                <div className="whitespace-pre-wrap">{m.content}</div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        <div className="flex gap-2">
          <textarea
            className="min-h-[88px] flex-1 rounded-2xl border border-outline-variant/50 bg-surface px-3 py-2 text-sm text-on-surface"
            placeholder="Ask for ad ideas, copy, scripts, or image concepts…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={busy}
          />
          <button type="button" className="btn-primary self-end px-4 py-2 text-sm disabled:opacity-50" disabled={busy} onClick={() => void send()}>
            Send
          </button>
        </div>
      </div>
      <div className="space-y-4">
        <div className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-4" aria-live="polite">
          <h3 className="font-display text-sm font-bold text-on-surface">Activity</h3>
          {busy || rawEvents.length > 0 ? (
            <>
              <div className="mt-3">
                <MarketingPhaseVisualizer step={activityStep} />
              </div>
              <div className="mt-3">
                <ActivitySurface phase={surfacePhase} compact />
              </div>
              <p className="mt-3 text-sm font-medium text-on-surface">{statusLine}</p>
            </>
          ) : (
            <p className="mt-2 text-sm text-on-surface-variant">{statusLine}</p>
          )}
        </div>
        <CollapsibleDevLog lines={devLogLines} title="Technical log" className="!p-4" />
        <div className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-4">
          <h3 className="font-display text-sm font-bold text-on-surface">Artifacts</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {artifacts.map((a) => (
              <li key={a.id} className="rounded-xl bg-surface-container/80 px-2 py-2">
                <span className="font-mono text-xs text-primary">{a.kind}</span> {a.title}
                {a.storage_path ? (
                  <a
                    className="mt-1 block text-xs text-primary hover:underline"
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      void (async () => {
                        const r = await apiFetch(`/v1/artifacts/${a.id}/signed-url`);
                        if (r.ok) {
                          const b = await r.json();
                          const href = safeExternalHref(String(b.url ?? ""));
                          if (href) window.open(href, "_blank", "noopener,noreferrer");
                        }
                      })();
                    }}
                  >
                    Open signed URL
                  </a>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
