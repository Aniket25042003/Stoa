import { getServerApiBase, proxyToApi } from "@/lib/server-api";

/** Enforce API-side public rate limits before sensitive auth actions. */
export async function enforceAuthRateLimit(
  request: Request,
  email: string,
  scope: "auth_signin" | "auth_signup" | "auth_resend",
): Promise<Response | null> {
  if (!getServerApiBase()) return null;

  const upstream = await proxyToApi(request, "/v1/auth/rate-limit-gate", {
    method: "POST",
    body: JSON.stringify({ email, scope }),
  });
  if (upstream.ok) return null;
  const text = await upstream.text();
  return new Response(text, {
    status: upstream.status,
    headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json" },
  });
}
