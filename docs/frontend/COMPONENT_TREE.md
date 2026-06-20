# Component Tree

**One-liner:** App shell wraps workspace pages; product primitives compose feature UIs.

## Why it exists

Components split into app shell (navigation chrome), product design system (reusable primitives), marketing (public site), and page-level workspace containers that own data fetching.

## Component hierarchy

```
RootLayout (fonts, ThemeProvider, globals.css)
│
├── (marketing)/layout.tsx
│   ├── Navbar
│   ├── Footer
│   ├── LenisProvider
│   └── MarketingPageShell
│       ├── MarketingHero
│       ├── CapabilityPanel
│       ├── FeatureSection
│       └── WaitlistForm
│
├── (app)/layout.tsx
│   └── AppShell
│       ├── AppSidebar          ← APP_NAVIGATION from lib/app-navigation.ts
│       ├── AppTopBar
│       │   └── OrgSwitcher
│       ├── AppMobileNav
│       └── {page workspace}
│           ├── DashboardWorkspace
│           ├── IntelligenceWorkspace
│           ├── CompetitiveWorkspace
│           ├── CampaignsWorkspace
│           └── DataHubLayout
│               └── DataHubContext.Provider
│                   ├── ProfilePage
│                   ├── SourcesPage
│                   ├── IntegrationsPage
│                   └── CompetitorsPage
│
└── (onboarding)/layout.tsx
    └── OnboardingWizard
```

## Major workspace components

| Component | Path | Data needed | User interactions |
|-----------|------|-------------|---------------------|
| `IntelligenceWorkspace` | `app/(app)/intelligence/intelligence-workspace.tsx` | Signals, ICP, insights, CRM stats | Ask question, expand insights, refresh |
| `DashboardWorkspace` | `app/(app)/dashboard/dashboard-workspace.tsx` | Dashboard summary, completeness | View stats, navigate to incomplete sections |
| `CompetitiveWorkspace` | `app/(app)/competitive/competitive-workspace.tsx` | Competitors, alerts | Add/edit/delete competitor, trigger scan |
| `CampaignsWorkspace` | `app/(app)/campaigns/campaigns-workspace.tsx` | Campaign list | Create campaign, view assets |
| `DataHubContext` | `app/(app)/data/data-hub-context.tsx` | Org profile, documents, competitors | Upload, paste, save profile, toasts |

## App shell components

| Component | Path | Role |
|-----------|------|------|
| `AppShell` | `components/app-shell/AppShell.tsx` | Sidebar + top bar layout wrapper |
| `AppSidebar` | `components/app-shell/AppSidebar.tsx` | Navigation from `APP_NAVIGATION` |
| `AppTopBar` | `components/app-shell/AppTopBar.tsx` | Org switcher, user menu |
| `OrgSwitcher` | `components/app-shell/OrgSwitcher.tsx` | Multi-org selection, sets cookie |
| `AppMobileNav` | `components/app-shell/AppMobileNav.tsx` | Bottom tab bar on mobile |
| `CompleteDataPrompt` | `components/app-shell/CompleteDataPrompt.tsx` | Empty state when no data ingested |
| `useAppPermissions` | `components/app-shell/useAppPermissions.ts` | Fetches permissions from session |

## Product primitives (design system)

| Component | Path | Props / usage |
|-----------|------|---------------|
| `ProductButton` | `components/product/ProductButton.tsx` | `variant`, `size` — primary CTA |
| `ProductCard` | `components/product/ProductCard.tsx` | Container with sand background |
| `ProductInput` | `components/product/ProductInput.tsx` | Text input, textarea variants |
| `ProductBadge` | `components/product/ProductBadge.tsx` | Status/kind labels |
| `ProductPageHeader` | `components/product/ProductPageHeader.tsx` | Page title + description |
| `ProductEmptyState` | `components/product/ProductEmptyState.tsx` | No-data placeholder |
| `ProductAtmosphere` | `components/product/ProductAtmosphere.tsx` | Background glow effects |
| `AuthPageShell` | `components/product/AuthPageShell.tsx` | Login/signup layout |

## Marketing components (selected)

| Component | Path | Role |
|-----------|------|------|
| `MarketingHero` | `components/marketing/immersive/MarketingHero.tsx` | Landing hero with orb |
| `ProductOrbCanvas` | `components/marketing/immersive/ProductOrbCanvas.tsx` | WebGL product orb |
| `CapabilityPanel` | `components/marketing/immersive/CapabilityPanel.tsx` | Feature capability tabs |
| `ScrollLinkedLanding` | `components/marketing/immersive/ScrollLinkedLanding.tsx` | Scroll-driven landing |
| `PricingCard` | `components/marketing/PricingCard.tsx` | Pricing tier display |

## Architecture diagram

```
AppShell (layout chrome)
    │
    ├── AppSidebar ──► APP_NAVIGATION links
    │
    └── Page workspace (feature container)
            │
            ├── apiFetch() for data
            ├── Product* primitives for UI
            └── consumeSse() for realtime
```

## Key code callouts

- **`APP_NAVIGATION`** — [`lib/app-navigation.ts`](../../apps/web/src/lib/app-navigation.ts) — Single source for sidebar, mobile nav, breadcrumbs.
- **`IntelligenceWorkspace`** — Largest workspace; Q&A + insights + ICP display.
- **`DataHubContext`** — Shared state for all `/data/*` pages.

## Tech decisions

1. **Workspace pattern** — Each feature page is a thin `page.tsx` rendering a `*-workspace.tsx` client component.
2. **Product primitives** — Consistent sand/orange styling via shared components, not copy-paste Tailwind.
3. **Marketing isolation** — `components/marketing/` separate from product; different token system (`mkt-*`).

## Talking points

- 67 component files total; ~20 are product/shell, ~30 marketing, ~10 motion helpers.
- Legacy `RunCard` component remains but `/runs` routes now redirect.
- Permissions gate nav items via `useAppPermissions` hook.
