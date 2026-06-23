/**
 * @file apps/web/src/app/(app)/data/data-hub-context.tsx
 * @layer Frontend Product UI
 * @description Implements data hub context behavior for the frontend product ui.
 * @dependencies React, BFF apiFetch
 */
"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { apiFetch } from "@/lib/api";
import type { DataHubToastVariant } from "./data-hub-toast";

const TOAST_DURATION_MS = 4000;

export type Org = {
  id: string;
  name: string;
  website_url?: string | null;
  industry?: string | null;
  profile?: Record<string, string>;
};

export type Completeness = {
  percent: number;
  completed: number;
  total: number;
  missing: string[];
  checks: Record<string, boolean>;
};

export type Document = {
  id: string;
  title: string;
  doc_type: string;
  status: string;
  created_at?: string;
};
export type Competitor = { id: string; name: string; website_url?: string | null };

type DataHubContextValue = {
  org: Org | null;
  completeness: Completeness | null;
  documents: Document[];
  competitors: Competitor[];
  toast: { message: string; variant: DataHubToastVariant } | null;
  showToast: (message: string, variant?: DataHubToastVariant) => void;
  saving: boolean;
  refresh: () => Promise<void>;
  profile: {
    name: string;
    setName: (v: string) => void;
    websiteUrl: string;
    setWebsiteUrl: (v: string) => void;
    industry: string;
    setIndustry: (v: string) => void;
    targetCustomers: string;
    setTargetCustomers: (v: string) => void;
    businessModel: string;
    setBusinessModel: (v: string) => void;
    stage: string;
    setStage: (v: string) => void;
    goals: string;
    setGoals: (v: string) => void;
    brandVoice: string;
    setBrandVoice: (v: string) => void;
    competitorNotes: string;
    setCompetitorNotes: (v: string) => void;
    saveProfile: (e: React.FormEvent) => Promise<void>;
  };
  sources: {
    pasteTitle: string;
    setPasteTitle: (v: string) => void;
    pasteContent: string;
    setPasteContent: (v: string) => void;
    pasteType: string;
    setPasteType: (v: string) => void;
    uploadTitle: string;
    setUploadTitle: (v: string) => void;
    uploadType: string;
    setUploadType: (v: string) => void;
    uploadFile: File | null;
    setUploadFile: (v: File | null) => void;
    handlePaste: (e: React.FormEvent) => Promise<void>;
    handleUpload: (e: React.FormEvent) => Promise<void>;
  };
  competitorsForm: {
    compName: string;
    setCompName: (v: string) => void;
    compUrl: string;
    setCompUrl: (v: string) => void;
    handleAddCompetitor: (e: React.FormEvent) => Promise<void>;
  };
};

const DataHubContext = createContext<DataHubContextValue | null>(null);

