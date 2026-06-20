/**
 * @file apps/web/src/lib/sse.ts
 * @layer Frontend Shared Utilities
 * @description Provides shared client/server utility logic used across the Next.js app.
 * @dependencies standard library / local modules
 */
/**
 * Read text/event-stream. Browser calls go through the authenticated BFF proxy.
 */
export async function consumeSse(
  path: string,
  onEvent: (data: Record<string, unknown>) => void,
  signal?: AbortSignal,
  accessToken?: string
): Promise<void> {
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const url =
    typeof window === "undefined"
      ? `${process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "")}/${normalizedPath}`
      : `/api/backend/${normalizedPath}`;

  const headers: Record<string, string> = { Accept: "text/event-stream" };
  if (typeof window === "undefined" && accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  const res = await fetch(url, { headers, signal });
  if (!res.ok || !res.body) {
    throw new Error(`SSE failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
    let idx: number;
    while ((idx = buf.indexOf("\n\n")) !== -1) {
      const chunk = buf.slice(0, idx);
      buf = buf.slice(idx + 2);
      const lines = chunk.split("\n");
      for (const line of lines) {
        if (line.startsWith(":") || line.trim() === "") continue;
        if (line.startsWith("data:")) {
          const raw = line.slice(5).trim();
          try {
            onEvent(JSON.parse(raw) as Record<string, unknown>);
          } catch {
            onEvent({ message: raw });
          }
        }
      }
    }
  }
}
