/** Client-safe API helper — always routes through the BFF proxy. */
export async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`/api/backend/${normalizedPath}`, { ...init, headers });
  return res;
}
