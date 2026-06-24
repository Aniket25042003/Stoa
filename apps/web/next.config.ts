import type { NextConfig } from "next";
import { buildContentSecurityPolicy } from "./src/lib/csp";

const isProduction = process.env.NODE_ENV === "production";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: buildContentSecurityPolicy({ allowUnsafeEval: !isProduction }),
  },
  ...(isProduction
    ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }]
    : []),
];

const nextConfig: NextConfig = {
  transpilePackages: [],
  async redirects() {
    return [
      { source: "/see-it-in-action", destination: "/#how-it-works", permanent: false },
      { source: "/pricing", destination: "/#pricing", permanent: false },
      { source: "/faq", destination: "/#faq", permanent: false },
      { source: "/how-it-works", destination: "/#how-it-works", permanent: false },
    ];
  },
  async headers() {
    return [{ source: "/(.*)", headers: securityHeaders }];
  },
};

export default nextConfig;
