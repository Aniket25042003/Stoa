export function clientIpFromRequest(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for");
  if (forwarded) {
    const part = forwarded.split(",")[0]?.trim();
    if (part) return part;
  }
  const realIp = request.headers.get("x-real-ip")?.trim();
  if (realIp) return realIp;
  return "unknown";
}

export function trustedProxyHeaders(request: Request): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Stoa-Client-IP": clientIpFromRequest(request),
  };
  const secret = process.env.INTERNAL_PROXY_SECRET;
  if (secret) {
    headers["X-Stoa-Proxy-Secret"] = secret;
  }
  return headers;
}
