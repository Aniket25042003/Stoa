# Color Theme

**One-liner:** Sand-and-orange product palette with indigo marketing accents and Syne typography.

## Why it exists

Stoa uses two visual systems: a warm sand/orange product UI for the authenticated app and a separate marketing design language with indigo accents. CSS custom properties in Tailwind v4 enable theme switching without a config file.

## How it works

1. **Token definition** — [`apps/web/src/app/globals.css`](../apps/web/src/app/globals.css) defines CSS variables in `:root` (light) and `html.dark` (dark).
2. **Tailwind mapping** — `@theme inline` block maps vars to `--color-*` utilities (e.g. `bg-primary`, `text-on-surface`).
3. **Marketing tokens** — Separate `--mkt-*` variables for public pages; applied via `.product-v2` wrapper class.
4. **Fonts** — Loaded in [`apps/web/src/app/layout.tsx`](../apps/web/src/app/layout.tsx) via `next/font/google`.

## Product color tokens (light mode)

| Token | Hex | Usage |
|-------|-----|-------|
| `--surface` | `#F5E6C8` | Sand canvas backdrop |
| `--on-surface` | `#040406` | Primary text (midnight ink) |
| `--on-surface-variant` | `#504838` | Secondary text |
| `--primary` | `#FF571A` | Electric orange — buttons, accents |
| `--on-primary` | `#FAF8F5` | Text on primary buttons |
| `--primary-container` | `#FF8F5E` | Lighter orange container |
| `--secondary` | `#8E713A` | Khaki ink accent |
| `--outline` | `#C4A265` | Borders |
| `--error` | `#cc3333` | Error states |

## Product color tokens (dark mode)

| Token | Hex | Usage |
|-------|-----|-------|
| `--surface` | `#040406` | Pure midnight canvas |
| `--on-surface` | `#F5E6C8` | Sand text on dark |
| `--primary` | `#FF571A` | Neon orange-red primary |
| `--surface-container-low` | `#08080c` | Card backgrounds |
| `--bg-glow-1` | `rgb(255 87 26 / 10%)` | Orange ambient glow |

## Marketing tokens (`mkt-*`)

| Token | Hex | Usage |
|-------|-----|-------|
| `--mkt-surface` | `#F8F6F2` | Marketing page background |
| `--mkt-ink` | `#14141A` | Marketing body text |
| `--mkt-muted` | `#6B6F7D` | Secondary marketing text |
| `--mkt-accent` | `#4F46E5` | Indigo accent (CTAs, links) |
| `--mkt-accent-warm` | `#E85D4C` | Warm coral highlight |
| `--mkt-dark-band` | `#0E1018` | Dark section backgrounds |
| `--mkt-dark-ink` | `#F2F0EB` | Text on dark bands |

## Typography

| Font | Variable | Usage |
|------|----------|-------|
| **Syne** | `--font-syne` | Headings — `font-syne font-extrabold uppercase tracking-tight` |
| **DM Sans** | `--font-dm-sans` | Body, labels — `font-dm-sans text-sm` |
| **Inter** | `--font-inter` | Fallback sans |
| **Space Grotesk** | `--font-space-grotesk` | Eyebrow labels (`.eyebrow` class) |
| **Manrope** | `--font-manrope` | Available, less common |

### Typical heading pattern

```tsx
<h1 className="font-syne text-4xl font-extrabold uppercase tracking-tight text-mkt-ink">
```

### Typical label pattern

```tsx
<p className="font-dm-sans text-[9px] font-bold uppercase tracking-[0.22em] text-mkt-muted">
```

## Animations and utilities

| Utility | Keyframes | Where used |
|---------|-----------|------------|
| `animate-marquee` | `marquee 24s linear` | Marketing marquee |
| `animate-shimmer` | `shimmer 2.4s` | Loading shimmer |
| `animate-float` | `float 6s` | Floating elements |
| `animate-glow-pulse` | `glow-pulse 2s` | Pulsing glow |
| `.hero-dashboard-grid` | `hero-grid-pulse 3.2s` | Dashboard grid animation |
| `.pipeline-step-pulse` | `pipeline-step-pulse 2.4s` | Pipeline visualizer |
| `.btn-primary` | — | Legacy orange gradient button |
| `.card-glass` | — | Glass card (legacy `/runs` pages) |

Reduced motion: animations disabled via `@media (prefers-reduced-motion: reduce)`.

## Architecture diagram

```
layout.tsx (font loading)
       │
       ▼
globals.css
  ├── :root / html.dark  → product tokens
  ├── @theme inline      → Tailwind color-* utilities
  └── .product-v2        → marketing mkt-* tokens
       │
       ▼
Components use bg-primary, text-mkt-ink, font-syne, etc.
```

## Key code callouts

- **`globals.css`** — All token definitions and animation keyframes.
- **`lib/product-v2.ts`** — `PRODUCT_V2_CLASS = "product-v2"` applied to product pages.
- **`lib/marketing-v2.ts`** — `isMarketingV2Page()` route detection for marketing chrome.
- **`lib/theme.tsx`** — React context for light/dark toggle (marketing pages).

## Tech decisions

1. **Tailwind v4 CSS-first** — No `tailwind.config.js`; tokens live in CSS for easier theming.
2. **Dual token systems** — Product orange/sand vs marketing indigo keeps brand flexibility.
3. **Syne for display** — Distinctive uppercase headings differentiate from generic SaaS typography.

## Talking points

- Design intent: Command Center aesthetic — near-black base in dark mode, electric orange accent, sand warmth in light mode.
- Product pages force light mode per phase-1b UI revamp; marketing supports dark bands.
- Old `DESIGN.md` (Geist/cream) was removed — it did not match current CSS.
