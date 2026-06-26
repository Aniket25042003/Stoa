-- Phase 5–6: Campaign analysis + sales–marketing alignment

create table if not exists public.analytics_metric_facts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  connection_id uuid references public.integration_connections(id) on delete set null,
  source text not null check (source in ('ga4', 'posthog')),
  period_start date not null,
  period_end date not null,
  dimension_type text not null check (dimension_type in (
    'channel', 'campaign', 'source_medium', 'landing_page', 'utm_campaign', 'utm_source', 'utm_medium'
  )),
  dimension_value text not null default '',
  metrics jsonb not null default '{}'::jsonb,
  synced_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (org_id, source, period_start, period_end, dimension_type, dimension_value)
);

create index if not exists idx_analytics_metric_facts_org_dim
  on public.analytics_metric_facts(org_id, dimension_type, period_end desc);

alter table public.canonical_contacts add column if not exists lead_source text;
alter table public.canonical_contacts add column if not exists utm_campaign text;
alter table public.canonical_contacts add column if not exists utm_source text;
alter table public.canonical_contacts add column if not exists utm_medium text;

alter table public.canonical_deals add column if not exists lead_source text;
alter table public.canonical_deals add column if not exists utm_campaign text;
alter table public.canonical_deals add column if not exists utm_source text;
alter table public.canonical_deals add column if not exists utm_medium text;

alter table public.precomputed_insights drop constraint if exists precomputed_insights_scope_check;
alter table public.precomputed_insights add constraint precomputed_insights_scope_check
  check (scope in (
    'intelligence', 'dashboard', 'competitive', 'campaigns',
    'campaign_analysis', 'alignment'
  ));

create table if not exists public.deal_stage_snapshots (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  deal_id uuid not null references public.canonical_deals(id) on delete cascade,
  stage text not null,
  entered_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_deal_stage_snapshots_deal
  on public.deal_stage_snapshots(deal_id, entered_at desc);

alter table public.analytics_metric_facts enable row level security;
alter table public.deal_stage_snapshots enable row level security;

do $policy$
declare
  t text;
begin
  foreach t in array array['analytics_metric_facts', 'deal_stage_snapshots']
  loop
    execute format(
      'create policy %I on public.%I for select using (org_id = public.current_org_id())',
      t || '_select', t
    );
    execute format(
      'create policy %I on public.%I for insert with check (org_id = public.current_org_id() and public.has_min_role(''analyst''))',
      t || '_insert', t
    );
    execute format(
      'create policy %I on public.%I for update using (org_id = public.current_org_id() and public.has_min_role(''analyst'')) with check (org_id = public.current_org_id())',
      t || '_update', t
    );
    execute format(
      'create policy %I on public.%I for delete using (org_id = public.current_org_id() and public.has_min_role(''admin''))',
      t || '_delete', t
    );
  end loop;
end
$policy$;
