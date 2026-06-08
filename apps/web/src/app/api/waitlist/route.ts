import { NextResponse } from "next/server";
import { createAdminClient } from "@/lib/supabase/admin";

const RATE_WINDOW_MS = 60_000;
const RATE_LIMIT = 5;
const hits = new Map<string, number[]>();

function rateLimited(ip: string): boolean {
  const now = Date.now();
  const windowStart = now - RATE_WINDOW_MS;
  const recent = (hits.get(ip) ?? []).filter((t) => t >= windowStart);
  if (recent.length >= RATE_LIMIT) {
    hits.set(ip, recent);
    return true;
  }
  recent.push(now);
  hits.set(ip, recent);
  return false;
}

export async function POST(request: Request) {
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  if (rateLimited(ip)) {
    return NextResponse.json({ detail: "Too many requests" }, { status: 429 });
  }

  let body: { name?: string; email?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ detail: "Invalid JSON" }, { status: 400 });
  }

  const name = (body.name ?? "").trim();
  const email = (body.email ?? "").trim().toLowerCase();
  if (!name || name.length > 200) {
    return NextResponse.json({ detail: "Invalid name" }, { status: 400 });
  }
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return NextResponse.json({ detail: "Invalid email" }, { status: 400 });
  }

  try {
    const supabase = createAdminClient();
    const { error } = await supabase.from("waitlist").insert([{ name, email }]);
    if (error) {
      if (error.code === "23505") {
        return NextResponse.json({ status: "already_registered" }, { status: 200 });
      }
      return NextResponse.json({ detail: "Registration failed" }, { status: 500 });
    }
    return NextResponse.json({ status: "registered" }, { status: 201 });
  } catch {
    return NextResponse.json({ detail: "Waitlist unavailable" }, { status: 503 });
  }
}
