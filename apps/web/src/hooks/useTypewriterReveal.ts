"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type UseTypewriterRevealOptions = {
  enabled?: boolean;
  /** Target total reveal duration for long answers (ms). */
  maxDurationMs?: number;
  onComplete?: () => void;
};

function prefersReducedMotion(): boolean {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function tokenizeForReveal(text: string): string[] {
  const tokens: string[] = [];
  const re = /\S+\s*/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    tokens.push(match[0]);
  }
  return tokens;
}

export function useTypewriterReveal(
  text: string,
  { enabled = true, maxDurationMs = 4000, onComplete }: UseTypewriterRevealOptions = {},
) {
  const tokens = useMemo(() => tokenizeForReveal(text), [text]);
  const [visibleCount, setVisibleCount] = useState(0);
  const [isRevealing, setIsRevealing] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const shouldAnimate = enabled && text.length > 0 && !prefersReducedMotion();

  useEffect(() => {
    if (!shouldAnimate) {
      setVisibleCount(tokens.length);
      setIsRevealing(false);
      return;
    }

    setVisibleCount(0);
    setIsRevealing(true);

    const tickMs = 32;
    const wordsPerTick = Math.max(1, Math.ceil(tokens.length / (maxDurationMs / tickMs)));

    let count = 0;
    const timer = window.setInterval(() => {
      count = Math.min(tokens.length, count + wordsPerTick);
      setVisibleCount(count);
      if (count >= tokens.length) {
        window.clearInterval(timer);
        setIsRevealing(false);
        onCompleteRef.current?.();
      }
    }, tickMs);

    return () => window.clearInterval(timer);
  }, [text, tokens.length, shouldAnimate, maxDurationMs]);

  const displayText = shouldAnimate
    ? tokens.slice(0, visibleCount).join("")
    : text;

  return { displayText, isRevealing, isComplete: !isRevealing };
}
