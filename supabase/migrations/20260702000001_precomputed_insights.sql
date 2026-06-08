-- Phase B1: Precomputed proactive insights

create table if not exists public.precomputed_insights (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  scope text not null check (scope in ('intelligence', 'dashboard', 'competitive', 'campaigns')),
  key text not null,
  title text not null,
  content jsonb not null default '{}'::jsonb,
  citations jsonb not null default '[]'::jsonb,
  version int not null default 1,
  is_stale boolean not null default false,
  source_document_count int not null default 0,
  created_at timestamptz not null default now(),
  unique (org_id, scope, key)
);

create index if not exists idx_precomputed_insights_org_scope
  on public.precomputed_insights(org_id, scope);

alter table public.precomputed_insights enable row level security;

create policy precomputed_insights_org on public.precomputed_insights for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());
