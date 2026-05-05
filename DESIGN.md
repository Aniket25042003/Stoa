---
name: GTM Agent
colors:
  cream: "#ffffe3"
  ink: "#4a4a4a"
  slate: "#6d8196"
  mist: "#cbcbcb"
  surface-default: "#ffffe3"
  on-surface-primary: "#4a4a4a"
  on-surface-secondary: "rgba(74, 74, 74, 0.70)"
  on-surface-tertiary: "rgba(74, 74, 74, 0.50)"
  on-surface-muted: "rgba(74, 74, 74, 0.60)"
  accent-primary: "#6d8196"
  on-accent-primary: "#ffffe3"
  border-default: "#cbcbcb"
  border-subtle: "rgba(203, 203, 203, 0.80)"
  border-inverse-subtle: "rgba(203, 203, 203, 0.40)"
  surface-elevated: "rgba(255, 255, 227, 0.90)"
  surface-overlay: "rgba(255, 255, 227, 0.80)"
  surface-scrim: "rgba(255, 255, 227, 0.70)"
  surface-nav-scrolled: "rgba(255, 255, 227, 0.80)"
  surface-nav-top: "rgba(255, 255, 227, 0.40)"
  surface-marquee: "rgba(255, 255, 227, 0.70)"
  surface-card: "rgba(255, 255, 227, 0.95)"
  inverse-surface: "#4a4a4a"
  on-inverse-primary: "#ffffe3"
  on-inverse-secondary: "rgba(255, 255, 227, 0.85)"
  on-inverse-tertiary: "rgba(255, 255, 227, 0.75)"
  on-inverse-muted: "rgba(255, 255, 227, 0.60)"
  on-inverse-label: "rgba(255, 255, 227, 0.50)"
  grid-line: "rgba(203, 203, 203, 0.45)"
  grid-line-strong: "rgba(203, 203, 203, 0.35)"
  gradient-orb-from: "rgba(109, 129, 150, 0.35)"
  gradient-orb-via: "rgba(74, 74, 74, 0.20)"
  gradient-orb-to: "transparent"
  focus-ring: "rgba(109, 129, 150, 0.30)"
  ring-accent-muted: "rgba(109, 129, 150, 0.30)"
  shadow-glow-color: "rgba(109, 129, 150, 0.35)"
typography:
  font-family-sans: "Geist Sans"
  font-family-mono: "Geist Mono"
  display-hero:
    fontFamily: "Geist Sans"
    fontSize: "clamp(3rem, 6vw, 6rem)"
    fontWeight: "600"
    lineHeight: "1.05"
    letterSpacing: "-0.05em"
  headline-section:
    fontFamily: "Geist Sans"
    fontSize: "clamp(2.25rem, 4vw, 3.75rem)"
    fontWeight: "600"
    lineHeight: "1.05"
    letterSpacing: "-0.02em"
  headline-card:
    fontFamily: "Geist Sans"
    fontSize: "1.5rem"
    fontWeight: "500"
    lineHeight: "1.25"
    letterSpacing: "-0.02em"
  title-page:
    fontFamily: "Geist Sans"
    fontSize: "clamp(1.875rem, 3vw, 2.25rem)"
    fontWeight: "600"
    lineHeight: "1.2"
    letterSpacing: "-0.02em"
  body-lead:
    fontFamily: "Geist Sans"
    fontSize: "clamp(1.125rem, 2vw, 1.25rem)"
    fontWeight: "400"
    lineHeight: "1.625"
  body-md:
    fontFamily: "Geist Sans"
    fontSize: "1rem"
    fontWeight: "400"
    lineHeight: "1.75"
  body-sm:
    fontFamily: "Geist Sans"
    fontSize: "0.875rem"
    fontWeight: "400"
    lineHeight: "1.5"
  label-eyebrow:
    fontFamily: "Geist Mono"
    fontSize: "0.75rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.2em"
    textTransform: "uppercase"
  label-eyebrow-wide:
    fontFamily: "Geist Mono"
    fontSize: "0.75rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.28em"
    textTransform: "uppercase"
  label-marquee:
    fontFamily: "Geist Mono"
    fontSize: "0.6875rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.28em"
    textTransform: "uppercase"
  label-pill:
    fontFamily: "Geist Mono"
    fontSize: "0.6875rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.05em"
    textTransform: "uppercase"
  label-badge:
    fontFamily: "Geist Mono"
    fontSize: "0.625rem"
    fontWeight: "400"
    lineHeight: "1"
    letterSpacing: "0.1em"
    textTransform: "uppercase"
  nav-brand:
    fontFamily: "Geist Sans"
    fontSize: "1.125rem"
    fontWeight: "600"
    lineHeight: "1.25"
    letterSpacing: "-0.02em"
