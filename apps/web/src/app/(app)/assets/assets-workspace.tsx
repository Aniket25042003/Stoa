"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  ProductButton,
  ProductCard,
  ProductPageHeader,
  ProductStatusPill,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { safeStoragePublicUrl } from "@/lib/storage-url";
import { cn } from "@/lib/cn";

type Campaign = {
  id: string;
  brief: string;
  status: string;
  assets?: Record<string, unknown>;
  created_at: string;
};

type ContentFile = {
  storage_path: string;
  public_url: string;
  mime_type: string;
};

type ContentAsset = {
  id: string;
  asset_type: "image" | "video";
  prompt: string;
  status: string;
  files: ContentFile[];
  created_at: string;
};

type FilterType = "all" | "campaigns" | "content";

type LibraryItem =
  | { kind: "campaign"; id: string; title: string; status: string; created_at: string; preview: string }
  | { kind: "content"; id: string; title: string; status: string; created_at: string; preview: string; asset_type: string };

export function AssetsWorkspace() {
  const searchParams = useSearchParams();
  const initialFilter = (searchParams.get("type") as FilterType) || "all";
  const [filter, setFilter] = useState<FilterType>(
    initialFilter === "campaigns" || initialFilter === "content" ? initialFilter : "all",
  );
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [contentAssets, setContentAssets] = useState<ContentAsset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const [campRes, contentRes] = await Promise.all([
      apiFetch("/v1/campaigns"),
      apiFetch("/v1/content"),
    ]);
    if (!campRes.ok && !contentRes.ok) {
      setLoadError("We couldn't load your assets right now. Please try again in a moment.");
      return;
    }
    setLoadError(null);
    if (campRes.ok) setCampaigns((await campRes.json()).campaigns ?? []);
    if (contentRes.ok) setContentAssets((await contentRes.json()).assets ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const items = useMemo((): LibraryItem[] => {
    const campaignItems: LibraryItem[] = campaigns.map((c) => ({
      kind: "campaign",
      id: c.id,
      title: c.brief.slice(0, 120) || "Campaign",
      status: c.status,
      created_at: c.created_at,
      preview: c.brief,
    }));
    const contentItems: LibraryItem[] = contentAssets.map((a) => ({
      kind: "content",
      id: a.id,
      title: a.prompt.slice(0, 120) || "Content asset",
      status: a.status,
      created_at: a.created_at,
      preview: a.prompt,
      asset_type: a.asset_type,
    }));
    if (filter === "campaigns") return campaignItems;
    if (filter === "content") return contentItems;
    return [...campaignItems, ...contentItems].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
  }, [campaigns, contentAssets, filter]);

  const selectedCampaign = campaigns.find((c) => c.id === selectedId);
  const selectedContent = contentAssets.find((a) => a.id === selectedId);

  return (
    <div className="space-y-6">
      <ProductPageHeader
        eyebrow="Library"
        title="Generated assets"
        lead="Review past campaign packages and content generations. Create new work through the GTM Agent."
        actions={
          <Link href="/agent?q=Create%20a%20new%20campaign%20brief%20for%20our%20next%20launch">
            <ProductButton>Generate via Agent</ProductButton>
          </Link>
        }
      />

      {loadError ? <p className="text-sm text-red-600">{loadError}</p> : null}

      <div className="flex gap-2">
        {(["all", "campaigns", "content"] as const).map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setFilter(tab)}
            className={cn(
              "rounded-sm border px-3 py-1.5 text-xs font-medium capitalize transition-colors",
              filter === tab
                ? "border-mkt-accent bg-mkt-accent/[0.08] text-mkt-accent"
                : "border-mkt-ink/[0.08] text-mkt-muted hover:text-mkt-ink",
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <ProductCard className="divide-y divide-mkt-ink/[0.06] p-0">
          {items.length === 0 ? (
            <p className="p-6 text-sm text-mkt-muted">No assets yet. Ask the agent to generate campaigns or content.</p>
          ) : (
            items.map((item) => (
              <button
                key={`${item.kind}-${item.id}`}
                type="button"
                onClick={() => setSelectedId(item.id)}
                className={cn(
                  "w-full px-4 py-4 text-left transition-colors hover:bg-mkt-ink/[0.02]",
                  selectedId === item.id && "bg-mkt-accent/[0.04]",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-[10px] font-medium uppercase tracking-wider text-mkt-subtle">
                      {item.kind === "campaign" ? "Campaign" : item.asset_type}
                    </p>
                    <p className="mt-1 line-clamp-2 text-sm font-medium text-mkt-ink">{item.title}</p>
                    <p className="mt-1 text-xs text-mkt-muted">
                      {new Date(item.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <ProductStatusPill status={item.status} />
                </div>
              </button>
            ))
          )}
        </ProductCard>

        <ProductCard className="min-h-[320px] p-6">
          {selectedCampaign ? (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-mkt-ink">Campaign package</h2>
              <p className="text-sm text-mkt-muted">{selectedCampaign.brief}</p>
              <ProductStatusPill status={selectedCampaign.status} />
              {selectedCampaign.assets && Object.keys(selectedCampaign.assets).length > 0 ? (
                <pre className="max-h-96 overflow-auto rounded-sm border border-mkt-ink/[0.06] bg-mkt-ink/[0.02] p-4 text-xs text-mkt-ink">
                  {JSON.stringify(selectedCampaign.assets, null, 2)}
                </pre>
              ) : (
                <p className="text-sm text-mkt-muted">Assets will appear when generation completes.</p>
              )}
            </div>
          ) : selectedContent ? (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold text-mkt-ink">Content asset</h2>
              <p className="text-sm text-mkt-muted">{selectedContent.prompt}</p>
              <ProductStatusPill status={selectedContent.status} />
              {selectedContent.files?.length ? (
                <div className="grid gap-3 sm:grid-cols-2">
                  {selectedContent.files.map((file) => {
                    const url = safeStoragePublicUrl(file.public_url);
                    if (!url) return null;
                    return (
                    <a
                      key={file.storage_path}
                      href={url}
                      target="_blank"
                      rel="noreferrer"
                      className="block overflow-hidden rounded-sm border border-mkt-ink/[0.06]"
                    >
                      {file.mime_type.startsWith("image/") ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={url} alt="" className="h-40 w-full object-cover" />
                      ) : (
                        <div className="flex h-40 items-center justify-center text-xs text-mkt-muted">Video</div>
                      )}
                    </a>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-mkt-muted">Files will appear when generation completes.</p>
              )}
            </div>
          ) : (
            <p className="text-sm text-mkt-muted">Select an asset to view details.</p>
          )}
        </ProductCard>
      </div>
    </div>
  );
}
