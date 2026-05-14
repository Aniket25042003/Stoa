"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/lib/api";
import { consumeSse } from "@/app/(app)/runs/[id]/stream";

type Msg = { id: string; role: string; content: string; agent?: string | null; created_at?: string };
type Artifact = { id: string; kind: string; title: string; storage_path?: string | null; mime_type?: string | null };

export function MarketingChat({
  chatId,
  companyId: _companyId,
  accessToken,
}: {
  chatId: string;
  companyId: string;
  accessToken: string;
}) {
  void _companyId;
  const [messages, setMessages] = useState<Msg[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [events, setEvents] = useState<string[]>([]);
  const acRef = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    const res = await apiFetch(`/v1/chats/${chatId}`, { accessToken });
    if (!res.ok) return;
    const body = await res.json();
    setMessages(body.messages ?? []);
    setArtifacts(body.artifacts ?? []);
  }, [chatId, accessToken]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setBusy(true);
    setInput("");
    setEvents([]);
    try {
      const res = await apiFetch(`/v1/chats/${chatId}/messages`, {
        method: "POST",
        accessToken,
        body: JSON.stringify({ content: text }),
      });
      if (!res.ok) throw new Error(await res.text());
      await refresh();
      const base = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
      if (!base) return;
      acRef.current?.abort();
      acRef.current = new AbortController();
      const url = `${base}/v1/chats/${chatId}/events`;
      await consumeSse(
        url,
        accessToken,
        (data) => {
          const m = typeof data.message === "string" ? data.message : JSON.stringify(data);
          setEvents((prev) => [...prev.slice(-40), `${data.agent || "?"}: ${m}`]);
          if (m === "Pipeline completed") void refresh();
        },
        acRef.current.signal
      );
      await refresh();
    } catch (e) {
      setEvents((p) => [...p, String(e)]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2 space-y-4 rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-5">
        <div className="max-h-[480px] space-y-3 overflow-y-auto pr-1">
          {messages.map((m) => (
            <div
              key={m.id}
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
            </div>
          ))}
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
        <div className="rounded-3xl border border-outline-variant/50 bg-surface-container-low/80 p-4">
          <h3 className="font-display text-sm font-bold text-on-surface">Activity</h3>
          <ul className="mt-2 max-h-40 overflow-y-auto font-mono text-[10px] text-on-surface-variant">
            {events.map((e, i) => (
              <li key={i}>{e}</li>
            ))}
          </ul>
        </div>
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
                        const r = await apiFetch(`/v1/artifacts/${a.id}/signed-url`, { accessToken });
                        if (r.ok) {
                          const b = await r.json();
                          if (b.url) window.open(b.url, "_blank", "noopener,noreferrer");
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
