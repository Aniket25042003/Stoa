import { NextResponse } from "next/server";

/** Legacy endpoint removed — use the current org-scoped API instead. */
export async function POST() {
  return NextResponse.json({ detail: "Endpoint removed" }, { status: 410 });
}
