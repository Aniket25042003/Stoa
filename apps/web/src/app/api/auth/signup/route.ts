import { proxyJsonResponse } from "@/lib/server-api";

export async function POST(request: Request) {
  return proxyJsonResponse(request, "/v1/auth/signup");
}
