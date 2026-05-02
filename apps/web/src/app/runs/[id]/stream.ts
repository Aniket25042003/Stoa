/**
 * Read text/event-stream with Authorization header (EventSource cannot set headers).
 */
export async function consumeSse(
  url: string,
  accessToken: string,
  onEvent: (data: Record<string, unknown>) => void,
  signal?: AbortSignal
): Promise<void> {
  const res = await fetch(url, {
    headers: { Accept: "text/event-stream", Authorization: `Bearer ${accessToken}` },
    signal,
  });
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
