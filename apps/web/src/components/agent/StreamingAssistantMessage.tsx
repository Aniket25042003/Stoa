"use client";

import { useEffect, useRef } from "react";
import { InsightMarkdown } from "@/components/product/InsightMarkdown";
import { useTypewriterReveal } from "@/hooks/useTypewriterReveal";
import { cn } from "@/lib/cn";

type StreamingAssistantMessageProps = {
  content: string;
  reveal?: boolean;
  onRevealComplete?: () => void;
};

export function StreamingAssistantMessage({
  content,
  reveal = false,
  onRevealComplete,
}: StreamingAssistantMessageProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const { displayText, isRevealing } = useTypewriterReveal(content, {
    enabled: reveal,
    onComplete: onRevealComplete,
  });

  useEffect(() => {
    if (!isRevealing) return;
    rootRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [displayText, isRevealing]);

  return (
    <div ref={rootRef} className="relative">
      <InsightMarkdown>{displayText}</InsightMarkdown>
      {isRevealing ? (
        <span
          className={cn(
            "ml-0.5 inline-block h-[1em] w-0.5 translate-y-px animate-pulse",
            "bg-mkt-accent align-middle",
          )}
          aria-hidden
        />
      ) : null}
    </div>
  );
}
