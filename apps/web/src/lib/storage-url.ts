/**
 * @file apps/web/src/lib/storage-url.ts
 * @layer Frontend Shared Utilities
 * @description Validates Supabase storage URLs before use in href/img/src.
 */

function supabaseStorageOrigin(): string | null {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!supabaseUrl) return null;
  try {
    return new URL(supabaseUrl).origin;
  } catch {
    return null;
  }
}

/** True when URL is HTTPS and points at this project's Supabase storage API. */
export function isAllowedStoragePublicUrl(raw: string): boolean {
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return false;
    const expectedOrigin = supabaseStorageOrigin();
    if (!expectedOrigin || url.origin !== expectedOrigin) return false;
    return url.pathname.startsWith("/storage/v1/object/");
  } catch {
    return false;
  }
}

export function safeStoragePublicUrl(raw: string | null | undefined): string | null {
  if (!raw) return null;
  return isAllowedStoragePublicUrl(raw) ? raw : null;
}
