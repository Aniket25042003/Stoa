import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { getAuthEntryPath, isLoginEnabled } from "@/lib/auth-entry";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/data",
  "/intelligence",
  "/competitive",
  "/campaigns",
  "/onboarding",
  "/gtm",
  "/marketing",
  "/runs",
];

function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

export async function middleware(request: NextRequest) {
  const nextUrl = request.nextUrl;

  if (nextUrl.pathname === "/login" && !isLoginEnabled()) {
    return NextResponse.redirect(new URL("/waitlist", request.url));
  }

  if (nextUrl.pathname === "/" && nextUrl.searchParams.has("code")) {
    const dest = nextUrl.clone();
    dest.pathname = "/auth/callback";
    return NextResponse.redirect(dest);
  }

  let response = NextResponse.next({ request: { headers: request.headers } });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    if (isProtectedPath(nextUrl.pathname)) {
      return NextResponse.redirect(new URL(getAuthEntryPath(), request.url));
    }
    return response;
  }

  const supabase = createServerClient(url, key, {
    cookies: {
      getAll() {
        return request.cookies.getAll();
      },
      setAll(cookiesToSet: { name: string; value: string; options?: CookieOptions }[]) {
        cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
        response = NextResponse.next({ request });
        cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (isProtectedPath(nextUrl.pathname) && !user) {
    return NextResponse.redirect(new URL(getAuthEntryPath(), request.url));
  }

  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
