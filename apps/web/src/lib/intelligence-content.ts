/** Normalize LLM insight text for product UI (strip inline refs, fix markdown spacing). */

/** Inline evidence markers: [kb:...], [doc:uuid], [signal:id], etc. */
const INLINE_CITATION_RE =
  /\s*\[(?:kb|doc|signal|precomputed|crm|agent_evidence):[^\]]+\]/gi;

const KB_CITATION_RE = /\s*\[(?:kb:[^\]]+)\]/gi;
const THOUGHT_SIGNATURE_RE = /['"]thought_signature['"]\s*:\s*['"][^'"]*['"]\s*,?\s*/gi;

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/** Remove inline evidence citation markers from synthesized answers. */
export function stripInlineCitations(text: string): string {
  return text
    .replace(INLINE_CITATION_RE, "")
    .replace(KB_CITATION_RE, "")
    .replace(/\s+([.,;:!?])/g, "$1")
    .replace(/[ \t]{2,}/g, " ")
    .trim();
}

/** @deprecated Use stripInlineCitations */
export function stripKbCitations(text: string): string {
  return stripInlineCitations(text);
}

/** Strip Vertex/Gemini thought blocks leaked into stringified agent output. */
export function sanitizeAgentContent(text: string): string {
  let out = text.trim();
  if (!out) return out;

  if (out.startsWith("[{") && out.includes("thought_signature")) {
    const textField = out.match(/'text':\s*'((?:[^'\\]|\\.)*)'/);
    const tailField = out.match(/},\s*'((?:[^'\\]|\\.)*)'\s*\]\s*$/s);
    const parts: string[] = [];
    if (textField?.[1]) parts.push(textField[1].replace(/\\'/g, "'"));
    if (tailField?.[1]) parts.push(tailField[1].replace(/\\'/g, "'"));
    if (parts.length) out = parts.join("");
  }

  return out.replace(THOUGHT_SIGNATURE_RE, "").trim();
}

/** Add line breaks so inline markdown lists and headings parse correctly. */
export function normalizeInsightMarkdown(text: string): string {
  let out = sanitizeAgentContent(stripInlineCitations(text));
  out = out.replace(/\s+(#{1,3}\s+)/g, "\n\n$1");
  out = out.replace(/([.!?])\s+\*\s+/g, "$1\n\n* ");
  out = out.replace(/\s+\*\s+(?=\*\*)/g, "\n\n* ");
  out = out.replace(/[ \t]+\n/g, "\n");
  out = out.replace(/\n{3,}/g, "\n\n");
  out = out.replace(/``+/g, "`");
  return out.trim();
}

/** Drop a leading markdown heading when it repeats the surrounding card title. */
export function stripRedundantMarkdownHeading(text: string, contextualTitle?: string): string {
  if (!contextualTitle?.trim()) return text;
  const titleWords = contextualTitle
    .toLowerCase()
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 4)
    .join("\\s+");
  if (!titleWords) return text;
  const pattern = new RegExp(`^#{1,3}\\s*${titleWords}[^\\n]*\\n+`, "i");
  return text.replace(pattern, "").trim();
}

/** Full pipeline for rendering intelligence / dashboard copy in the UI. */
export function prepareInsightText(text: string, contextualTitle?: string): string {
  const normalized = normalizeInsightMarkdown(text);
  return stripRedundantMarkdownHeading(normalized, contextualTitle);
}

export function isInternalCitation(value: string): boolean {
  const trimmed = value.trim().replace(/^\[|\]$/g, "");
  return /^(kb|doc|signal|precomputed|crm|agent_evidence):/i.test(trimmed);
}

/** @deprecated Use isInternalCitation */
export function isKbCitation(value: string): boolean {
  return isInternalCitation(value);
}

export function visibleCitations(citations: string[] | undefined): string[] {
  return (citations ?? []).filter((citation) => !isInternalCitation(citation));
}
