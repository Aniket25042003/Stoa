#!/usr/bin/env bash
# Split wip/save-all-changes into stacked feature branches from main.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
WIP="wip/save-all-changes"
MAIN="main"

checkout_from_wip() {
  local branch="$1"
  shift
  git checkout "$MAIN" -q
  git branch -D "$branch" 2>/dev/null || true
  git checkout -b "$branch" -q
  if [ "$#" -gt 0 ]; then
    git checkout "$WIP" -- "$@"
  fi
}

commit_if_changes() {
  local msg="$1"
  if git diff --cached --quiet && git diff --quiet; then
    echo "  (no changes for: $msg)"
    return 0
  fi
  git add -A
  git reset HEAD supabase/.temp/cli-latest 2>/dev/null || true
  git commit -m "$msg"
}

echo "=== PR1: monorepo foundations ==="
checkout_from_wip chore/monorepo-foundations \
  AGENTS.md .pre-commit-config.yaml README.md docs/ legacy/
commit_if_changes "chore: add agent docs, ADRs, and archive legacy GTM stack.

Move superseded agents, API, MCP, and migrations under legacy/ for reference.
Add AGENTS.md as the single source of truth for phased delivery."

echo "=== PR2: supabase greenfield schema ==="
git checkout chore/monorepo-foundations -q
git checkout -B feat/supabase-greenfield-schema -q
git checkout "$WIP" -- \
  supabase/migrations/20260701000000_reset_legacy_schema.sql \
  supabase/migrations/20260701000001_baseline_tenancy.sql \
  supabase/migrations/20260701000002_intelligence_schema.sql \
  supabase/migrations/20260701000003_competitive_schema.sql \
  supabase/migrations/20260701000004_campaigns_schema.sql \
  supabase/migrations/20260702000000_org_profile.sql \
  supabase/migrations/20260702000001_precomputed_insights.sql \
  supabase/migrations/20260703000000_knowledge_base.sql
commit_if_changes "feat(db): add greenfield Supabase schema for marketing intelligence.

Tenancy, intelligence, competitive, campaigns, org profile, insights, and knowledge base."

echo "=== PR3: stoa_core ==="
git checkout feat/supabase-greenfield-schema -q
git checkout -B feat/stoa-core -q
git checkout "$WIP" -- services/core/ services/worker/
commit_if_changes "feat(core): add stoa_core shared library and worker deps.

Config, LLM router, ingestion, RAG, Redis/SSE, security helpers, and Celery worker requirements."

echo "=== PR4: API platform ==="
git checkout feat/stoa-core -q
git checkout -B feat/api-platform -q
git checkout "$WIP" -- services/api/
commit_if_changes "feat(api): replace GTM API with marketing intelligence platform.

FastAPI routers, Celery tasks, JWT auth, org RBAC, ingestion, intelligence,
competitive, campaigns, and security hardening."

echo "=== PR5: supabase RLS security ==="
git checkout feat/api-platform -q
git checkout -B security/supabase-rls-storage -q
git checkout "$WIP" -- \
  supabase/migrations/20260704000000_rbac_rls_hardening.sql \
  supabase/migrations/20260704000001_storage_policies.sql
commit_if_changes "security(db): add role-aware RLS and storage bucket policies.

Viewers read-only via PostgREST; analysts write; admins delete. Harden waitlist inserts."

echo "=== PR6: web product workspaces ==="
git checkout security/supabase-rls-storage -q
git checkout -B feat/web-product-workspaces -q
git checkout "$WIP" -- \
  apps/web/src/app/\(app\)/campaigns/ \
  apps/web/src/app/\(app\)/competitive/ \
  apps/web/src/app/\(app\)/data/ \
  apps/web/src/app/\(app\)/intelligence/ \
  apps/web/src/app/\(app\)/dashboard/dashboard-workspace.tsx \
  apps/web/src/app/\(app\)/dashboard/page.tsx \
  apps/web/src/app/\(app\)/onboarding/ \
  apps/web/src/app/\(app\)/gtm/page.tsx \
  apps/web/src/app/\(app\)/marketing/page.tsx \
  apps/web/src/components/app-shell/CompleteDataPrompt.tsx \
  apps/web/src/lib/auth-entry.ts \
  apps/web/src/lib/sse.ts \
  apps/web/src/app/\(app\)/companies-load-error.tsx
commit_if_changes "feat(web): add intelligence product workspaces and navigation.

Dashboard, data hub, intelligence, competitive, campaigns, and onboarding flows."

echo "=== PR7: web security hardening ==="
git checkout feat/web-product-workspaces -q
git checkout -B security/web-auth-proxy -q
git checkout "$WIP" -- \
  apps/web/src/middleware.ts \
  apps/web/src/app/auth/callback/auth-callback-client.tsx \
  apps/web/src/lib/api.ts \
  apps/web/src/lib/safe-url.ts \
  apps/web/src/lib/supabase/admin.ts \
  apps/web/src/app/api/backend/ \
  apps/web/src/app/api/waitlist/ \
  apps/web/src/app/api/companies/route.ts \
  apps/web/src/app/waitlist/page.tsx \
  apps/web/next.config.ts \
  apps/web/.env.example \
  apps/web/src/app/\(app\)/layout.tsx \
  apps/web/src/components/app-shell/AppHeader.tsx \
  apps/web/src/app/\(app\)/runs/ \
  apps/web/src/app/\(app\)/gtm/gtm-workspace.tsx \
  apps/web/src/app/\(app\)/marketing/ \
  apps/web/src/components/app-shell/CompanySwitcher.tsx \
  apps/web/src/app/login/page.tsx
commit_if_changes "security(web): add auth gate, BFF proxy, and safe URL handling.

Middleware protects app routes; JWT stays server-side via /api/backend; fix open redirects."

echo "=== PR8: infra CI deploy ==="
git checkout security/web-auth-proxy -q
git checkout -B chore/ci-infra-deploy -q
git checkout "$WIP" -- \
  .github/workflows/ci.yml \
  render.yaml \
  docker-compose.yml \
  services/api/.env.example \
  apps/web/src/app/\(marketing\)/ \
  apps/web/src/components/marketing/
commit_if_changes "chore(infra): add CI security scanning and production deploy config.

Gitleaks, dependency audits, Redis AUTH locally, Render TLS and STOA_ENV."

echo "Done. Branches:"
git branch --list 'chore/*' 'feat/*' 'security/*' | grep -v wip
