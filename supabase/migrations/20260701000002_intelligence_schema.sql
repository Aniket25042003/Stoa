-- Phase 1: Customer / ICP Intelligence

create extension if not exists vector;

create table if not exists public.data_sources (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  source_type text not null check (source_type in ('upload', 'paste', 'hubspot', 'salesforce', 'gong', 'reviews')),
  label text not null,
  status text not null default 'active',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.documents (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  title text not null,
  doc_type text not null check (doc_type in ('call_transcript', 'review', 'crm_export', 'note')),
  content text,
  storage_path text,
  status text not null default 'pending' check (status in ('pending', 'processed', 'failed')),
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ingestion_jobs (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  status text not null default 'queued' check (status in ('queued', 'running', 'completed', 'failed')),
  error text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  finished_at timestamptz
);

create table if not exists public.document_chunks (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  embedding vector(768),
  created_at timestamptz not null default now()
);

create index if not exists idx_document_chunks_embedding on public.document_chunks
  using hnsw (embedding vector_cosine_ops);

create table if not exists public.intelligence (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  document_id uuid references public.documents(id) on delete set null,
  chunk_id uuid references public.document_chunks(id) on delete set null,
  kind text not null check (kind in ('pain_point', 'objection', 'buying_trigger', 'segment', 'win_loss')),
  content text not null,
  confidence float not null default 0.5,
  evidence jsonb not null default '{}'::jsonb,
  version int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists public.icp_profiles (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  version int not null,
  profile jsonb not null default '{}'::jsonb,
  signal_count int not null default 0,
  created_at timestamptz not null default now(),
  unique (org_id, version)
);

create table if not exists public.conversations (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  title text,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.messages (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  conversation_id uuid not null references public.conversations(id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create trigger documents_updated_at before update on public.documents
  for each row execute function public.set_updated_at();
create trigger conversations_updated_at before update on public.conversations
  for each row execute function public.set_updated_at();

-- RLS
alter table public.data_sources enable row level security;
alter table public.documents enable row level security;
alter table public.ingestion_jobs enable row level security;
alter table public.document_chunks enable row level security;
alter table public.intelligence enable row level security;
alter table public.icp_profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;

create policy data_sources_org on public.data_sources for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy documents_org on public.documents for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy ingestion_jobs_org on public.ingestion_jobs for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy document_chunks_org on public.document_chunks for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy intelligence_org on public.intelligence for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy icp_profiles_org on public.icp_profiles for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy conversations_org on public.conversations for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy messages_org on public.messages for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

-- Vector search RPC (service role from workers)
create or replace function public.match_document_chunks(
  p_org_id uuid,
  p_embedding vector(768),
  p_match_count int default 10
)
returns table (
  id uuid,
  document_id uuid,
  content text,
  similarity float
)
language sql
stable
security definer
set search_path = public
as $$
  select
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> p_embedding) as similarity
  from public.document_chunks dc
  where dc.org_id = p_org_id and dc.embedding is not null
  order by dc.embedding <=> p_embedding
  limit p_match_count;
$$;

revoke all on function public.match_document_chunks(uuid, vector, int) from public;
grant execute on function public.match_document_chunks(uuid, vector, int) to service_role;
