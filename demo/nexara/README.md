# Stoa Demo Workspace

Fictional B2B marketing analytics company **Stoa** (demo customer) — seeded for product videos and sales demos.

## Quick start

```bash
# From repo root — requires SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in .env
# and OPENAI_API_KEY or Vertex for embeddings/precompute
python scripts/seed_demo_org.py

# Re-seed existing workspace (idempotent)
python scripts/seed_demo_org.py --reuse

# Staging
python scripts/seed_demo_org.py --env-file .env.staging --reuse

# Relational data only (no embeddings / LLM precompute)
python scripts/seed_demo_org.py --skip-embeddings
```

## Login credentials

| Field | Default |
|-------|---------|
| Email | `demo@stoa.demo` |
| Password | `StoaDemo2026!` |
| Org | Stoa (`stoa-demo` slug) |

Override with `DEMO_USER_EMAIL` and `DEMO_USER_PASSWORD`.

## What gets seeded

- **Org profile** — ICP, goals, brand voice, competitor notes
- **9 documents** — call transcripts, G2 reviews, CRM export, battlecard, ICP one-pager
- **7 knowledge chunks** — ICP, competitive snapshots, campaign assets, GA4 summary, agent evidence
- **CRM** — 8 accounts, 10 contacts, 12 deals, 6 interactions
- **Integrations** — HubSpot + Gong (fresh), GA4 (stale) mock connections
- **Competitive** — InsightLoop, PipelineIQ, RevTrack + 6 alerts
- **Campaigns** — completed Q3 launch, running webinar nurture, failed partner, queued displacement
- **Content** — 12 assets (mixed status for bottleneck demo)
- **Analytics** — channel + UTM metrics for campaign analysis
- **Precomputed insights** — intelligence, dashboard, campaign_analysis, alignment (requires LLM)

## Video script

See [docs/demo/VIDEO_SCRIPT.md](../../docs/demo/VIDEO_SCRIPT.md) for suggested questions and scenes.

## File layout

```
demo/nexara/
  manifest.yaml      # Structured seed data
  documents/         # Markdown files → documents + intelligence
  knowledge/         # Long-form KB chunks
```
