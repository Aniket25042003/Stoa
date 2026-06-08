export function isSafeExternalHref(url: string): boolean {
  try {
    const parsed = new URL(url.trim());
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && Boolean(parsed.hostname);
  } catch {
    return false;
  }
}

export function safeExternalHref(url: string): string | undefined {
  return isSafeExternalHref(url) ? url : undefined;
}
