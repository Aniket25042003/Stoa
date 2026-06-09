-- Phase 2: Competitive Intelligence

create table if not exists public.competitors (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  website_url text,
  pricing_url text,
  content_hash text,
  last_snapshot text,
  last_scanned_at timestamptz,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.competitive_alerts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  competitor_id uuid not null references public.competitors(id) on delete cascade,
  summary text not null,
  severity text not null default 'medium' check (severity in ('low', 'medium', 'high')),
  categories jsonb not null default '[]'::jsonb,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.competitors enable row level security;
alter table public.competitive_alerts enable row level security;

create policy competitors_org on public.competitors for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy competitive_alerts_org on public.competitive_alerts for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());