spacing:
  unit: 8px
  section-padding-x-mobile: 16px
  section-padding-x-desktop: 24px
  section-y-tight: 32px
  section-y-default: 80px
  section-y-hero-bottom: 112px
  stack-gap-sm: 12px
  stack-gap-md: 16px
  stack-gap-lg: 24px
  stack-gap-xl: 40px
  card-padding: 32px
  card-padding-compact: 20px
  container-max-marketing: "72rem"
  container-max-app: "64rem"
  marquee-gap: 56px
radii:
  sm: "0.5rem"
  md: "0.75rem"
  lg: "1rem"
  full: "9999px"
elevation:
  shadow-sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)"
  shadow-glow: "0 20px 60px -20px rgba(109, 129, 150, 0.35)"
  blur-backdrop-nav: "12px"
  blur-orb: "64px"
motion:
  duration-fast: "150ms"
  duration-base: "300ms"
  duration-reveal: "450ms"
  duration-orb-cycle: "18s"
  duration-marquee: "40s"
  duration-status-pulse: "1.4s"
  easing-nav: "ease"
  easing-reveal: "cubic-bezier(0.22, 1, 0.36, 1)"
  easing-orb: "easeInOut"
  spring-hover:
    stiffness: 260
    damping: 22
  marquee-keyframes:
    name: "horizontal-scroll"
    distance: "50%"
  orb-drift:
    repeat: "infinity"
    ease: "easeInOut"
  reduced-motion-fallback: "respect-user-preference"
grid:
  marketing-columns-feature: 3
  footer-columns: 4
  base-track: 32px
  footer-grid-track: 40px
breakpoints:
  md: "768px"
  lg: "1024px"
components:
  button-primary:
    backgroundColor: "{colors.accent-primary}"
    color: "{colors.on-accent-primary}"
    borderRadius: "{radii.sm}"
    padding: "12px 24px"
    fontWeight: "600"
    fontSize: "0.875rem"
    boxShadow: "{elevation.shadow-glow}"
    hoverOpacity: "0.9"
  button-secondary:
    backgroundColor: "{colors.surface-overlay}"
    color: "{colors.on-surface-primary}"
    border: "1px solid {colors.border-default}"
    borderRadius: "{radii.sm}"
    padding: "12px 24px"
    fontWeight: "600"
    fontSize: "0.875rem"
  button-ghost-inverse:
    backgroundColor: "transparent"
    color: "{colors.on-inverse-primary}"
    border: "1px solid {colors.border-default}"
    borderRadius: "{radii.sm}"
    padding: "8px 12px"
    fontWeight: "600"
    fontSize: "0.875rem"
  card-feature:
    backgroundColor: "{colors.surface-elevated}"
    border: "1px solid {colors.border-subtle}"
    borderRadius: "{radii.lg}"
    padding: "{spacing.card-padding}"
    hoverLift: "-4px"
    hoverShadow: "{elevation.shadow-glow}"
  card-run:
    backgroundColor: "{colors.surface-card}"
    border: "1px solid {colors.border-default}"
    borderRadius: "{radii.lg}"
    padding: "{spacing.card-padding-compact}"
    hoverLift: "-2px"
    hoverShadow: "{elevation.shadow-glow}"
  card-pricing-highlight:
    border: "1px solid {colors.accent-primary}"
    ring: "2px solid {colors.ring-accent-muted}"
    boxShadow: "{elevation.shadow-glow}"
  navbar:
    position: "sticky"
    blur: "{elevation.blur-backdrop-nav}"
    borderBottomScrolled: "1px solid {colors.border-subtle}"
    backgroundScrolled: "{colors.surface-nav-scrolled}"
    backgroundTop: "{colors.surface-nav-top}"
  status-pill:
    borderRadius: "{radii.full}"
    border: "1px solid {colors.border-default}"
    backgroundColor: "{colors.surface-default}"
    padding: "4px 12px"
    typography: "{typography.label-pill}"
  link-nav:
    fontSize: "0.875rem"
    fontWeight: "500"
    color: "rgba(74, 74, 74, 0.80)"
    underlineHover: "{colors.accent-primary}"
  eyebrow-section:
    typography: "{typography.label-eyebrow}"
    color: "{colors.accent-primary}"
---

## Brand & style

GTM Agent presents an **approachable, founder-centric SaaS** aesthetic: warm paper-like surfaces, soft charcoal type, and a single cool **slate blue** accent so actions and technical labels feel precise without corporate coldness. The product markets **autonomous multi-agent workflows**; the UI balances that complexity with **airy whitespace**, restrained borders, and **monospace micro-labels** (eyebrows, stack names, run IDs) that signal “tooling you can trust.” Motion is **calm and springy**—cards lift slightly on hover, a hero gradient orb drifts slowly, and scroll reveals ease in with a premium easing curve—while respecting reduced-motion preferences.

The emotional target is **confident clarity**: not flashy glassmorphism, but a **studio workspace** on warm cream paper with light grid texture and occasional deep-ink bands for contrast.

## Colors

The palette is intentionally narrow:

