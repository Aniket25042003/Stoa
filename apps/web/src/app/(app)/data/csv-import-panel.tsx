"use client";

import { useMemo, useState } from "react";
import { apiFetch } from "@/lib/api";
import { ProductButton, ProductCard, ProductInput, ProductSelect } from "@/components/product";
import { useDataHub } from "./data-hub-context";

type Mapping = Record<string, string | null>;

type CsvField = {
  key: string;
  label: string;
  group: string;
};

const FALLBACK_FIELDS: CsvField[] = [
  { key: "email", label: "Email address", group: "Contact" },
  { key: "name", label: "Contact name", group: "Contact" },
  { key: "title", label: "Job title", group: "Contact" },
  { key: "company", label: "Company name", group: "Company" },
  { key: "domain", label: "Company domain", group: "Company" },
  { key: "industry", label: "Industry", group: "Company" },
  { key: "deal_name", label: "Deal name", group: "Deal" },
  { key: "deal_amount", label: "Deal amount", group: "Deal" },
  { key: "deal_stage", label: "Deal stage", group: "Deal" },
  { key: "won", label: "Won / lost", group: "Deal" },
  { key: "loss_reason", label: "Loss reason", group: "Deal" },
  { key: "transcript", label: "Call transcript", group: "Content" },
  { key: "review", label: "Customer review", group: "Content" },
];

function resetFileInput() {
  const input = document.getElementById("csv-import-file") as HTMLInputElement | null;
  if (input) input.value = "";
}

export function CsvImportPanel({ onImported }: { onImported?: () => void }) {
  const { showToast } = useDataHub();
  const [file, setFile] = useState<File | null>(null);
  const [content, setContent] = useState("");
  const [headers, setHeaders] = useState<string[]>([]);
  const [mapping, setMapping] = useState<Mapping>({});
  const [fields, setFields] = useState<CsvField[]>(FALLBACK_FIELDS);
  const [title, setTitle] = useState("CRM CSV import");
  const [step, setStep] = useState<"upload" | "map">("upload");
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);

  const groupedFields = useMemo(() => {
    const groups = new Map<string, CsvField[]>();
    for (const field of fields) {
      const list = groups.get(field.group) ?? [];
      list.push(field);
      groups.set(field.group, list);
    }
    return Array.from(groups.entries());
  }, [fields]);

  const detectedCount = useMemo(
    () => Object.values(mapping).filter((value) => Boolean(value)).length,
    [mapping]
  );

  function resetUpload() {
    setFile(null);
    setContent("");
    setHeaders([]);
    setMapping({});
    setTitle("CRM CSV import");
    setStep("upload");
    setLoading(false);
    setImporting(false);
    resetFileInput();
  }

  async function handleFile(f: File) {
    setLoading(true);
    setFile(f);
    setTitle(f.name.replace(/\.csv$/i, "") || "CRM CSV import");
    const text = await f.text();
    setContent(text);
    const res = await apiFetch("/v1/integrations/csv/detect", {
      method: "POST",
      body: JSON.stringify({ title: f.name, content: text }),
    });
    setLoading(false);
    if (!res.ok) {
      showToast("Could not read CSV columns", "error");
      resetUpload();
      return;
    }
    const body = await res.json();
    setHeaders(body.headers ?? []);
    setMapping(body.suggested_mapping ?? {});
    if (Array.isArray(body.fields) && body.fields.length > 0) {
      setFields(body.fields as CsvField[]);
    }
    if ((body.headers ?? []).length === 0) {
      showToast("This file has no column headers", "error");
      resetUpload();
      return;
    }
    setStep("map");
  }

  async function importCsv(e: React.FormEvent) {
    e.preventDefault();
    setImporting(true);
    const res = await apiFetch("/v1/integrations/csv/import", {
      method: "POST",
      body: JSON.stringify({ title, content, column_mapping: mapping }),
    });
    setImporting(false);
    if (!res.ok) {
      showToast("CSV import failed", "error");
      return;
    }
    showToast("CSV imported — view it under Sources & uploads");
    resetUpload();
    onImported?.();
  }

  return (
    <ProductCard className="space-y-4">
      <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Structured CSV import</h2>
      <p className="font-dm-sans text-sm text-mkt-muted">
        Upload a CRM export or customer list. We match your columns to contacts, companies, and deals. Imported CSVs also
        appear on Sources &amp; uploads as CRM exports.
      </p>

      {step === "upload" ? (
        <div className="space-y-2">
          <label
            htmlFor="csv-import-file"
            className="inline-flex cursor-pointer items-center justify-center rounded-sm border border-mkt-ink/10 bg-[#F8F6F2] px-4 py-2.5 font-dm-sans text-[10px] font-bold uppercase tracking-widest text-mkt-ink shadow-sm transition-all hover:border-mkt-accent/30 hover:text-mkt-accent"
          >
            {loading ? "Reading file…" : "Choose file"}
          </label>
          <input
            id="csv-import-file"
            type="file"
            accept=".csv,text/csv"
            className="sr-only"
            disabled={loading}
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) void handleFile(f);
            }}
          />
        </div>
      ) : null}

      {step === "map" && file ? (
        <form onSubmit={importCsv} className="space-y-4">
          <div className="rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4">
            <p className="font-dm-sans text-sm font-medium text-mkt-ink">{file.name}</p>
            <p className="mt-1 font-dm-sans text-xs text-mkt-muted">
              {headers.length} columns detected · {detectedCount} auto-matched
            </p>
            <p className="mt-2 font-dm-sans text-xs text-mkt-muted">
              Columns in file: {headers.join(", ")}
            </p>
          </div>

          <ProductInput value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Import title" />

          <div className="space-y-5">
            {groupedFields.map(([group, groupFields]) => (
              <div key={group} className="space-y-3">
                <p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-accent">{group}</p>
                {groupFields.map((field) => (
                  <label key={field.key} className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-3">
                    <span className="w-full shrink-0 font-dm-sans text-sm text-mkt-ink sm:w-40">{field.label}</span>
                    <ProductSelect
                      className="flex-1"
                      value={mapping[field.key] ?? ""}
                      onChange={(e) => setMapping({ ...mapping, [field.key]: e.target.value || null })}
                    >
                      <option value="">— skip —</option>
                      {headers.map((header) => (
                        <option key={header} value={header}>
                          {header}
                        </option>
                      ))}
                    </ProductSelect>
                  </label>
                ))}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <ProductButton type="submit" disabled={importing}>
              {importing ? "Importing…" : `Import ${file.name}`}
            </ProductButton>
            <ProductButton type="button" variant="secondary" disabled={importing} onClick={resetUpload}>
              Cancel
            </ProductButton>
          </div>
        </form>
      ) : null}
    </ProductCard>
  );
}
