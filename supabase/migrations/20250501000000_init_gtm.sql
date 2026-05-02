-- GTM Agent core schema + RLS
-- See AGENT.md for semantics

create extension if not exists "uuid-ossp";

create table if not exists public.gtm_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  status text not null default 'awaiting_plan_approval' check (status in ('awaiting_plan_approval', 'queued', 'running', 'completed', 'failed')),
  run_input jsonb not null default '{}',
  master_plan jsonb not null default '{}',
  plan_feedback text,
  plan_approved_at timestamptz,
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_tasks (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.gtm_runs (id) on delete cascade,
  agent_name text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'completed', 'failed')),
  payload jsonb not null default '{}',
  result jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.research_sources (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.gtm_runs (id) on delete cascade,
  source_type text not null check (source_type in ('reddit', 'x', 'web', 'serp', 'other')),
  source_url text,
  title text,
  excerpt text,
  metadata jsonb not null default '{}',
  retrieved_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists public.agent_artifacts (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.gtm_runs (id) on delete cascade,
  artifact_type text not null,
  content jsonb not null default '{}',
  version int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists public.run_events (
  id bigserial primary key,
  run_id uuid not null references public.gtm_runs (id) on delete cascade,
  event_type text not null,
  payload jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_gtm_runs_user_created on public.gtm_runs (user_id, created_at desc);
create index if not exists idx_agent_tasks_run on public.agent_tasks (run_id);
create index if not exists idx_research_sources_run on public.research_sources (run_id);
create index if not exists idx_run_events_run on public.run_events (run_id, id);

create table if not exists public.gtm_reports (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references public.gtm_runs (id) on delete cascade,
  markdown text not null,
  version int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists public.report_exports (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.gtm_reports (id) on delete cascade,
  format text not null default 'pdf',
  storage_path text,
  created_at timestamptz not null default now()
);

create index if not exists idx_gtm_reports_run on public.gtm_reports (run_id, version desc);

-- updated_at trigger
create or replace function public.set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_gtm_runs_updated on public.gtm_runs;
create trigger trg_gtm_runs_updated
before update on public.gtm_runs
for each row execute function public.set_updated_at();

-- RLS
alter table public.gtm_runs enable row level security;
alter table public.agent_tasks enable row level security;
alter table public.research_sources enable row level security;
alter table public.agent_artifacts enable row level security;
alter table public.run_events enable row level security;
alter table public.gtm_reports enable row level security;
alter table public.report_exports enable row level security;

-- Policies: owners only (JWT auth.uid())
create policy "gtm_runs_select_own" on public.gtm_runs
  for select using (auth.uid() = user_id);
create policy "gtm_runs_insert_own" on public.gtm_runs
  for insert with check (auth.uid() = user_id);
create policy "gtm_runs_update_own" on public.gtm_runs
  for update using (auth.uid() = user_id);

create policy "agent_tasks_select_own" on public.agent_tasks
  for select using (
    exists (select 1 from public.gtm_runs r where r.id = agent_tasks.run_id and r.user_id = auth.uid())
  );
create policy "agent_tasks_all_own" on public.agent_tasks
  for all using (
    exists (select 1 from public.gtm_runs r where r.id = agent_tasks.run_id and r.user_id = auth.uid())
  );

create policy "research_sources_select_own" on public.research_sources
  for select using (
    exists (select 1 from public.gtm_runs r where r.id = research_sources.run_id and r.user_id = auth.uid())
  );
create policy "research_sources_all_own" on public.research_sources
  for all using (
    exists (select 1 from public.gtm_runs r where r.id = research_sources.run_id and r.user_id = auth.uid())
  );

create policy "agent_artifacts_select_own" on public.agent_artifacts
  for select using (
    exists (select 1 from public.gtm_runs r where r.id = agent_artifacts.run_id and r.user_id = auth.uid())
  );
create policy "agent_artifacts_all_own" on public.agent_artifacts
  for all using (
    exists (select 1 from public.gtm_runs r where r.id = agent_artifacts.run_id and r.user_id = auth.uid())
  );

create policy "run_events_select_own" on public.run_events
  for select using (
    exists (select 1 from public.gtm_runs r where r.id = run_events.run_id and r.user_id = auth.uid())
  );
create policy "run_events_all_own" on public.run_events
  for all using (
    exists (select 1 from public.gtm_runs r where r.id = run_events.run_id and r.user_id = auth.uid())
  );

create policy "gtm_reports_select_own" on public.gtm_reports
  for select using (
    exists (select 1 from public.gtm_runs r where r.id = gtm_reports.run_id and r.user_id = auth.uid())
  );
create policy "gtm_reports_all_own" on public.gtm_reports
  for all using (
    exists (select 1 from public.gtm_runs r where r.id = gtm_reports.run_id and r.user_id = auth.uid())
  );

create policy "report_exports_select_own" on public.report_exports
  for select using (
    exists (
      select 1 from public.gtm_reports rep
      join public.gtm_runs r on r.id = rep.run_id
      where rep.id = report_exports.report_id and r.user_id = auth.uid()
    )
  );
create policy "report_exports_all_own" on public.report_exports
  for all using (
    exists (
      select 1 from public.gtm_reports rep
      join public.gtm_runs r on r.id = rep.run_id
      where rep.id = report_exports.report_id and r.user_id = auth.uid()
    )
  );
