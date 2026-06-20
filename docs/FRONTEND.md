# Frontend

**One-liner:** Next.js 15 App Router with BFF proxy, Supabase auth, and workspace-based product pages.

## Why it exists

The frontend delivers marketing pages and an authenticated product shell. A BFF (Backend-for-Frontend) proxy keeps API keys and service role credentials off the browser while providing a seamless auth experience via Supabase SSR.

## How it works

### Directory organization

```
apps/web/src/
├── app/
│   ├── (marketing)/     Public pages: /, /pricing, /faq, /waitlist
│   ├── (app)/           Authenticated product pages
│   ├── (onboarding)/    /onboarding flow
│   ├── login/           Auth pages
│   └── api/             BFF routes (backend proxy, auth)
├── components/
│   ├── app-shell/       Sidebar, top bar, org switcher
│   ├── product/         Design system primitives
│   ├── marketing/       Landing page UI + immersive WebGL
│   ├── motion/          Animation helpers
│   └── onboarding/      Onboarding wizard
└── lib/                 api.ts, sse.ts, auth, navigation, theme
```

### Routing (App Router)

28 page routes using Next.js 15 route groups:

| Group | Routes | Layout |
|-------|--------|--------|
| `(marketing)` | `/`, `/pricing`, `/faq`, `/how-it-works`, `/see-it-in-action`, `/waitlist` | Marketing navbar + footer |
| `(app)` | `/dashboard`, `/data/*`, `/intelligence`, `/competitive`, `/campaigns`, `/settings/*` | `AppShell` with sidebar |
| `(onboarding)` | `/onboarding`, `/onboarding/processing` | Minimal chrome |
| Standalone | `/login`, `/verify-email`, `/invite/[token]` | Auth pages |

Legacy redirect stubs: `/gtm` → `/intelligence`, `/marketing` → `/campaigns`, `/runs/*` → `/dashboard`.

### Middleware

[`apps/web/src/middleware.ts`](../apps/web/src/middleware.ts):

- Supabase session refresh
- Protected route prefixes (`/dashboard`, `/data`, `/intelligence`, etc.)
- Prelaunch public-site gate
- CSP + security headers

### Data fetching strategy

| Layer | File | Pattern |
|-------|------|---------|
| Client | `lib/api.ts` | `apiFetch("/v1/...")` → `/api/backend/v1/...` |
| Server | `lib/api-server.ts` | Direct `NEXT_PUBLIC_API_URL` with JWT |
| SSE | `lib/sse.ts` | `consumeSse()` for realtime events |
| BFF | `app/api/backend/[...path]/route.ts` | Proxies all methods with auth + org cookie |

No React Query or SWR — components use `useState` + `useEffect` + `apiFetch` directly.

### Shared layouts

- **Root** — `app/layout.tsx`: fonts, `ThemeProvider`, `globals.css`
- **App** — `app/(app)/layout.tsx`: session-state gates (email verify, onboarding), wraps in `AppShell`
- **Data hub** — `app/(app)/data/layout.tsx`: `DataHubLayout` with subnav

Navigation SSOT: [`lib/app-navigation.ts`](../apps/web/src/lib/app-navigation.ts)

## Architecture diagram

```
Browser
   │
   ├─► (marketing) pages ──► static/SSR, no auth
   │
   └─► (app) pages ──► middleware auth check
              │
              ├─► apiFetch() ──► /api/backend/v1/* (BFF)
              │                        │
              │                        ▼
              │                   FastAPI + JWT + X-Org-Id
              │
              └─► consumeSse() ──► /api/backend/v1/*/events
```

## Key code callouts

- **`AppShell`** — [`components/app-shell/AppShell.tsx`](../apps/web/src/components/app-shell/AppShell.tsx) — Sidebar + top bar wrapper.
- **`apiFetch()`** — [`lib/api.ts`](../apps/web/src/lib/api.ts) — Client-side API helper.
- **BFF proxy** — [`app/api/backend/[...path]/route.ts`](../apps/web/src/app/api/backend/[...path]/route.ts) — Auth + org header injection.
- **`IntelligenceWorkspace`** — [`app/(app)/intelligence/intelligence-workspace.tsx`](../apps/web/src/app/(app)/intelligence/intelligence-workspace.tsx) — Main Q&A UI.

## Tech decisions

1. **BFF proxy pattern** — Browser never sees `SUPABASE_SERVICE_ROLE_KEY` or direct API URL in client bundle for writes.
2. **No global state library** — React Context + local state keeps bundle small; server state fetched on mount.
3. **Workspace components** — Each feature page renders a `*-workspace.tsx` client component with its own data fetching.

## Talking points

- `product-v2` CSS class applied to authenticated pages for design system tokens.
- Org context via `stoa-active-org` cookie set by org switcher.
- Vercel deployment with `vercel.json` config.

## Related docs

- Component hierarchy: [`docs/frontend/COMPONENT_TREE.md`](frontend/COMPONENT_TREE.md)
- State patterns: [`docs/frontend/STATE_MANAGEMENT.md`](frontend/STATE_MANAGEMENT.md)
- End-to-end flow: [`docs/frontend/DATA_FLOW.md`](frontend/DATA_FLOW.md)
