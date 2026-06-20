/**
 * @file apps/web/src/lib/theme.tsx
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies React
 */
"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

/** User-selected appearance. `null` means follow the OS (no key in localStorage). */
export type ThemePreference = "light" | "dark" | null;

type ThemeContextValue = {
  /** Explicit choice, or `null` when following system preference. */
  preference: ThemePreference;
  resolvedTheme: "light" | "dark";
  setTheme: (value: "light" | "dark") => void;
};

const STORAGE_KEY = "gtm-theme";

const ThemeContext = createContext<ThemeContextValue | null>(null);

/**
 * Handles resolve theme behavior for this part of the Stoa application.
 *
 * @param preference - Input value used to render UI or execute the workflow.
 * @param systemPrefersDark - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function resolveTheme(
  preference: ThemePreference,
  systemPrefersDark: boolean
): "light" | "dark" {
  if (preference === "light" || preference === "dark") {
    return preference;
  }
  return systemPrefersDark ? "dark" : "light";
}

/**
 * Handles theme provider behavior for this part of the Stoa application.
 *
 * @param children - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(null);
  const [systemPrefersDark, setSystemPrefersDark] = useState(false);
  const [hasReadStorage, setHasReadStorage] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    setSystemPrefersDark(mql.matches);

    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "light" || saved === "dark") {
      setPreferenceState(saved);
    } else {
      setPreferenceState(null);
      if (saved === "system") {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
    setHasReadStorage(true);

    const onChange = (event: MediaQueryListEvent) => setSystemPrefersDark(event.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  const resolvedTheme = resolveTheme(preference, systemPrefersDark);

  useEffect(() => {
    if (!hasReadStorage) {
      return;
    }
    document.documentElement.classList.toggle("dark", resolvedTheme === "dark");
    if (preference === null) {
      localStorage.removeItem(STORAGE_KEY);
    } else {
      localStorage.setItem(STORAGE_KEY, preference);
    }
  }, [resolvedTheme, preference, hasReadStorage]);

  const setTheme = (value: "light" | "dark") => {
    setPreferenceState(value);
  };

  const value = useMemo(
    () => ({
      preference,
      resolvedTheme,
      setTheme,
    }),
    [preference, resolvedTheme]
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Handles use theme behavior for this part of the Stoa application.
 * @returns Rendered UI or completion signal for the workflow.
 */
export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return ctx;
}
