-- Phase 1d: Customer data integrations — connections, canonical entities, sync runs

-- Extend data_sources source_type values
alter table public.data_sources drop constraint if exists data_sources_source_type_check;
alter table public.data_sources add constraint data_sources_source_type_check
  check (source_type in (
    'upload', 'paste', 'hubspot', 'salesforce', 'gong', 'reviews',
    'zendesk', 'intercom', 'csv_structured', 'slack', 'notion',
    'google_drive', 'jira', 'posthog', 'ga4', 'reddit'
  ));

create table if not exists public.integration_connections (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  provider text not null check (provider in (
    'hubspot', 'salesforce', 'gong', 'zendesk', 'intercom', 'reviews',
    'csv_structured', 'slack', 'notion', 'google_drive', 'jira', 'posthog', 'ga4', 'reddit'
  )),
  status text not null default 'pending' check (status in ('pending', 'active', 'error', 'revoked')),
  label text not null default '',
  credentials_encrypted text,
  provider_metadata jsonb not null default '{}'::jsonb,
  scopes text[] not null default '{}',
  token_expires_at timestamptz,
  last_sync_at timestamptz,
  sync_cursor jsonb not null default '{}'::jsonb,
  last_error text,
  data_source_id uuid references public.data_sources(id) on delete set null,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, provider)
);

create index if not exists idx_integration_connections_org on public.integration_connections(org_id);

create table if not exists public.integration_sync_runs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  connection_id uuid not null references public.integration_connections(id) on delete cascade,
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  records_fetched int not null default 0,
  records_written int not null default 0,
  error text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_integration_sync_runs_connection on public.integration_sync_runs(connection_id, created_at desc);

create table if not exists public.canonical_accounts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  external_source text not null,
  external_id text not null,
  name text,
  domain text,
  industry text,
  employee_count_range text,
  annual_revenue numeric,
  country text,
  lifecycle_stage text,
  raw_properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, external_source, external_id)
);

create index if not exists idx_canonical_accounts_org on public.canonical_accounts(org_id);

create table if not exists public.canonical_contacts (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  account_id uuid references public.canonical_accounts(id) on delete set null,
  external_source text not null,
  external_id text not null,
  email text,
  name text,
  title text,
  department text,
  persona_tags text[] not null default '{}',
  raw_properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, external_source, external_id)
);

create index if not exists idx_canonical_contacts_org on public.canonical_contacts(org_id);
create index if not exists idx_canonical_contacts_account on public.canonical_contacts(account_id);

create table if not exists public.canonical_deals (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  account_id uuid references public.canonical_accounts(id) on delete set null,
  external_source text not null,
  external_id text not null,
  name text,
  amount numeric,
  currency text default 'USD',
  stage text,
  pipeline text,
  close_date date,
  is_won boolean,
  is_closed boolean,
  loss_reason text,
  owner_name text,
  raw_properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, external_source, external_id)
);

create index if not exists idx_canonical_deals_org on public.canonical_deals(org_id);
create index if not exists idx_canonical_deals_account on public.canonical_deals(account_id);

create table if not exists public.canonical_interactions (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  interaction_type text not null check (interaction_type in (
    'call_transcript', 'support_ticket', 'review', 'note', 'email', 'meeting'
  )),
  account_id uuid references public.canonical_accounts(id) on delete set null,
  contact_id uuid references public.canonical_contacts(id) on delete set null,
  deal_id uuid references public.canonical_deals(id) on delete set null,
  external_source text not null,
  external_id text not null,
  occurred_at timestamptz,
  title text,
  body_text text,
  participants jsonb not null default '[]'::jsonb,
  sentiment text,
  raw_properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, external_source, external_id)
);

create index if not exists idx_canonical_interactions_org on public.canonical_interactions(org_id);
create index if not exists idx_canonical_interactions_type on public.canonical_interactions(org_id, interaction_type);

-- Link intelligence signals to canonical interactions
alter table public.intelligence add column if not exists interaction_id uuid
  references public.canonical_interactions(id) on delete set null;
alter table public.intelligence add column if not exists source_type text;

create trigger integration_connections_updated_at before update on public.integration_connections
  for each row execute function public.set_updated_at();
create trigger canonical_accounts_updated_at before update on public.canonical_accounts
  for each row execute function public.set_updated_at();
create trigger canonical_contacts_updated_at before update on public.canonical_contacts
  for each row execute function public.set_updated_at();
create trigger canonical_deals_updated_at before update on public.canonical_deals
  for each row execute function public.set_updated_at();
create trigger canonical_interactions_updated_at before update on public.canonical_interactions
  for each row execute function public.set_updated_at();

-- RLS
alter table public.integration_connections enable row level security;
alter table public.integration_sync_runs enable row level security;
alter table public.canonical_accounts enable row level security;
alter table public.canonical_contacts enable row level security;
alter table public.canonical_deals enable row level security;
alter table public.canonical_interactions enable row level security;

do $policy$
declare
  t text;
begin
  foreach t in array array[
    'integration_connections', 'integration_sync_runs',
    'canonical_accounts', 'canonical_contacts', 'canonical_deals', 'canonical_interactions'
  ]
  loop
    execute format('create policy %I on public.%I for select using (org_id = public.current_org_id())', t || '_select', t);
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
