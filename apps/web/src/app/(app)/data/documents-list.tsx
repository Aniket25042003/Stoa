/**
 * @file apps/web/src/app/(app)/data/documents-list.tsx
 * @layer Frontend Product UI
 * @description Implements documents list behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { productLabelClass } from "@/lib/product-typography";
import { useEffect, useState } from "react";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import {
  ProductButton,
  ProductCard,
  ProductInput,
  ProductSelect,
  ProductStatusPill,
  ProductTable,
  ProductTableCell,
  ProductTableHead,
  ProductTableHeaderCell,
  ProductTextarea,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import type { Document } from "./data-hub-context";

const DOC_TYPE_LABELS: Record<string, string> = {
  note: "Note",
  call_transcript: "Call transcript",
  review: "Review",
  crm_export: "CRM export",
};

const labelClass = productLabelClass;

type DocumentDetail = Document & {
  content?: string | null;
  storage_path?: string | null;
  source?: "paste" | "upload";
  editable?: boolean;
  updated_at?: string | null;
};

/**
 * Handles format doc type behavior for this part of the Stoa application.
 *
 * @param docType - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function formatDocType(docType: string) {
  return DOC_TYPE_LABELS[docType] ?? docType.replace(/_/g, " ");
}

/**
 * Handles format date behavior for this part of the Stoa application.
 *
 * @param value - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function DocumentViewerModal({
  document,
  canEdit,
  onClose,
  onSaved,
  onError,
}: {
  document: DocumentDetail;
  canEdit: boolean;
  onClose: () => void;
  onSaved: () => void;
  onError: (message: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [draftTitle, setDraftTitle] = useState(document.title);
  const [draftType, setDraftType] = useState(document.doc_type);
  const [draftContent, setDraftContent] = useState(document.content ?? "");

  useEffect(() => {
    setEditing(false);
    setDraftTitle(document.title);
    setDraftType(document.doc_type);
    setDraftContent(document.content ?? "");
  }, [document]);

  const isUploaded = document.source === "upload" || Boolean(document.storage_path);

  async function saveEdits() {
    setSaving(true);
    const res = await apiFetch(`/v1/intelligence/documents/${document.id}`, {
      method: "PATCH",
      body: JSON.stringify({
        title: draftTitle,
        content: draftContent,
        doc_type: draftType,
      }),
    });
    setSaving(false);
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      onError(typeof body?.detail === "string" ? body.detail : "Could not save document");
      return;
    }
    await res.json();
    setEditing(false);
    onSaved();
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-mkt-ink/40 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="document-viewer-title"
      onClick={onClose}
    >
      <ProductCard className="max-h-[85vh] w-full max-w-3xl overflow-hidden" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between gap-4 border-b border-mkt-ink/[0.06] pb-4">
          <div className="min-w-0 flex-1">
            {editing ? (
              <div className="space-y-3">
                <div>
                  <label className={labelClass}>Title</label>
                  <ProductInput value={draftTitle} onChange={(e) => setDraftTitle(e.target.value)} className="mt-1.5" />
                </div>
                <div>
                  <label className={labelClass}>Type</label>
                  <ProductSelect value={draftType} onChange={(e) => setDraftType(e.target.value)} className="mt-1.5">
                    <option value="note">Note</option>
                    <option value="call_transcript">Call transcript</option>
                    <option value="review">Review</option>
                    <option value="crm_export">CRM export</option>
                  </ProductSelect>
                </div>
              </div>
            ) : (
              <>
                <p className="text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                  {formatDocType(document.doc_type)}
                  {isUploaded ? " · File upload" : " · Pasted text"}
                </p>
                <h3
                  id="document-viewer-title"
                  className="mt-1 text-xl font-semibold tracking-tight text-mkt-ink"
                >
                  {document.title}
                </h3>
              </>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <ProductStatusPill status={document.status} />
              <span className="text-xs text-mkt-muted">Added {formatDate(document.created_at)}</span>
            </div>
          </div>
          <div className="flex shrink-0 gap-2">
            {canEdit && document.editable !== false && !isUploaded ? (
              editing ? (
                <>
                  <ProductButton variant="secondary" onClick={() => setEditing(false)} disabled={saving}>
                    Cancel
                  </ProductButton>
                  <ProductButton onClick={() => void saveEdits()} disabled={saving}>
                    {saving ? "Saving…" : "Save"}
                  </ProductButton>
                </>
              ) : (
                <ProductButton variant="secondary" onClick={() => setEditing(true)}>
                  Edit
                </ProductButton>
              )
            ) : null}
            {!editing ? (
              <ProductButton variant="ghost" onClick={onClose}>
                Close
              </ProductButton>
            ) : null}
          </div>
        </div>

        <div className="mt-4 max-h-[55vh] overflow-auto">
          {editing ? (
            <div>
              <label className={labelClass}>Content</label>
              <ProductTextarea
                value={draftContent}
                onChange={(e) => setDraftContent(e.target.value)}
                className="mt-1.5 min-h-[280px]"
              />
              <p className="mt-2 text-xs text-mkt-muted">
                Saving will re-process this document for intelligence signals.
              </p>
            </div>
          ) : document.content ? (
            <pre className="whitespace-pre-wrap text-sm leading-relaxed text-mkt-ink">{document.content}</pre>
          ) : isUploaded ? (
            <p className="text-sm text-mkt-muted">
              This document was uploaded as a file
              {document.storage_path ? (
                <>
                  {" "}
                  (
                  <code className="rounded-sm bg-mkt-ink/[0.04] px-1 py-0.5 font-mono text-xs">
                    {document.storage_path.split("/").pop()}
                  </code>
                  )
                </>
              ) : null}
              . Re-upload from the form above to replace it.
            </p>
          ) : (
            <p className="text-sm text-mkt-muted">No content available for this document.</p>
          )}
        </div>
      </ProductCard>
    </div>
  );
}

export function DocumentsList({
  documents,
  onDeleted,
  onUpdated,
  onError,
}: {
  documents: Document[];
  onDeleted: () => void;
  onUpdated: () => void;
  onError: (message: string) => void;
}) {
  const { permissions, loaded } = useAppPermissions();
  const canDelete = loaded && permissions != null && permissions.includes("documents:delete");
  const canEdit = loaded && permissions != null && permissions.includes("documents:write");
  const [viewing, setViewing] = useState<DocumentDetail | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function openDocument(documentId: string) {
    setLoadingId(documentId);
    const res = await apiFetch(`/v1/intelligence/documents/${documentId}`);
    setLoadingId(null);
    if (!res.ok) {
      onError("Could not load document");
      return;
    }
    const body = await res.json();
    setViewing(body.document as DocumentDetail);
  }

  async function deleteDocument(document: Document) {
    const confirmed = window.confirm(`Delete "${document.title}"? This cannot be undone.`);
    if (!confirmed) return;

    setDeletingId(document.id);
    const res = await apiFetch(`/v1/intelligence/documents/${document.id}`, { method: "DELETE" });
    setDeletingId(null);
    if (!res.ok) {
      onError("Could not delete document");
      return;
    }
    if (viewing?.id === document.id) setViewing(null);
    onDeleted();
  }

  return (
    <>
      <ProductCard>
        <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
          Uploaded documents
        </h2>
        <p className="mt-1 text-sm text-mkt-muted">
          View content or remove documents you no longer want in your knowledge base. Pasted documents can be edited
          in place.
        </p>

        {documents.length === 0 ? (
          <p className="mt-4 text-sm text-mkt-muted">No documents yet. Paste or upload one above.</p>
        ) : (
          <ProductTable className="mt-4">
            <ProductTableHead>
              <ProductTableHeaderCell>Title</ProductTableHeaderCell>
              <ProductTableHeaderCell>Type</ProductTableHeaderCell>
              <ProductTableHeaderCell>Status</ProductTableHeaderCell>
              <ProductTableHeaderCell>Added</ProductTableHeaderCell>
              <ProductTableHeaderCell>
                <span className="sr-only">Actions</span>
              </ProductTableHeaderCell>
            </ProductTableHead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <ProductTableCell className="font-medium">{doc.title}</ProductTableCell>
                  <ProductTableCell className="text-mkt-muted">{formatDocType(doc.doc_type)}</ProductTableCell>
                  <ProductTableCell>
                    <ProductStatusPill status={doc.status} />
                  </ProductTableCell>
                  <ProductTableCell className="text-mkt-muted">{formatDate(doc.created_at)}</ProductTableCell>
                  <ProductTableCell>
                    <div className="flex justify-end gap-2">
                      <ProductButton
                        variant="secondary"
                        onClick={() => void openDocument(doc.id)}
                        disabled={loadingId === doc.id}
                      >
                        {loadingId === doc.id ? "Loading…" : "View"}
                      </ProductButton>
                      {canDelete ? (
                        <ProductButton
                          variant="ghost"
                          onClick={() => void deleteDocument(doc)}
                          disabled={deletingId === doc.id}
                        >
                          {deletingId === doc.id ? "Deleting…" : "Delete"}
                        </ProductButton>
                      ) : null}
                    </div>
                  </ProductTableCell>
                </tr>
              ))}
            </tbody>
          </ProductTable>
        )}
      </ProductCard>

      {viewing ? (
        <DocumentViewerModal
          document={viewing}
          canEdit={canEdit}
          onClose={() => setViewing(null)}
          onSaved={onUpdated}
          onError={onError}
        />
      ) : null}
    </>
  );
}
