# Phase 1b — App UI Revamp

## Scope

Unify authenticated Stoa surfaces (login through dashboard, data hub, intelligence workspaces, settings) with the marketing cream/indigo design system. Replace the flat header nav with a hybrid **AppShell**: collapsible sidebar (desktop), bottom nav + sheet (mobile), grouped menus with submenus.

## Design system

- **Tokens:** Reuse `mkt-*` CSS variables (`--mkt-surface`, `--mkt-ink`, `--mkt-muted`, `--mkt-accent`, `--mkt-accent-warm`, `--mkt-dark-band`).
- **Wrapper:** `.product-v2` on authenticated layouts; calmer grid/blur atmosphere than marketing.
- **Typography:** Syne for titles, DM Sans for body; uppercase micro-label eyebrows.
- **Primitives:** `apps/web/src/components/product/` — `ProductButton`, `ProductCard`, `ProductInput`, `ProductPageHeader`, `ProductBadge`, `ProductStatusPill`, etc.
- **Light-only:** Dark mode toggle removed from authenticated app (marketing remains light-only).

## Navigation

Single source of truth: `apps/web/src/lib/app-navigation.ts`.

| Group | Routes |
|-------|--------|
| Home | `/dashboard` |
| Workspace | `/data/profile`, `/data/sources`, `/data/integrations`, `/data/competitors` |
| Intelligence | `/intelligence`, `/competitive`, `/campaigns` |
| Organization | `/settings/team`, `/settings/roles` |

- Permission filtering via `canReadNav()` — items hidden until session permissions load (no flash).
- Data hub uses `SectionSubnav` in `data/layout.tsx`.
- Settings uses `settings/layout.tsx` subnav (Team | Roles).
- Legacy redirects preserved: `/gtm` → `/intelligence`, `/marketing` → `/campaigns`.

## Shell components

- `AppShell`, `AppSidebar`, `AppTopBar`, `AppMobileNav`
- Sidebar collapse persisted in `localStorage` (`useSidebarCollapsed`)
- Mobile: Home, Data, Intel tabs + More sheet (intelligence + org + sign out)

## Page migrations

| Area | Status |
|------|--------|
| Login, verify-email, invite, onboarding | Product auth shell |
| Dashboard | `ProductPageHeader`, stat cards, readiness band |
| Data hub | Sub-routes + shared `DataHubProvider` |
| Intelligence, competitive, campaigns | Product theme |
| Settings team/roles | Product tables + headers |

## Removed / deprecated

- `AppHeader`, `CompanySwitcher`, `AppReadinessGate` (replaced by `AppShell`)
- `gtm-workspace`, `marketing-workspace` (routes redirect only)
- Orange `btn-primary` / `card-glass` on product surfaces (legacy tokens remain in `globals.css` for `/runs` until migrated)

## Middleware

- `/settings` added to `PROTECTED_PREFIXES` in `apps/web/src/middleware.ts`

## Visual QA checklist

Manual pass before release:

- [ ] **Login** — split brand panel + cream card; OAuth + email; no dark mode toggle
- [ ] **Verify email / invite** — centered product card, indigo CTAs
- [ ] **Onboarding** — stepper on cream, indigo progress
- [ ] **Dashboard** — Syne org title, stat grid, dark readiness band, no duplicate quick-link row
- [ ] **Sidebar (desktop)** — groups expand; active route indigo left border; collapse persists on reload
- [ ] **Mobile nav** — bottom tabs; More sheet lists intelligence + org; sign out works
- [ ] **Data hub** — subnav across profile / sources / integrations / competitors
- [ ] **Intelligence** — two-column layout; citation badges; ask follow-up form
- [ ] **Competitive** — warm badge on high-severity alerts
- [ ] **Campaigns** — brief form; `ProductStatusPill` on list + assets panel
- [ ] **Settings** — team table + invite; roles permission matrix
- [ ] **RBAC** — nav items hidden for viewer vs admin (no permission flash)
- [ ] **Org switcher** — mkt tokens in top bar
- [ ] **Legacy URLs** — `/gtm`, `/marketing` redirect correctly

## Exit criteria

- [x] All `(app)`, login, onboarding, verify-email, invite use `mkt-*` tokens on product surfaces
- [x] Single nav config drives sidebar and mobile nav
- [x] Desktop sidebar collapses; mobile bottom nav + sheet
- [x] Data hub submenu routes under `/data/*`
- [x] Dark mode toggle removed from authenticated experience
- [x] `/settings/*` protected in middleware
- [x] Phase agent doc updated (this file)
