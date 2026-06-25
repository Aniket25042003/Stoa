# V3 Design Theme

Single source of truth for Marketing V3 and Product V3 styling in `apps/web`.

## Surfaces


| Surface                         | Wrapper         | Components                                       |
| ------------------------------- | --------------- | ------------------------------------------------ |
| Marketing (`/`, `/waitlist`)    | `.marketing-v2` | `components/marketing/v3/*`                      |
| Product (auth, onboarding, app) | `.product-v2`   | `components/product/*`, `components/app-shell/*` |


## Color tokens (`globals.css`)


| Token                    | Value              | Use                 |
| ------------------------ | ------------------ | ------------------- |
| `--mkt-surface`          | `#F9F8F6`          | Page canvas         |
| `--mkt-surface-elevated` | `#FFFFFF`          | Cards, inputs       |
| `--mkt-ink`              | `#0A0A0A`          | Primary text        |
| `--mkt-ink-secondary`    | `#8A8A8A`          | Headline secondary  |
| `--mkt-muted`            | `#6B6B6B`          | Body secondary      |
| `--mkt-subtle`           | `#B0B0B0`          | Eyebrows, hints     |
| `--mkt-border`           | `rgba(0,0,0,0.08)` | Borders             |
| `--mkt-accent`           | `#0A0A0A`          | Primary CTA (black) |
| `--mkt-dark-band`        | `#141414`          | Dark sections       |
| `--mkt-dark-ink`         | `#F5F5F5`          | Text on dark band   |


## Marketing utilities

- `.mkt-section-pad` / `.mkt-section-pad-hero` — vertical rhythm
- `.mkt-solid-btn`, `.mkt-glass-btn` — pill CTAs
- `.mkt-pastel-card`, `.mkt-mini-card` — feature/pricing cards
- `.mkt-section-bg-*` — section backdrops (hero, dark, dots, warm, cta)
- `StretchedHeroGrid` — hero-only angled grid with vertical fade

## Product V3 rules

**Use:** `mkt-`* tokens, `ProductCard`, `ProductButton`, `ProductInput`, Syne uppercase page headers, `rounded-sm` density.

**Do not use in product:** pastel section cards, `StretchedHeroGrid`, indigo/orange MD3 tokens (`.btn-primary`, `.card-glass`, `--primary`).

**Deprecated (legacy MD3/sand):** `--surface`, `--primary`, `.btn-primary`, `.card-glass` — do not add new usages.

## Manual QA checklist

- [x] Landing: grid fade, anchors, FAQ, pricing toggle (desktop + mobile)
- [x] Waitlist: submit success/error
- [x] Login → onboarding → processing → dashboard
- [x] Data profile save; integrations UI
- [x] Intelligence SSE ask
- [x] Prelaunch prod: only `/`, `/waitlist` public; auth redirects to waitlist