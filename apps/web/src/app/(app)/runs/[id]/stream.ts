import { consumeSse } from "@/lib/sse";

export async function consumeRunSse(
  path: string,
  onEvent: (data: Record<string, unknown>) => void,
  signal?: AbortSignal,
  accessToken?: string
): Promise<void> {
  return consumeSse(path, onEvent, signal, accessToken);
}
