"use client";

import { useEffect, useState } from "react";
import type { SessionState } from "@/lib/auth-workflow";

export function useAppPermissions() {
  const [permissions, setPermissions] = useState<string[] | null>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const controller = new AbortController();

    void (async () => {
      try {
        const res = await fetch("/api/auth/session", { signal: controller.signal });
        if (!res.ok) {
          console.error("Failed to load session permissions", res.status);
          setPermissions(null);
          return;
        }
        const state = (await res.json()) as SessionState & { permissions?: string[] };
        setPermissions(state.permissions ?? []);
      } catch (error) {
        if (controller.signal.aborted) return;
        console.error("Failed to load session permissions", error);
        setPermissions(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoaded(true);
        }
      }
    })();

    return () => controller.abort();
  }, []);

  return { permissions, loaded };
}
