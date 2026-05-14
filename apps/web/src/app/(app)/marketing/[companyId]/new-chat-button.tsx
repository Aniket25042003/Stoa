"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

export function NewMarketingChatButton({ accessToken, companyId }: { accessToken: string; companyId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function onClick() {
    setBusy(true);
    try {
      const res = await apiFetch(`/v1/companies/${companyId}/chats`, {
        method: "POST",
        accessToken,
        body: JSON.stringify({}),
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      router.push(`/marketing/${companyId}/chats/${data.id}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <button type="button" className="btn-secondary px-4 py-2 text-sm disabled:opacity-50" disabled={busy} onClick={() => void onClick()}>
      {busy ? "Creating…" : "New marketing chat"}
    </button>
  );
}
