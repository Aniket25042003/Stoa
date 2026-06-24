/**
 * @file apps/web/src/app/(app)/content/content-workspace.tsx
 * @layer Frontend Product UI
 * @description Implements the workspace interface for AI image and video asset generation.
 * @dependencies React, Lucide, BFF apiFetch
 */

"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Clapperboard,
  Download,
  Image as ImageIcon,
  Loader2,
  Play,
  Plus,
  Trash2,
  Video,
  X,
} from "lucide-react";
import { CompleteDataPrompt } from "@/components/app-shell/CompleteDataPrompt";
import {
  ProductButton,
  ProductCard,
  ProductPageHeader,
  ProductSelect,
  ProductStatusPill,
  ProductTextarea,
} from "@/components/product";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import { safeStoragePublicUrl } from "@/lib/storage-url";

type ContentFile = {
  storage_path: string;
  public_url: string;
  mime_type: string;
  width?: number;
  height?: number;
  duration_seconds?: number;
  size_bytes?: number;
};

type ContentAsset = {
  id: string;
  campaign_id: string | null;
  asset_type: "image" | "video";
  prompt: string;
  enriched_prompt: string | null;
  reference_asset_id: string | null;
  config: {
    aspect_ratio: string;
    number_of_images?: number;
    resolution?: string;
    use_fast_model?: boolean;
  };
  status: "queued" | "generating" | "completed" | "failed";
  error: string | null;
  files: ContentFile[];
  generation_metadata: {
    model_used?: string;
    generation_time_seconds?: number;
    kb_context_refs?: Array<{
      ref: string;
      kind: string;
      title: string;
    }>;
  };
  created_at: string;
};

type Campaign = {
  id: string;
  brief: string;
};

const ACTIVE_STATUSES = new Set(["queued", "generating"]);

function assetNeedsPolling(assets: ContentAsset[]) {
  return assets.some((a) => ACTIVE_STATUSES.has(a.status.toLowerCase()));
}

