"use client";

import { useEffect, useState } from "react";
import type { SessionState } from "@/lib/auth-workflow";

export function useAppPermissions() {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    void (async () => {
      const res = await fetch("/api/auth/session");
      if (res.ok) {
        const state = (await res.json()) as SessionState & { permissions?: string[] };
        setPermissions(state.permissions ?? []);
      }
      setLoaded(true);
    })();
  }, []);

  return { permissions, loaded };
}
