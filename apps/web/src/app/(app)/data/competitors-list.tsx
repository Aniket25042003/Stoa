/**
 * @file apps/web/src/app/(app)/data/competitors-list.tsx
 * @layer Frontend Product UI
 * @description Implements competitors list behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { useState, type InputHTMLAttributes, type ReactNode } from "react";
import { useAppPermissions } from "@/components/app-shell/useAppPermissions";
import {
  ProductButton,
  ProductCard,
  ProductTable,
  ProductTableCell,
  ProductTableHead,
  ProductTableHeaderCell,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { Competitor } from "./data-hub-context";

type EditDraft = {
  name: string;
  website_url: string;
};

/**
 * Handles inline table input behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function InlineTableInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "m-0 box-border h-6 w-full max-w-full min-w-0 rounded-sm border border-mkt-border bg-mkt-surface-elevated/50 px-1 py-0 text-sm leading-5 text-mkt-ink shadow-none placeholder:text-mkt-muted/50 focus:border-mkt-accent/60 focus:outline-none focus:ring-0",
        className
      )}
      {...props}
    />
  );
}

/**
 * Handles cell text behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function CellText({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span className={cn("block min-w-0 truncate text-sm leading-5", className)}>{children}</span>
  );
}

/**
 * Handles data cell behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
function DataCell({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <ProductTableCell className={cn("max-w-0 overflow-hidden align-middle px-3 py-2.5", className)}>
      <div className="min-w-0 max-w-full">{children}</div>
    </ProductTableCell>
  );
}

export function CompetitorsList({
  competitors,
  onUpdated,
  onDeleted,
  onError,
}: {
  competitors: Competitor[];
  onUpdated: () => void;
  onDeleted: () => void;
  onError: (message: string) => void;
}) {
  const { permissions, loaded } = useAppPermissions();
  const canManage = loaded && permissions != null && permissions.includes("competitive:manage");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draft, setDraft] = useState<EditDraft>({ name: "", website_url: "" });
  const [savingId, setSavingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function startEdit(competitor: Competitor) {
    setEditingId(competitor.id);
    setDraft({
      name: competitor.name,
      website_url: competitor.website_url ?? "",
    });
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft({ name: "", website_url: "" });
  }

  async function saveEdit(competitorId: string) {
    const trimmedName = draft.name.trim();
    if (!trimmedName) {
      onError("Competitor name is required");
      return;
    }

    setSavingId(competitorId);
    const res = await apiFetch(`/v1/competitive/competitors/${competitorId}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: trimmedName,
        website_url: draft.website_url.trim() || null,
      }),
    });
    setSavingId(null);
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      onError(typeof body?.detail === "string" ? body.detail : "Could not update competitor");
      return;
    }
    cancelEdit();
    onUpdated();
  }

  async function deleteCompetitor(competitor: Competitor) {
    const confirmed = window.confirm(`Remove "${competitor.name}" from tracked competitors?`);
    if (!confirmed) return;

    setDeletingId(competitor.id);
    const res = await apiFetch(`/v1/competitive/competitors/${competitor.id}`, { method: "DELETE" });
    setDeletingId(null);
    if (!res.ok) {
      onError("Could not delete competitor");
      return;
    }
    if (editingId === competitor.id) cancelEdit();
    onDeleted();
  }

  return (
    <ProductCard>
      <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">Tracked competitors</h2>
      <p className="mt-1 text-sm text-mkt-muted">
        Update names and websites or remove competitors you no longer want to track.
      </p>

      {competitors.length === 0 ? (
        <p className="mt-4 text-sm text-mkt-muted">No competitors added yet.</p>
      ) : (
        <ProductTable className="mt-4 [&_table]:table-fixed">
          <colgroup>
            <col style={{ width: "28%" }} />
            <col style={{ width: "28%" }} />
            {canManage ? <col style={{ width: "44%" }} /> : null}
          </colgroup>
          <ProductTableHead>
            <ProductTableHeaderCell>Name</ProductTableHeaderCell>
            <ProductTableHeaderCell>Website</ProductTableHeaderCell>
            {canManage ? (
              <ProductTableHeaderCell>
                <span className="sr-only">Actions</span>
              </ProductTableHeaderCell>
            ) : null}
          </ProductTableHead>
          <tbody>
            {competitors.map((competitor) => {
              const isEditing = editingId === competitor.id;
              return (
                <tr key={competitor.id}>
                  <DataCell>
                    {isEditing ? (
                      <InlineTableInput
                        value={draft.name}
                        onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                        className="font-medium"
                        aria-label="Competitor name"
                        autoFocus
                      />
                    ) : (
                      <CellText className="font-medium text-mkt-ink">{competitor.name}</CellText>
                    )}
                  </DataCell>
                  <DataCell>
                    {isEditing ? (
                      <InlineTableInput
                        value={draft.website_url}
                        onChange={(e) => setDraft({ ...draft, website_url: e.target.value })}
                        className="text-mkt-muted"
                        placeholder="https://…"
                        aria-label="Website URL"
                      />
                    ) : (
                      <CellText className="text-mkt-muted">{competitor.website_url || "—"}</CellText>
                    )}
                  </DataCell>
                  {canManage ? (
                    <ProductTableCell className="w-[44%] whitespace-nowrap align-middle px-3 py-2.5">
                      <div className="flex justify-end gap-1.5">
                        {isEditing ? (
                          <>
                            <ProductButton
                              variant="secondary"
                              className="px-3 py-1.5 text-xs"
                              onClick={() => void saveEdit(competitor.id)}
                              disabled={savingId === competitor.id}
                            >
                              {savingId === competitor.id ? "Saving…" : "Save"}
                            </ProductButton>
                            <ProductButton
                              variant="ghost"
                              className="px-3 py-1.5 text-xs"
                              onClick={cancelEdit}
                              disabled={savingId === competitor.id}
                            >
                              Cancel
                            </ProductButton>
                          </>
                        ) : (
                          <>
                            <ProductButton
                              variant="secondary"
                              className="px-3 py-1.5 text-xs"
                              onClick={() => startEdit(competitor)}
                            >
                              Edit
                            </ProductButton>
                            <ProductButton
                              variant="ghost"
                              className="px-3 py-1.5 text-xs"
                              onClick={() => void deleteCompetitor(competitor)}
                              disabled={deletingId === competitor.id}
                            >
                              {deletingId === competitor.id ? "Deleting…" : "Delete"}
                            </ProductButton>
                          </>
                        )}
                      </div>
                    </ProductTableCell>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </ProductTable>
      )}
    </ProductCard>
  );
}
