/** Client-safe API helper — always routes through the BFF proxy. */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  try {
    return await fetch(`/api/backend/${normalizedPath}`, { ...init, headers });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to fetch";
    return new Response(JSON.stringify({ detail: message }), {
      status: 503,
      headers: { "Content-Type": "application/json" },
    });
  }
}