/**
 * Handles data hub provider behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function DataHubProvider({ children }: { children: ReactNode }) {
  const [org, setOrg] = useState<Org | null>(null);
  const [completeness, setCompleteness] = useState<Completeness | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [competitors, setCompetitors] = useState<Competitor[]>([]);
  const [toast, setToast] = useState<{ message: string; variant: DataHubToastVariant } | null>(null);
  const [saving, setSaving] = useState(false);
  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((message: string, variant: DataHubToastVariant = "success") => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, variant });
    toastTimerRef.current = setTimeout(() => setToast(null), TOAST_DURATION_MS);
  }, []);

  useEffect(() => {
    return () => {
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  const [name, setName] = useState("");
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [industry, setIndustry] = useState("");
  const [targetCustomers, setTargetCustomers] = useState("");
  const [businessModel, setBusinessModel] = useState("");
  const [stage, setStage] = useState("");
  const [goals, setGoals] = useState("");
  const [brandVoice, setBrandVoice] = useState("");
  const [competitorNotes, setCompetitorNotes] = useState("");

  const [pasteTitle, setPasteTitle] = useState("");
  const [pasteContent, setPasteContent] = useState("");
  const [pasteType, setPasteType] = useState("note");
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadType, setUploadType] = useState("note");
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const [compName, setCompName] = useState("");
  const [compUrl, setCompUrl] = useState("");

  const refresh = useCallback(async () => {
    const [orgRes, docsRes, compRes] = await Promise.all([
      apiFetch("/v1/orgs/me"),
      apiFetch("/v1/intelligence/documents"),
      apiFetch("/v1/competitive/competitors"),
    ]);
    if (orgRes.ok) {
      const body = await orgRes.json();
      const o = body.org as Org;
      setOrg(o);
      setCompleteness(body.completeness);
      setName(o.name ?? "");
      setWebsiteUrl(o.website_url ?? "");
      setIndustry(o.industry ?? "");
      const p = o.profile ?? {};
      setTargetCustomers(p.target_customers ?? "");
      setBusinessModel(p.business_model ?? "");
      setStage(p.stage ?? "");
      setGoals(p.goals ?? "");
      setBrandVoice(p.brand_voice ?? "");
      setCompetitorNotes(p.known_competitors_notes ?? "");
    }
    if (docsRes.ok) setDocuments((await docsRes.json()).documents ?? []);
    if (compRes.ok) setCompetitors((await compRes.json()).competitors ?? []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const saveProfile = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      setSaving(true);
      const res = await apiFetch("/v1/orgs/me", {
        method: "PATCH",
        body: JSON.stringify({
          name,
          website_url: websiteUrl || null,
          industry: industry || null,
          profile: {
            target_customers: targetCustomers || null,
            business_model: businessModel || null,
            stage: stage || null,
            goals: goals || null,
            brand_voice: brandVoice || null,
            known_competitors_notes: competitorNotes || null,
          },
        }),
      });
      setSaving(false);
      if (!res.ok) {
        showToast("Could not save profile", "error");
        return;
      }
      showToast("Profile saved");
      void refresh();
    },
    [
      name,
      websiteUrl,
      industry,
      targetCustomers,
      businessModel,
      stage,
      goals,
      brandVoice,
      competitorNotes,
      showToast,
      refresh,
    ]
  );

  const handlePaste = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const res = await apiFetch("/v1/ingestion/paste", {
        method: "POST",
        body: JSON.stringify({ title: pasteTitle, content: pasteContent, doc_type: pasteType }),
      });
      if (!res.ok) {
        showToast("Could not ingest document", "error");
        return;
      }
      setPasteTitle("");
      setPasteContent("");
      showToast("Document queued for processing");
      void refresh();
    },
    [pasteTitle, pasteContent, pasteType, showToast, refresh]
  );

  const handleUpload = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!uploadFile) return;
      const form = new FormData();
      form.append("title", uploadTitle || uploadFile.name);
      form.append("doc_type", uploadType);
      form.append("file", uploadFile);
      const res = await apiFetch("/v1/ingestion/upload", { method: "POST", body: form });
      if (!res.ok) {
        showToast("Could not upload file", "error");
        return;
      }
      setUploadTitle("");
      setUploadFile(null);
      showToast("File uploaded");
      void refresh();
    },
    [uploadFile, uploadTitle, uploadType, showToast, refresh]
  );

  const handleAddCompetitor = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const res = await apiFetch("/v1/competitive/competitors", {
        method: "POST",
        body: JSON.stringify({ name: compName, website_url: compUrl || undefined }),
      });
      if (!res.ok) {
        showToast("Could not add competitor", "error");
        return;
      }
      setCompName("");
      setCompUrl("");
      showToast("Competitor added");
      void refresh();
    },
    [compName, compUrl, showToast, refresh]
  );

  const value = useMemo<DataHubContextValue>(
    () => ({
      org,
      completeness,
      documents,
      competitors,
      toast,
      showToast,
      saving,
      refresh,
      profile: {
        name,
        setName,
        websiteUrl,
        setWebsiteUrl,
        industry,
        setIndustry,
        targetCustomers,
        setTargetCustomers,
        businessModel,
        setBusinessModel,
        stage,
        setStage,
        goals,
        setGoals,
        brandVoice,
        setBrandVoice,
        competitorNotes,
        setCompetitorNotes,
        saveProfile,
      },
      sources: {
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
      },
      competitorsForm: {
        compName,
        setCompName,
        compUrl,
        setCompUrl,
        handleAddCompetitor,
      },
    }),
    [
      org,
      completeness,
      documents,
      competitors,
      toast,
      showToast,
      saving,
      refresh,
      name,
      websiteUrl,
      industry,
      targetCustomers,
      businessModel,
      stage,
      goals,
      brandVoice,
      competitorNotes,
      pasteTitle,
      pasteContent,
      pasteType,
      uploadTitle,
      uploadType,
      uploadFile,
      compName,
      compUrl,
      saveProfile,
      handlePaste,
      handleUpload,
      handleAddCompetitor,
    ]
  );

  return <DataHubContext.Provider value={value}>{children}</DataHubContext.Provider>;
}

/**
 * Handles use data hub behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function useDataHub() {
  const ctx = useContext(DataHubContext);
  if (!ctx) throw new Error("useDataHub must be used within DataHubProvider");
  return ctx;
}
