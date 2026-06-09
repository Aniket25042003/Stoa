const serverApiBase = () => {
  const b = process.env.NEXT_PUBLIC_API_URL;
  if (!b) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return b.replace(/\/$/, "");
};

const clientApiBase = () => "/api/backend";

function resolveBase() {
  return typeof window === "undefined" ? serverApiBase() : clientApiBase();
}

export async function apiFetch(path: string, init: RequestInit & { accessToken?: string } = {}) {
  const { accessToken, ...rest } = init;
  const headers = new Headers(rest.headers);
  if (typeof window === "undefined" && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (!headers.has("Content-Type") && !(rest.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const res = await fetch(`${resolveBase()}/${normalizedPath}`, { ...rest, headers });
  return res;
}
