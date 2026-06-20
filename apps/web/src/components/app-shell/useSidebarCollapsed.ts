/**
 * @file apps/web/src/components/app-shell/useSidebarCollapsed.ts
 * @layer Frontend Product UI
 * @description Implements a reusable React component used by the Stoa web experience.
 * @dependencies React
 */
"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "stoa-sidebar-collapsed";

/**
 * Handles use sidebar collapsed behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function useSidebarCollapsed() {
  const [collapsed, setCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    setCollapsed(stored === "true");
    setHydrated(true);
  }, []);

  function toggle() {
    setCollapsed((prev) => {
      const next = !prev;
      window.localStorage.setItem(STORAGE_KEY, String(next));
      return next;
    });
  }

  return { collapsed, toggle, hydrated };
}