- **Cream (`#ffffe3`)** is the default canvas—a warm, slightly yellow off-white that reduces harsh contrast versus pure white and pairs with ink text for a soft editorial feel.
- **Ink (`#4a4a4a`)** is primary text: not black, to stay gentle on long reading sessions.
- **Slate (`#6d8196`)** is the **primary interactive accent**: buttons, icon tint, link underlines, focus-adjacent emphasis, and the soft glow in shadows. It reads as a muted blue-gray “instrument” color.
- **Mist (`#cbcbcb`)** defines structure: card borders, pills, dividers, and grid lines. Many borders use **mist at reduced opacity** so surfaces feel layered without heavy chrome.

**Inverse surfaces** (footer, dark marketing bands) flip to **ink background** with **cream typography** and mist-toned dividers at low opacity. Gradients in the hero use **transparent washes** of slate and ink behind heavy blur so the page feels alive without competing with typography.

Opacity steps on ink (`70%`, `60%`, `50%`) handle secondary copy, captions, and de-emphasized metadata. Accent text on cream buttons uses the cream hex for maximum clarity against slate fills.

## Typography

**Geist Sans** carries almost all UI and marketing prose: semibold **display** sizes for hero and section titles with **tight tracking**, medium weights for card titles, regular for body. **Geist Mono** is reserved for **system-like labels**: uppercase eyebrows with **wide letter-spacing** (0.2em–0.28em), marquee tech tags, run IDs, status pills, and footer meta—reinforcing “pipeline / agent” semantics.

Hierarchy is established by **size jumps** (hero → section headline → card title → body) and by **tracking**: display lines use **negative tracking** for a modern editorial poster look; mono labels use **positive tracking** for legibility at small sizes. Body leads use relaxed line height (~1.6) for scan-friendly paragraphs on marketing pages.

## Layout & spacing

Content lives in **centered max-width columns**: a wider rail for marketing storytelling, a slightly narrower one for signed-in app views so dense run data does not sprawl. Horizontal padding steps from **16px** on small screens to **24px** on medium and up. Vertical rhythm stacks **sections** with generous **80px+** padding between major blocks; within cards, **32px** padding is common.

Grids are simple: **three-column** feature rows at desktop, collapsing to a single column. The optional background **grid graphic** uses a **32px** (marketing) or **40px** (footer) square grid with faint mist lines and a **radial mask** that fades the grid toward the edges so the center stays readable.

## Elevation & depth

Depth is **subtle and warm**, not Material-style harsh shadows:

- Default cards use **light border + slight translucency** (`cream` at ~90–95% opacity) over the base cream body.
- **Primary elevation** is the custom **glow shadow**: a large, soft, slate-tinted shadow (`0 20px 60px -20px` at ~35% slate opacity) applied to primary CTAs, featured pricing, and hover states on cards—reading as a **diffuse lift** rather than a drop shadow.
- **Navigation** uses **backdrop blur** plus semi-transparent cream when the user scrolls, with a mist border fading in—glass-light, not opaque bars.

No harsh black shadows; separation relies on **mist borders** and **translucent surfaces**.

## Motion

Interaction timing favors **300ms** for navigation chrome, **450ms** for scroll-triggered reveals with a **cubic-bezier(0.22, 1, 0.36, 1)** ease (snappy deceleration). Hover lifts on cards use a **spring** (high stiffness, moderate damping) so motion feels physical. The hero **ambient orb** animates position over **~18s** with ease-in-out repetition for a breathing background. A **marquee** band scrolls tech names over **40s** linearly; status dots for active runs **pulse opacity and scale** on a **~1.4s** loop. All decorative motion should honor **prefers-reduced-motion** by disabling or simplifying animation.

## Shapes

Corners are **rounded but not pill-shaped** for main surfaces: **8px** (`0.5rem`) for buttons and small controls, **12px** (`0.75rem`) for nested icon holders, **16px** (`1rem`) for cards and panels. **Pills** use **full radius** for status chips and badges. Primary actions are **rectangular with rounded corners**, not fully rounded pills—keeping a slightly serious B2B posture.

## Components

**Primary buttons** are slate-filled with cream label text and the glow shadow; hover reduces opacity rather than shifting hue.**Secondary buttons** are cream-tinted fills with a mist outline.**Cards** combine mist borders, elevated cream fill, and on hover: slight translate up plus the glow shadow (or spring-hover on featured motion surfaces).**Pricing highlights** add a slate border, soft ring, and glow shadow for the recommended tier.**Navigation links** use an animated **slate underline** growing from the left.**Eyebrows** always use mono caps + slate color.**Run rows and pills** lean on mono IDs and uppercase status to align with the “operations dashboard” metaphor without becoming dark-mode terminal chrome.

Together, tokens and patterns describe a **single coherent product**: warm studio paper, one trustworthy accent, monospace telemetry labels, and soft elevation that whispers rather than shouts.
