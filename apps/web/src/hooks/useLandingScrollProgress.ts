"use client";

import { useCallback, useEffect, useState } from "react";
import { FEATURE_SECTION_COUNT } from "@/lib/landingFeatures";

export interface LandingScrollState {
  /** 0–1 across the 6-feature scroll range */
  progress: number;
  /** 0–5 active feature index */
  activeSection: number;
  /** 0–5 feature face index (same as activeSection) */
  activeFace: number;
}

const DEFAULT_STATE: LandingScrollState = {
  progress: 0,
  activeSection: 0,
  activeFace: 0,
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

export function useLandingScrollProgress(
  scrollRangeRef: React.RefObject<HTMLElement | null>,
  sectionCount: number
) {
  const [state, setState] = useState<LandingScrollState>(DEFAULT_STATE);

  const update = useCallback(() => {
    const el = scrollRangeRef.current;
    if (!el) return;

    const rect = el.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const scrollTop = window.scrollY;
    const rangeTop = scrollTop + rect.top;
    const rangeHeight = el.offsetHeight;
    const scrollable = Math.max(rangeHeight - viewportHeight, 1);

    const rawProgress = (scrollTop - rangeTop) / scrollable;
    const progress = clamp(rawProgress, 0, 1);

    const maxSection = Math.max(sectionCount - 1, 0);
    const sectionIndex = clamp(Math.round(progress * maxSection), 0, maxSection);

    const activeFace = clamp(sectionIndex, 0, FEATURE_SECTION_COUNT - 1);

    setState((prev) => {
      if (
        prev.progress === progress &&
        prev.activeSection === sectionIndex &&
        prev.activeFace === activeFace
      ) {
        return prev;
      }
      return { progress, activeSection: sectionIndex, activeFace };
    });
  }, [scrollRangeRef, sectionCount]);

  useEffect(() => {
    update();

    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update, { passive: true });

    const el = scrollRangeRef.current;
    const ro = el ? new ResizeObserver(update) : null;
    if (el && ro) ro.observe(el);

    return () => {
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      ro?.disconnect();
    };
  }, [update, scrollRangeRef]);

  return state;
}
