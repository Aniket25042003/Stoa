-- Nexara company onboarding, active GTM plans, and company-scoped GTM chat.

alter table public.companies
  add column if not exists website_url text,
  add column if not exists industry text,
  add column if not exists target_customers text,
  add column if not exists geography text,
  add column if not exists business_model text,
  add column if not exists stage text,
  add column if not exists goals text[] not null default '{}',
  add column if not exists known_competitors text[] not null default '{}',
  add column if not exists constraints text[] not null default '{}',
  add column if not exists onboarding_completed_at timestamptz;

create table if not exists public.company_gtm_plans (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  source text not null check (source in ('generated', 'uploaded')),
  title text not null default 'GTM plan',
  content_markdown text not null default '',
  content_json jsonb not null default '{}',
  source_run_id uuid references public.gtm_runs (id) on delete set null,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_company_gtm_plans_company_active
  on public.company_gtm_plans (company_id, is_active, updated_at desc);

create unique index if not exists idx_company_gtm_plans_one_active
  on public.company_gtm_plans (company_id)
  where is_active;

drop trigger if exists trg_company_gtm_plans_updated on public.company_gtm_plans;
create trigger trg_company_gtm_plans_updated
before update on public.company_gtm_plans
for each row execute function public.set_updated_at();

create table if not exists public.gtm_plan_messages (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  plan_id uuid references public.company_gtm_plans (id) on delete set null,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null default '',
  parts jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_gtm_plan_messages_company_created
  on public.gtm_plan_messages (company_id, created_at);

alter table public.company_gtm_plans enable row level security;
alter table public.gtm_plan_messages enable row level security;

create policy "company_gtm_plans_select_own" on public.company_gtm_plans
  for select using (
    exists (select 1 from public.companies c where c.id = company_gtm_plans.company_id and c.user_id = auth.uid())
  );

create policy "company_gtm_plans_all_own" on public.company_gtm_plans
  for all using (
    exists (select 1 from public.companies c where c.id = company_gtm_plans.company_id and c.user_id = auth.uid())
  )
  with check (
    exists (select 1 from public.companies c where c.id = company_gtm_plans.company_id and c.user_id = auth.uid())
  );

create policy "gtm_plan_messages_select_own" on public.gtm_plan_messages
  for select using (
    exists (select 1 from public.companies c where c.id = gtm_plan_messages.company_id and c.user_id = auth.uid())
  );

create policy "gtm_plan_messages_all_own" on public.gtm_plan_messages
  for all using (
    exists (select 1 from public.companies c where c.id = gtm_plan_messages.company_id and c.user_id = auth.uid())
  )
  with check (
    exists (select 1 from public.companies c where c.id = gtm_plan_messages.company_id and c.user_id = auth.uid())
  );
