"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/cn";
import { prepareInsightText } from "@/lib/intelligence-content";

type InsightMarkdownProps = {
  children: string;
  className?: string;
  /** Parent section title — redundant markdown headings are removed when they match. */
  contextualTitle?: string;
  compact?: boolean;
};

export function InsightMarkdown({
  children,
  className,
  contextualTitle,
  compact = false,
}: InsightMarkdownProps) {
  const markdown = prepareInsightText(children, contextualTitle);
  if (!markdown) return null;

  return (
    <div
      className={cn(
        "insight-markdown text-mkt-muted [&_strong]:font-semibold [&_strong]:text-mkt-ink",
        compact ? "text-xs leading-relaxed" : "text-sm leading-relaxed",
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children: heading }) => (
            <h3
              className={cn(
                "font-semibold tracking-tight text-mkt-ink",
                compact ? "mt-3 mb-1.5 text-sm" : "mt-4 mb-2 text-base",
              )}
            >
              {heading}
            </h3>
          ),
          h2: ({ children: heading }) => (
            <h3
              className={cn(
                "font-semibold tracking-tight text-mkt-ink",
                compact ? "mt-3 mb-1.5 text-sm" : "mt-4 mb-2 text-base",
              )}
            >
              {heading}
            </h3>
          ),
          h3: ({ children: heading }) => (
            <h4
              className={cn(
                "font-semibold text-mkt-ink",
                compact ? "mt-2 mb-1 text-xs" : "mt-3 mb-1.5 text-sm",
              )}
            >
              {heading}
            </h4>
          ),
          p: ({ children: paragraph }) => (
            <p className={cn("text-mkt-muted", compact ? "mb-2 last:mb-0" : "mb-3 last:mb-0")}>
              {paragraph}
            </p>
          ),
          ul: ({ children: list }) => (
            <ul
              className={cn(
                "list-disc space-y-1.5 pl-5 text-mkt-muted",
                compact ? "mb-2" : "mb-3",
              )}
            >
              {list}
            </ul>
          ),
          ol: ({ children: list }) => (
            <ol
              className={cn(
                "list-decimal space-y-1.5 pl-5 text-mkt-muted",
                compact ? "mb-2" : "mb-3",
              )}
            >
              {list}
            </ol>
          ),
          li: ({ children: item }) => <li className="leading-relaxed">{item}</li>,
          a: ({ href, children: linkChildren }) => {
            const safe =
              href && /^https?:\/\//i.test(href) && !/^javascript:/i.test(href) ? href : undefined;
            if (!safe) {
              return <span>{linkChildren}</span>;
            }
            return (
              <a href={safe} target="_blank" rel="noopener noreferrer" className="text-mkt-ink underline">
                {linkChildren}
              </a>
            );
          },
          img: () => null,
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
