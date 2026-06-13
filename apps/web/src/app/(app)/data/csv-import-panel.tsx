"use client";

import { useState } from "react";
import { apiFetch } from "@/lib/api";

type Mapping = Record<string, string | null>;

export function CsvImportPanel({ onImported }: { onImported?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [content, setContent] = useState("");
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Mapping>({});
  const [title, setTitle] = useState("CRM CSV import");
  const [status, setStatus] = useState<string | null>(null);
  const [step, setStep] = useState<"upload" | "map" | "done">("upload");

  async function handleFile(f: File) {
    setFile(f);
    const text = await f.text();
    setContent(text);
    const res = await apiFetch("/v1/integrations/csv/detect", {
      method: "POST",
      body: JSON.stringify({ title: f.name, content: text }),
    });
    if (res.ok) {
      const body = await res.json();
      setHeaders(body.headers ?? []);
      setMapping(body.suggested_mapping ?? {});
      setStep("map");
    }
  }

  async function importCsv(e: React.FormEvent) {
    e.preventDefault();
    setStatus("Importing...");
    const res = await apiFetch("/v1/integrations/csv/import", {
      method: "POST",
      body: JSON.stringify({ title, content, column_mapping: mapping }),
    });
    if (!res.ok) {
      setStatus("Import failed");
      return;
    }
    setStatus("CSV imported — processing in background");
    setStep("done");
    onImported?.();
  }

  const mappingFields = [
    "email",
    "name",
    "title",
    "company",
    "domain",
    "industry",
    "deal_name",
    "deal_amount",
    "deal_stage",
    "won",
    "loss_reason",
    "transcript",
    "review",
  ];

  return (
    <div className="rounded-3xl p-6 card-glass space-y-4">
      <h2 className="font-display text-xl font-bold">Structured CSV import</h2>
      <p className="text-sm text-on-surface-variant">
        Upload a CRM export or customer list. We detect columns and map them to accounts, contacts, deals, and transcripts.
      </p>

      {step === "upload" ? (
        <input
          type="file"
          accept=".csv,text/csv"
          className="text-sm"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) void handleFile(f);
          }}
        />
      ) : null}

      {step === "map" ? (
        <form onSubmit={importCsv} className="space-y-3">
          <input
            className="w-full rounded-xl border border-outline-variant/60 bg-surface px-4 py-2 text-sm"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Import title"
          />
          {mappingFields.map((field) => (
            <label key={field} className="flex items-center gap-2 text-sm">
              <span className="w-32 shrink-0 text-on-surface-variant">{field}</span>
              <select
                className="flex-1 rounded-xl border border-outline-variant/60 bg-surface px-3 py-2 text-sm"
                value={mapping[field] ?? ""}
                onChange={(e) => setMapping({ ...mapping, [field]: e.target.value || null })}
              >
                <option value="">— skip —</option>
                {headers.map((h) => (
                  <option key={h} value={h}>
                    {h}
                  </option>
                ))}
              </select>
            </label>
          ))}
          <button type="submit" className="btn-primary px-4 py-2 text-sm">
            Import {file?.name ?? "CSV"}
          </button>
        </form>
      ) : null}

      {status ? <p className="text-sm text-on-surface-variant">{status}</p> : null}
    </div>
  );
}
