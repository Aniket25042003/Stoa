/**
 * @file apps/web/src/app/api/waitlist/route.ts
 * @layer Frontend BFF / API Routes
 * @description Handles browser-facing API requests and forwards them through the server-side boundary.
 * @dependencies standard library / local modules
 */
import { proxyJsonResponse } from "@/lib/server-api";

/**
 * Handles post behavior for this part of the Stoa application.
 *
 * @param request - Input value used to render UI or execute the workflow.
 * @returns Rendered UI or completion signal for the workflow.
 */
export async function POST(request: Request) {
  return proxyJsonResponse(request, "/v1/waitlist");
}
