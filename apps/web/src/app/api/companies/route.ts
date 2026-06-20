/**
 * @file apps/web/src/app/api/companies/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies Next.js
 */
import { NextResponse } from "next/server";

/** Legacy endpoint removed — use the current org-scoped API instead. */
export async function POST() {
  return NextResponse.json({ detail: "Endpoint removed" }, { status: 410 });
}
