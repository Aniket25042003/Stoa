-- Phase 3: Campaign orchestration

create table if not exists public.campaigns (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  brief text not null,
  brand_voice text,
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed', 'approved')),
  assets jsonb not null default '{}'::jsonb,
  error text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create trigger campaigns_updated_at before update on public.campaigns
  for each row execute function public.set_updated_at();

alter table public.campaigns enable row level security;

create policy campaigns_org on public.campaigns for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());
