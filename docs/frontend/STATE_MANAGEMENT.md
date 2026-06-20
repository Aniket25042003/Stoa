# State Management

**One-liner:** React Context for Data Hub and theme; cookies for org context; no global store library.

## Why it exists

The product scope doesn't require complex client-side state synchronization. Server data is fetched on page load; org context persists in cookies; only the Data Hub shares state across sub-pages.

## State layers

### 1. Global React Context (2 providers)

| Context | File | Shape | Scope |
|---------|------|-------|-------|
| `DataHubContext` | `app/(app)/data/data-hub-context.tsx` | `{ profile, documents, competitors, toasts, saveProfile, handleUpload, handlePaste, handleAddCompetitor }` | `/data/*` pages |
| `ThemeProvider` | `lib/theme.tsx` | `{ theme: "light" \| "dark", setTheme }` | Marketing pages (product is light-only) |

### 2. Local component state

All workspace components use `useState` + `useCallback` + `useEffect`:

```tsx
// intelligence-workspace.tsx pattern
const [signals, setSignals] = useState<Signal[]>([]);
const [question, setQuestion] = useState("");
const [answer, setAnswer] = useState<string | null>(null);
const [loading, setLoading] = useState(false);
```

No Zustand, Redux, Jotai, or TanStack Query.

### 3. Cookies (cross-session)

| Cookie / storage | File | Purpose |
|------------------|------|---------|
| `stoa-active-org` | `lib/active-org.ts` | Active org ID sent as `X-Org-Id` |
| Supabase auth cookies | `lib/supabase/server.ts` | Session managed by `@supabase/ssr` |

### 4. localStorage (legacy migration)

| Key | File | Purpose |
|-----|------|---------|
| `stoa.activeCompanyId` | `lib/active-company.ts` | Legacy company ID (migrating from `nexara.*`) |

### 5. Server state (fetched, not cached)

Data fetched via `apiFetch()` on component mount — no SWR/React Query cache keys. Each workspace calls refresh on load:

| Workspace | Endpoints fetched |
|-----------|-------------------|
| Intelligence | `/v1/intelligence/documents`, `/signals`, `/icp`, `/insights`, `/v1/dashboard/summary` |
| Dashboard | `/v1/dashboard/summary` |
| Competitive | `/v1/competitive/competitors`, `/alerts` |
| Campaigns | `/v1/campaigns` |
| Data Hub | `/v1/orgs/me`, `/v1/intelligence/documents`, `/v1/competitive/competitors` |

### 6. Permissions state

`useAppPermissions()` hook:

```tsx
// Fetches /api/auth/session on mount
const { permissions, loading } = useAppPermissions();
// Returns Set<string> of "resource:action" strings
```

Used by sidebar to hide nav items user can't access.

## Architecture diagram

```
┌─────────────────────────────────────────┐
│  Cookies: stoa-active-org, auth session │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  AppShell                                │
│  └── useAppPermissions() → nav gating   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  DataHubContext         Workspace local state
  (shared /data/*)       (useState per page)
        │                     │
        └──────────┬──────────┘
                   ▼
              apiFetch() → BFF → FastAPI
```

## DataHubContext shape

```tsx
type DataHubContextValue = {
  profile: OrgProfile | null;
  documents: Document[];
  competitors: Competitor[];
  toasts: Toast[];
  loading: boolean;
  saveProfile: (data: Partial<OrgProfile>) => Promise<void>;
  handleUpload: (file: File) => Promise<void>;
  handlePaste: (text: string, title: string) => Promise<void>;
  handleAddCompetitor: (data: CompetitorInput) => Promise<void>;
  dismissToast: (id: string) => void;
};
```

## Key code callouts

- **`data-hub-context.tsx`** — Only shared context in the product app.
- **`useAppPermissions.ts`** — Permission-based UI gating.
- **`active-org.ts`** — Client-side org cookie read/write.
- **`theme.tsx`** — Dark/light toggle for marketing.

## Tech decisions

1. **No React Query** — Fetch-on-mount is sufficient for current page count; avoids cache invalidation complexity.
2. **Context scoped to Data Hub** — Only pages that truly share state use Context; other workspaces are independent.
3. **Cookie-based org context** — Survives page navigation; BFF reads cookie for `X-Org-Id` header.

## Talking points

- Adding TanStack Query would benefit pages that refetch frequently (intelligence refresh after upload).
- SSE events update local state directly in workspace components (no event bus).
- Server Components used sparingly — most product pages are `"use client"` workspaces.
