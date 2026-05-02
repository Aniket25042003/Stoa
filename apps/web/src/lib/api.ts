const base = () => {
  const b = process.env.NEXT_PUBLIC_API_URL;
  if (!b) throw new Error("NEXT_PUBLIC_API_URL is not set");
  return b.replace(/\/$/, "");
};

export async function apiFetch(path: string, init: RequestInit & { accessToken?: string } = {}) {
  const { accessToken, ...rest } = init;
  const headers = new Headers(rest.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  headers.set("Content-Type", headers.get("Content-Type") ?? "application/json");
  const res = await fetch(`${base()}${path}`, { ...rest, headers });
  return res;
}
