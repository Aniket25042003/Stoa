import { NextResponse } from "next/server";
import { ACTIVE_ORG_COOKIE } from "@/lib/active-org";
import { proxyJsonResponse } from "@/lib/server-api";

export async function POST(request: Request) {
  const upstream = await proxyJsonResponse(request, "/v1/orgs/switch");
  const text = await upstream.text();
  if (!upstream.ok) {
    return new Response(text, { status: upstream.status, headers: { "Content-Type": "application/json" } });
  }
  let body: { active_org_id?: string } = {};
  try {
    body = JSON.parse(text) as { active_org_id?: string };
  } catch {
    return NextResponse.json({ detail: "Invalid response." }, { status: 502 });
  }
  const response = NextResponse.json(body);
  if (body.active_org_id) {
    response.cookies.set(ACTIVE_ORG_COOKIE, body.active_org_id, {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
    });
  }
  return response;
}
