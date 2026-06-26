-- Agent memory enrichment job tracking

create table if not exists public.enrichment_jobs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  job_type text not null check (job_type in (
    'company_enrichment',
    'competitor_enrichment',
    'competitor_rescan',
    'conversation_checkpoint',
    'crm_summary',
    'review_themes'
  )),
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  target_type text,
  target_id uuid,
  payload jsonb not null default '{}'::jsonb,
  result_summary jsonb not null default '{}'::jsonb,
  error text,
  idempotency_key text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create unique index if not exists idx_enrichment_jobs_idempotency
  on public.enrichment_jobs (org_id, idempotency_key)
  where idempotency_key is not null and status in ('queued', 'running');

create index if not exists idx_enrichment_jobs_org_status
  on public.enrichment_jobs (org_id, status, created_at desc);

create trigger enrichment_jobs_updated_at
  before update on public.enrichment_jobs
  for each row execute function public.set_updated_at();

alter table public.enrichment_jobs enable row level security;

create policy enrichment_jobs_select on public.enrichment_jobs for select
  using (public.is_org_member(org_id));

create policy enrichment_jobs_insert on public.enrichment_jobs for insert
  with check (public.has_permission_in_org(org_id, 'documents:write'));

create policy enrichment_jobs_update on public.enrichment_jobs for update
  using (public.has_permission_in_org(org_id, 'documents:write'))
  with check (public.is_org_member(org_id));

create policy enrichment_jobs_delete on public.enrichment_jobs for delete
  using (public.has_permission_in_org(org_id, 'documents:delete'));
