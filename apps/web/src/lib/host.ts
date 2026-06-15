export function resolveHostname(hostname?: string): string | undefined {
  if (hostname) return hostname;
  if (typeof window !== "undefined") return window.location.hostname;
  return undefined;
}

export function isLoopbackHost(hostname: string | undefined): boolean {
  if (!hostname) return false;
  const host = hostname.toLowerCase();
  return host === "localhost" || host === "127.0.0.1" || host === "[::1]";
}
