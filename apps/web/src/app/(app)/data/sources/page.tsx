"use client";

import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductSelect,
  ProductTextarea,
} from "@/components/product";
import { DocumentsList } from "../documents-list";
import { useDataHub } from "../data-hub-context";

const labelClass = "font-dm-sans text-[9px] font-bold uppercase tracking-[0.18em] text-mkt-muted";

export default function DataSourcesPage() {
  const { documents, sources, refresh, showToast } = useDataHub();
  const {
    pasteTitle,
    setPasteTitle,
    pasteContent,
    setPasteContent,
    pasteType,
    setPasteType,
    uploadTitle,
    setUploadTitle,
    uploadType,
    setUploadType,
    uploadFile,
    setUploadFile,
    handlePaste,
    handleUpload,
  } = sources;

  return (
    <div className="space-y-6">
      <ProductCard>
        <form onSubmit={(e) => void handlePaste(e)} className="space-y-4">
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Paste document</h2>
          <div>
            <label className={labelClass}>Title</label>
            <ProductInput value={pasteTitle} onChange={(e) => setPasteTitle(e.target.value)} required className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Type</label>
            <ProductSelect value={pasteType} onChange={(e) => setPasteType(e.target.value)} className="mt-1.5">
              <option value="note">Note</option>
              <option value="call_transcript">Call transcript</option>
              <option value="review">Review</option>
              <option value="crm_export">CRM export</option>
            </ProductSelect>
          </div>
          <div>
            <label className={labelClass}>Content</label>
            <ProductTextarea
              value={pasteContent}
              onChange={(e) => setPasteContent(e.target.value)}
              required
              className="mt-1.5 min-h-[140px]"
              placeholder="Paste content..."
            />
          </div>
          <ProductButton type="submit">Ingest document</ProductButton>
        </form>
      </ProductCard>

      <ProductCard>
        <form onSubmit={(e) => void handleUpload(e)} className="space-y-4">
          <h2 className="font-syne text-lg font-extrabold uppercase tracking-tight text-mkt-ink">Upload file</h2>
          <div>
            <label className={labelClass}>Title (optional)</label>
            <ProductInput value={uploadTitle} onChange={(e) => setUploadTitle(e.target.value)} className="mt-1.5" />
          </div>
          <div>
            <label className={labelClass}>Type</label>
            <ProductSelect value={uploadType} onChange={(e) => setUploadType(e.target.value)} className="mt-1.5">
              <option value="note">Note</option>
              <option value="call_transcript">Call transcript</option>
              <option value="review">Review</option>
              <option value="crm_export">CRM export</option>
            </ProductSelect>
          </div>
          <input
            type="file"
            accept=".txt,.csv,.md,.json"
            className="block font-dm-sans text-sm text-mkt-muted"
            onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
          />
          <ProductButton type="submit" variant="secondary" disabled={!uploadFile}>
            Upload file
          </ProductButton>
        </form>
      </ProductCard>

      <DocumentsList
        documents={documents}
        onDeleted={() => {
          showToast("Document removed");
          void refresh();
        }}
        onUpdated={() => {
          showToast("Document saved");
          void refresh();
        }}
        onError={(message) => showToast(message, "error")}
      />
    </div>
  );
}
