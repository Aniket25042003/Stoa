/**
 * @file apps/web/src/middleware.ts
 * @layer Application Source
 * @description Implements middleware behavior for the application source.
 * @dependencies Supabase, Next.js
 */
import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import { getAuthEntryPath, isLoginEnabled } from "@/lib/auth-entry";
import { buildContentSecurityPolicy } from "@/lib/csp";
import {
  getPrelaunchLegacyRedirect,
  isPrelaunchPublicApi,
  isPrelaunchPublicPath,
  isPublicSiteOnlyMode,
} from "@/lib/public-site-gate";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/data",
  "/intelligence",
  "/competitive",
  "/campaigns",
  "/settings",
  "/onboarding",
  "/gtm",
  "/marketing",
  "/runs",
];

/**
 * Handles is protected path behavior for this part of the Stoa application.
 *
 * @param pathname - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function isProtectedPath(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

/**
 * Handles apply security headers behavior for this part of the Stoa application.
 *
 * @param response - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function applySecurityHeaders(response: NextResponse): NextResponse {
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  response.headers.set("Content-Security-Policy", buildContentSecurityPolicy());
  if (process.env.NODE_ENV === "production") {
    response.headers.set("Strict-Transport-Security", "max-age=31536000; includeSubDomains");
  }
  return response;
}

/**
 * Handles prelaunch blocked response behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Result consumed by the caller or rendered by React.
 */
function prelaunchBlockedResponse(request: NextRequest): NextResponse {
  return applySecurityHeaders(NextResponse.redirect(new URL("/waitlist", request.url)));
}

/**
 * Handles middleware behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function middleware(request: NextRequest) {
  const nextUrl = request.nextUrl;
  const hostname = nextUrl.hostname;
  const pathname = nextUrl.pathname;
  const publicOnly = isPublicSiteOnlyMode(hostname);

  if (publicOnly) {
    const legacyRedirect = getPrelaunchLegacyRedirect(pathname);
    if (legacyRedirect) {
      return applySecurityHeaders(NextResponse.redirect(new URL(legacyRedirect, request.url)));
    }

    if (pathname.startsWith("/api/")) {
      if (!isPrelaunchPublicApi(pathname, request.method)) {
        return applySecurityHeaders(
          NextResponse.json({ detail: "Not available." }, { status: 404 }),
        );
      }
    } else if (!isPrelaunchPublicPath(pathname)) {
      return prelaunchBlockedResponse(request);
    }
  }

  if (nextUrl.pathname === "/login" && !isLoginEnabled(hostname)) {
    return prelaunchBlockedResponse(request);
  }

  if (nextUrl.pathname === "/" && nextUrl.searchParams.has("code")) {
    if (publicOnly) {
      return prelaunchBlockedResponse(request);
    }
    const dest = nextUrl.clone();
    dest.pathname = "/auth/callback";
    return NextResponse.redirect(dest);
  }

  let response = NextResponse.next({ request: { headers: request.headers } });

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    if (isProtectedPath(nextUrl.pathname)) {
      return prelaunchBlockedResponse(request);
    }
    return applySecurityHeaders(response);
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
    return NextResponse.redirect(new URL(getAuthEntryPath({ hostname }), request.url));
  }

  return applySecurityHeaders(response);
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|images/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|woff2?)$).*)",
  ],
};