export function ContentWorkspace() {
  const [assets, setAssets] = useState<ContentAsset[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [filterType, setFilterType] = useState<"all" | "image" | "video">("all");
  
  // Form state
  const [prompt, setPrompt] = useState("");
  const [assetType, setAssetType] = useState<"image" | "video">("image");
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [numImages, setNumImages] = useState(1);
  const [resolution, setResolution] = useState("720p");
  const [useFastModel, setUseFastModel] = useState(true);
  const [campaignId, setCampaignId] = useState("");
  const [referenceAssetId, setReferenceAssetId] = useState<string | null>(null);

  // UI state
  const [selectedAsset, setSelectedAsset] = useState<ContentAsset | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [ready, setReady] = useState(true);
  const [missing, setMissing] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);

  // Sync aspect ratio when assetType changes
  useEffect(() => {
    if (assetType === "video" && aspectRatio !== "16:9" && aspectRatio !== "9:16") {
      setAspectRatio("16:9");
    }
  }, [assetType, aspectRatio]);

  const refresh = useCallback(async () => {
    const [assetsRes, campRes, orgRes] = await Promise.all([
      apiFetch("/v1/content", {}),
      apiFetch("/v1/campaigns", {}),
      apiFetch("/v1/orgs/me", {}),
    ]);

    if (!assetsRes.ok) {
      const body = await assetsRes.json().catch(() => null);
      setLoadError(
        typeof body?.detail === "string"
          ? body.detail
          : "Could not reach the API. Is the backend running?"
      );
      return;
    }
    
    setLoadError(null);
    setAssets((await assetsRes.json()).assets ?? []);
    
    if (campRes.ok) {
      setCampaigns((await campRes.json()).campaigns ?? []);
    }
    
    if (orgRes.ok) {
      const body = await orgRes.json();
      const c = body.completeness;
      setReady(c?.ready_for_campaigns ?? false);
      setMissing(c?.missing ?? []);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // Poll generating assets
  useEffect(() => {
    if (!assetNeedsPolling(assets)) return;
    const interval = setInterval(() => void refresh(), 5000);
    return () => clearInterval(interval);
  }, [assets, refresh]);

  // Update selected asset details if it was generating and now completed
  useEffect(() => {
    if (selectedAsset) {
      const updated = assets.find((a) => a.id === selectedAsset.id);
      if (updated && updated.status !== selectedAsset.status) {
        setSelectedAsset(updated);
      }
    }
  }, [assets, selectedAsset]);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!prompt.trim()) return;

    setSubmitting(true);
    setStatus(null);

    const configPayload = {
      aspect_ratio: aspectRatio,
      number_of_images: assetType === "image" ? numImages : undefined,
      resolution: assetType === "video" ? resolution : undefined,
      use_fast_model: useFastModel,
    };

    const res = await apiFetch("/v1/content", {
      method: "POST",
      body: JSON.stringify({
        prompt: prompt.trim(),
        asset_type: assetType,
        campaign_id: campaignId || null,
        reference_asset_id: referenceAssetId,
        config: configPayload,
      }),
    });

    setSubmitting(false);

    if (!res.ok) {
      const body = await res.json().catch(() => null);
      setStatus(body?.detail || "Failed to enqueue generation");
      return;
    }

    const body = await res.json();
    setPrompt("");
    setReferenceAssetId(null);
    setStatus(`${assetType === "image" ? "Image" : "Video"} generation queued!`);
    
    // Automatically select the new asset to track progress
    if (body.asset) {
      setSelectedAsset(body.asset);
    }
    
    void refresh();
  }

  async function handleDelete(assetId: string) {
    if (!confirm("Are you sure you want to delete this asset?")) return;
    
    const res = await apiFetch(`/v1/content/${assetId}`, {
      method: "DELETE",
    });

    if (res.ok) {
      if (selectedAsset?.id === assetId) {
        setSelectedAsset(null);
      }
      setStatus("Asset deleted successfully");
      void refresh();
    } else {
      setStatus("Failed to delete asset");
    }
  }

  const animateImage = (imageAsset: ContentAsset) => {
    setAssetType("video");
    setReferenceAssetId(imageAsset.id);
    setAspectRatio(imageAsset.config.aspect_ratio || "16:9");
    setPrompt(`Animate this image: ${imageAsset.prompt}`);
    
    // Scroll to form
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const filteredAssets = assets.filter((a) => {
    if (filterType === "all") return true;
    return a.asset_type === filterType;
  });

  const getReferenceImageFile = (refId: string | null) => {
    if (!refId) return null;
    const refAsset = assets.find((a) => a.id === refId);
    return safeStoragePublicUrl(refAsset?.files?.[0]?.public_url);
  };

  return (
    <div className="space-y-8">
      <ProductPageHeader
        eyebrow="Content studio"
        title="Content at Scale"
        lead="Generate context-aware visual assets grounded in your company's Knowledge Base, brand voice, and target ICPs."
      />

      {!ready ? (
        <CompleteDataPrompt
          title="Complete data profiles for grounded creative assets"
          message="Upload documents, competitor profiles, and brand guidelines in the Data hub. The model will enrich your brief using this context."
          missing={missing}
        />
      ) : null}

      {loadError ? (
        <ProductCard className="border-mkt-accent-warm/25 bg-mkt-accent-warm/[0.06]">
          <p className="text-sm text-mkt-ink">{loadError}</p>
          <p className="mt-2 text-xs text-mkt-muted">
            Start the API with <code className="font-mono">pnpm dev:api</code> (or your usual FastAPI command), then refresh this page.
          </p>
        </ProductCard>
      ) : null}

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Creator Panel */}
        <div className="lg:col-span-1 space-y-6">
          <ProductCard className="p-6 h-fit">
            <h2 className="text-lg font-semibold tracking-tight text-mkt-ink border-b border-mkt-ink/10 pb-3">
              Asset Creator
            </h2>
            
            <form onSubmit={handleCreate} className="space-y-6 mt-4">
              {/* Type Toggle */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-mkt-muted mb-2">
                  Asset Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setAssetType("image")}
                    className={cn(
                      "flex items-center justify-center gap-2 py-2 px-3 border text-xs font-semibold rounded-sm transition-colors",
                      assetType === "image"
                        ? "border-mkt-accent bg-mkt-accent/[0.06] text-mkt-accent"
                        : "border-mkt-ink/10 text-mkt-muted hover:border-mkt-accent/20"
                    )}
                  >
                    <ImageIcon className="h-4 w-4" />
                    Image
                  </button>
                  <button
                    type="button"
                    onClick={() => setAssetType("video")}
                    className={cn(
                      "flex items-center justify-center gap-2 py-2 px-3 border text-xs font-semibold rounded-sm transition-colors",
                      assetType === "video"
                        ? "border-mkt-accent bg-mkt-accent/[0.06] text-mkt-accent"
                        : "border-mkt-ink/10 text-mkt-muted hover:border-mkt-accent/20"
                    )}
                  >
                    <Video className="h-4 w-4" />
                    Video
                  </button>
                </div>
              </div>

              {/* Reference Image for Image-to-Video */}
              {referenceAssetId && (
                <div className="border border-mkt-accent/20 bg-mkt-accent/[0.02] rounded-sm p-3 space-y-2 relative">
                  <button
                    type="button"
                    onClick={() => setReferenceAssetId(null)}
                    className="absolute top-2 right-2 text-mkt-muted hover:text-mkt-ink transition-colors"
                  >
                    <X className="h-4 w-4" />
                  </button>
                  <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                    Reference Image Attached
                  </span>
                  <div className="flex gap-3 items-center">
                    {getReferenceImageFile(referenceAssetId) && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={getReferenceImageFile(referenceAssetId) || ""}
                        alt="Reference image preview"
                        className="h-12 w-12 object-cover rounded-sm border border-mkt-ink/10"
                      />
                    )}
                    <span className="text-xs text-mkt-ink font-medium truncate max-w-[150px]">
                      Animated sequence seed
                    </span>
                  </div>
                </div>
              )}

              {/* User Prompt */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-mkt-muted mb-2">
                  Creative Brief / Prompt
                </label>
                <ProductTextarea
                  className="min-h-[100px] text-sm"
                  placeholder={
                    assetType === "image"
                      ? "Describe the visual asset (e.g. 'A sleek B2B SaaS dashboard hero banner in deep obsidian and vibrant silver themes, showing abstract glowing graphs...')"
                      : "Describe the motion sequence (e.g. 'Slow cinematic camera pan around a high-tech modern office space with glowing abstract graphs on glass displays...')"
                  }
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  required
                />
              </div>

              {/* Aspect Ratio Selector */}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-mkt-muted mb-2">
                  Aspect Ratio
                </label>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  {assetType === "image" ? (
                    <>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("1:1")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "1:1" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        1:1 Square
                      </button>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("16:9")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "16:9" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        16:9 Landscape
                      </button>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("9:16")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "9:16" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        9:16 Portrait
                      </button>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("4:3")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "4:3" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        4:3 Standard
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("16:9")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "16:9" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        16:9 Landscape
                      </button>
                      <button
                        type="button"
                        onClick={() => setAspectRatio("9:16")}
                        className={cn(
                          "py-2 border rounded-sm text-center font-medium",
                          aspectRatio === "9:16" ? "border-mkt-accent bg-mkt-accent/[0.04]" : "border-mkt-ink/10 text-mkt-muted"
                        )}
                      >
                        9:16 Portrait
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Advanced Configurations */}
              <div className="border border-mkt-ink/5 bg-mkt-ink/[0.01] rounded-sm p-4 space-y-4">
                <span className="block text-xs font-bold uppercase tracking-wider text-mkt-muted border-b border-mkt-ink/5 pb-1">
                  Model & Quality Settings
                </span>
                
                {/* Cheaper model toggle */}
                <div className="flex items-center justify-between">
                  <div className="pr-2">
                    <span className="block text-xs font-semibold text-mkt-ink">Cheaper Model Tier</span>
                    <span className="block text-[10px] text-mkt-muted">Uses fast variant to reduce credits</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={useFastModel}
                    onChange={(e) => setUseFastModel(e.target.checked)}
                    className="h-4 w-4 rounded-sm border-mkt-ink/15 text-mkt-accent focus:ring-mkt-accent"
                  />
                </div>

                {/* Batch count / Resolution */}
                {assetType === "image" ? (
                  <div>
                    <label className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle mb-1">
                      Batch Count (Images to generate)
                    </label>
                    <ProductSelect
                      value={numImages.toString()}
                      onChange={(e) => setNumImages(parseInt(e.target.value))}
                    >
                      <option value="1">1 Asset Variant</option>
                      <option value="2">2 Asset Variants</option>
                      <option value="3">3 Asset Variants</option>
                      <option value="4">4 Asset Variants</option>
                    </ProductSelect>
                  </div>
                ) : (
                  <div>
                    <label className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle mb-1">
                      Video Resolution
                    </label>
                    <ProductSelect
                      value={resolution}
                      onChange={(e) => setResolution(e.target.value)}
                    >
                      <option value="720p">720p (Fast)</option>
                      <option value="1080p">1080p (HQ)</option>
                    </ProductSelect>
                  </div>
                )}

                {/* Campaign Link dropdown */}
                <div>
                  <label className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle mb-1">
                    Link to Campaign
                  </label>
                  <ProductSelect
                    value={campaignId}
                    onChange={(e) => setCampaignId(e.target.value)}
                  >
                    <option value="">No Campaign Link</option>
                    {campaigns.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.brief.slice(0, 40)}...
                      </option>
                    ))}
                  </ProductSelect>
                </div>
              </div>

              {/* Submit button */}
              <ProductButton
                type="submit"
                className="w-full flex items-center justify-center gap-2 py-3"
                disabled={submitting}
              >
                {submitting ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    Generate Creative Assets
                  </>
                )}
              </ProductButton>
            </form>
          </ProductCard>
          
          {status && (
            <p className="text-xs font-semibold text-mkt-accent bg-mkt-accent/[0.04] p-3 rounded-sm border border-mkt-accent/10">
              {status}
            </p>
          )}
        </div>

        {/* Media Library */}
        <div className="lg:col-span-2 space-y-6">
          <ProductCard className="p-6 h-full flex flex-col">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-mkt-ink/10 pb-4">
              <h2 className="text-lg font-semibold tracking-tight text-mkt-ink">
                Asset Library
              </h2>
              
              {/* Filter Tabs */}
              <div className="flex rounded-sm border border-mkt-ink/10 p-0.5 text-xs bg-mkt-ink/[0.02]">
                {(["all", "image", "video"] as const).map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setFilterType(tab)}
                    className={cn(
                      "py-1 px-3 rounded-sm font-semibold transition-colors uppercase tracking-wider text-[10px]",
                      filterType === tab
                        ? "bg-mkt-ink/15 text-mkt-ink"
                        : "text-mkt-muted hover:text-mkt-ink"
                    )}
                  >
                    {tab}s
                  </button>
                ))}
              </div>
            </div>

            {/* Gallery Grid */}
            <div className="flex-1 mt-6">
              {filteredAssets.length === 0 ? (
                <div className="py-24 text-center">
                  <ImageIcon className="h-10 w-10 text-mkt-muted/45 mx-auto mb-3" />
                  <p className="text-sm text-mkt-muted">
                    No visual assets found in library. Use the creator panel to generate images and videos.
                  </p>
                </div>
              ) : (
                <div className="grid gap-6 sm:grid-cols-2 md:grid-cols-3">
                  {filteredAssets.map((asset) => {
                    const isGenerating = ACTIVE_STATUSES.has(asset.status.toLowerCase());
                    const isFailed = asset.status === "failed";
                    const isComplete = asset.status === "completed";
                    const hasFiles = asset.files && asset.files.length > 0;
                    
                    return (
                      <div
                        key={asset.id}
                        onClick={() => setSelectedAsset(asset)}
                        className={cn(
                          "group cursor-pointer border border-mkt-ink/10 hover:border-mkt-accent/25 bg-mkt-ink/[0.01] hover:bg-mkt-ink/[0.02] rounded-sm overflow-hidden flex flex-col transition-all h-[240px] relative",
                          selectedAsset?.id === asset.id && "border-mkt-accent ring-1 ring-mkt-accent/20"
                        )}
                      >
                        {/* Media Preview / State */}
                        <div className="flex-1 bg-black flex items-center justify-center relative overflow-hidden h-[150px]">
                          {isGenerating && (
                            <div className="flex flex-col items-center gap-2 text-white">
                              <Loader2 className="h-8 w-8 animate-spin text-mkt-accent" />
                              <span className="text-[10px] tracking-widest font-mono uppercase text-mkt-accent">
                                Processing...
                              </span>
                            </div>
                          )}
                          
                          {isFailed && (
                            <div className="text-center p-4">
                              <X className="h-8 w-8 text-mkt-accent-warm mx-auto mb-2" />
                              <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                                Generation Failed
                              </span>
                            </div>
                          )}

                          {isComplete && hasFiles && (
                            <>
                              {asset.asset_type === "image" ? (
                                // eslint-disable-next-line @next/next/no-img-element
                                <img
                                  src={safeStoragePublicUrl(asset.files[0].public_url) ?? ""}
                                  alt={asset.prompt}
                                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                                />
                              ) : (
                                <div className="w-full h-full relative group">
                                  {/* Video element doesn't auto play in grid to save performance, but we show play indicator */}
                                  <div className="absolute inset-0 bg-black/35 flex items-center justify-center z-10 opacity-75 group-hover:opacity-100 transition-opacity">
                                    <div className="h-10 w-10 rounded-full border border-white/30 bg-black/60 flex items-center justify-center text-white">
                                      <Play className="h-4 w-4 fill-white ml-0.5" />
                                    </div>
                                  </div>
                                  <div className="w-full h-full bg-mkt-accent/10 flex items-center justify-center text-mkt-muted text-xs font-mono uppercase tracking-widest">
                                    <Clapperboard className="h-8 w-8 text-mkt-accent opacity-50" />
                                  </div>
                                </div>
                              )}
                            </>
                          )}
                          
                          {/* Asset Type Icon Badge */}
                          <div className="absolute top-2 left-2 z-20 bg-black/60 backdrop-blur-md rounded-sm p-1 border border-white/10 text-white">
                            {asset.asset_type === "image" ? (
                              <ImageIcon className="h-3 w-3" />
                            ) : (
                              <Video className="h-3 w-3" />
                            )}
                          </div>
                        </div>

                        {/* Text Details */}
                        <div className="p-3 text-xs flex flex-col justify-between gap-2 border-t border-mkt-ink/5 bg-white">
                          <p className="font-semibold text-mkt-ink line-clamp-2 leading-relaxed">
                            {asset.prompt}
                          </p>
                          <div className="flex justify-between items-center mt-1">
                            <span className="text-[10px] text-mkt-muted font-mono">
                              {new Date(asset.created_at).toLocaleDateString()}
                            </span>
                            <ProductStatusPill status={asset.status} />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </ProductCard>
        </div>
      </div>

      {/* Lightbox Detail Drawer */}
      {selectedAsset && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-mkt-ink/10 rounded-sm w-full max-w-4xl max-h-[90vh] flex flex-col md:flex-row overflow-hidden shadow-2xl relative">
            
            {/* Close Button */}
            <button
              type="button"
              onClick={() => setSelectedAsset(null)}
              className="absolute top-4 right-4 z-50 bg-black/50 hover:bg-black/80 rounded-full p-2 border border-white/10 text-white transition-colors"
            >
              <X className="h-5 w-5" />
            </button>

            {/* Visual Preview Frame */}
            <div className="flex-1 bg-black flex items-center justify-center min-h-[300px] md:min-h-0 md:h-[600px] relative">
              {ACTIVE_STATUSES.has(selectedAsset.status.toLowerCase()) && (
                <div className="flex flex-col items-center gap-3 text-white">
                  <Loader2 className="h-10 w-10 animate-spin text-mkt-accent" />
                  <span className="text-xs font-mono uppercase tracking-widest text-mkt-accent">
                    Generating creative asset...
                  </span>
                </div>
              )}
              
              {selectedAsset.status === "failed" && (
                <div className="text-center p-8 text-white max-w-md">
                  <X className="h-12 w-12 text-mkt-accent-warm mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-mkt-ink">
                    Generation Failed
                  </h3>
                  <p className="mt-2 text-xs text-white/60 font-mono overflow-auto max-h-[150px] border border-white/10 bg-white/5 p-3 rounded-sm leading-relaxed text-left">
                    {selectedAsset.error || "Unknown platform exception during generation."}
                  </p>
                </div>
              )}

              {selectedAsset.status === "completed" && selectedAsset.files && selectedAsset.files.length > 0 && (
                <>
                  {selectedAsset.asset_type === "image" ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={safeStoragePublicUrl(selectedAsset.files[0].public_url) ?? ""}
                      alt={selectedAsset.prompt}
                      className="max-w-full max-h-[550px] object-contain"
                    />
                  ) : (
                    <video
                      src={safeStoragePublicUrl(selectedAsset.files[0].public_url) ?? ""}
                      controls
                      autoPlay
                      loop
                      className="max-w-full max-h-[550px]"
                    />
                  )}
                </>
              )}
            </div>

            {/* Metadata / Details Panel */}
            <div className="w-full md:w-[350px] p-6 border-t md:border-t-0 md:border-l border-mkt-ink/10 flex flex-col justify-between max-h-[600px] overflow-y-auto bg-white">
              <div className="space-y-6">
                <div>
                  <div className="flex gap-2 items-center mb-1">
                    <span className="text-xs font-medium uppercase tracking-wider text-mkt-muted">
                      {selectedAsset.asset_type}
                    </span>
                    <ProductStatusPill status={selectedAsset.status} />
                  </div>
                  <h3 className="text-base font-semibold tracking-tight text-mkt-ink">
                    Creative Metadata
                  </h3>
                </div>

                {/* Brief */}
                <div className="space-y-1">
                  <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                    Original Brief
                  </span>
                  <p className="text-xs text-mkt-ink leading-relaxed font-medium">
                    {selectedAsset.prompt}
                  </p>
                </div>

                {/* Enriched Prompt */}
                {selectedAsset.enriched_prompt && (
                  <div className="space-y-1">
                    <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                      Enriched Grounding Prompt
                    </span>
                    <p className="text-[11px] text-mkt-muted leading-relaxed italic bg-mkt-ink/[0.02] border border-mkt-ink/5 p-3 rounded-sm">
                      {selectedAsset.enriched_prompt}
                    </p>
                  </div>
                )}

                {/* Model Info */}
                {selectedAsset.status === "completed" && (
                  <div className="grid grid-cols-2 gap-4 text-xs border-y border-mkt-ink/10 py-3">
                    <div>
                      <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                        AI Model
                      </span>
                      <span className="font-mono text-mkt-ink font-semibold mt-0.5 block truncate">
                        {selectedAsset.generation_metadata?.model_used || "unknown"}
                      </span>
                    </div>
                    <div>
                      <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                        Render Time
                      </span>
                      <span className="font-mono text-mkt-ink font-semibold mt-0.5 block">
                        {selectedAsset.generation_metadata?.generation_time_seconds
                          ? `${selectedAsset.generation_metadata.generation_time_seconds}s`
                          : "unknown"}
                      </span>
                    </div>
                  </div>
                )}

                {/* KB Citations References */}
                {selectedAsset.status === "completed" &&
                  selectedAsset.generation_metadata?.kb_context_refs &&
                  selectedAsset.generation_metadata.kb_context_refs.length > 0 && (
                    <div className="space-y-2">
                      <span className="block text-xs font-medium uppercase tracking-wider text-mkt-subtle">
                        Knowledge Grounding Citations
                      </span>
                      <div className="space-y-1 max-h-[120px] overflow-y-auto">
                        {selectedAsset.generation_metadata.kb_context_refs.map((ref, idx) => (
                          <div
                            key={idx}
                            className="text-[10px] border border-mkt-ink/5 bg-mkt-ink/[0.01] rounded-sm p-1.5 flex justify-between items-center gap-2"
                          >
                            <span className="font-semibold text-mkt-ink truncate max-w-[120px]">
                              {ref.title}
                            </span>
                            <span className="text-[8px] bg-mkt-ink/10 font-mono px-1 rounded-sm uppercase tracking-wider text-mkt-muted">
                              {ref.kind.replace("_", " ")}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
              </div>

              {/* Action buttons */}
              <div className="mt-8 pt-4 border-t border-mkt-ink/10 space-y-2">
                {selectedAsset.status === "completed" && selectedAsset.asset_type === "image" && (
                  <ProductButton
                    type="button"
                    onClick={() => {
                      animateImage(selectedAsset);
                      setSelectedAsset(null);
                    }}
                    className="w-full flex items-center justify-center gap-2 border border-mkt-accent bg-transparent text-mkt-accent hover:bg-mkt-accent/[0.04]"
                  >
                    <Video className="h-4 w-4" />
                    Animate (Image-to-Video)
                  </ProductButton>
                )}

                {selectedAsset.status === "completed" &&
                  selectedAsset.files &&
                  selectedAsset.files.length > 0 &&
                  safeStoragePublicUrl(selectedAsset.files[0].public_url) && (
                  <a
                    href={safeStoragePublicUrl(selectedAsset.files[0].public_url)!}
                    download={`stoa-asset-${selectedAsset.id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full py-2.5 rounded-sm bg-mkt-ink text-white hover:bg-mkt-ink/90 flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Download File
                  </a>
                )}

                <button
                  type="button"
                  onClick={() => handleDelete(selectedAsset.id)}
                  className="w-full py-2.5 rounded-sm border border-mkt-accent-warm bg-transparent text-mkt-accent-warm hover:bg-mkt-accent-warm/[0.04] flex items-center justify-center gap-2 text-xs font-semibold uppercase tracking-wider transition-colors"
                >
                  <Trash2 className="h-4 w-4" />
                  Delete Asset
                </button>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
}
