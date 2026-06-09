-- Company workspace, shared KB (pgvector), marketing chat, GTM company link
-- See AGENT.md / marketing plan

create extension if not exists vector;

-- ---------------------------------------------------------------------------
-- companies
-- ---------------------------------------------------------------------------
create table if not exists public.companies (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  name text not null,
  description text,
  brand_voice jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_companies_user_created on public.companies (user_id, created_at desc);

drop trigger if exists trg_companies_updated on public.companies;
create trigger trg_companies_updated
before update on public.companies
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- gtm_runs.company_id (nullable for legacy rows)
-- ---------------------------------------------------------------------------
alter table public.gtm_runs
  add column if not exists company_id uuid references public.companies (id) on delete set null;

create index if not exists idx_gtm_runs_company on public.gtm_runs (company_id);

-- ---------------------------------------------------------------------------
-- marketing_chats (before company_knowledge.source_chat_id FK)
-- ---------------------------------------------------------------------------
create table if not exists public.marketing_chats (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  company_id uuid not null references public.companies (id) on delete cascade,
  title text not null default 'Marketing chat',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_marketing_chats_company on public.marketing_chats (company_id, created_at desc);

drop trigger if exists trg_marketing_chats_updated on public.marketing_chats;
create trigger trg_marketing_chats_updated
before update on public.marketing_chats
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- company_knowledge (768-dim for Vertex text-embedding-004)
-- ---------------------------------------------------------------------------
create table if not exists public.company_knowledge (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  kind text not null check (
    kind in (
      'competitor', 'positioning', 'icp', 'channel', 'learning',
      'asset_outcome', 'brand_decision', 'risk', 'other'
    )
  ),
  title text not null default '',
  content text not null default '',
  embedding vector(768),
  source_system text check (source_system in ('gtm', 'marketing')),
  source_run_id uuid references public.gtm_runs (id) on delete set null,
  source_chat_id uuid references public.marketing_chats (id) on delete set null,
  tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_company_knowledge_company on public.company_knowledge (company_id, kind);
create index if not exists idx_company_knowledge_tags on public.company_knowledge using gin (tags);

-- HNSW only on rows with embeddings (avoids null issues)
drop index if exists idx_company_knowledge_embedding;
create index if not exists idx_company_knowledge_embedding
  on public.company_knowledge
  using hnsw (embedding vector_cosine_ops)
  with (m = 16, ef_construction = 64)
  where (embedding is not null);

-- ---------------------------------------------------------------------------
-- company_competitors
-- ---------------------------------------------------------------------------
create table if not exists public.company_competitors (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  name text not null,
  url text,
  positioning text,
  channels jsonb not null default '{}',
  ad_examples jsonb not null default '[]',
  knowledge_id uuid references public.company_knowledge (id) on delete set null,
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_company_competitors_company on public.company_competitors (company_id);

drop trigger if exists trg_company_competitors_updated on public.company_competitors;
create trigger trg_company_competitors_updated
before update on public.company_competitors
for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- marketing_messages
-- ---------------------------------------------------------------------------
create table if not exists public.marketing_messages (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid not null references public.marketing_chats (id) on delete cascade,
  role text not null check (role in ('user', 'assistant', 'system', 'tool')),
  agent text,
  content text not null default '',
  parts jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_marketing_messages_chat on public.marketing_messages (chat_id, created_at);

-- ---------------------------------------------------------------------------
-- marketing_tasks
-- ---------------------------------------------------------------------------
create table if not exists public.marketing_tasks (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid not null references public.marketing_chats (id) on delete cascade,
  message_id uuid references public.marketing_messages (id) on delete set null,
  agent_name text not null,
  status text not null default 'pending' check (status in ('pending', 'running', 'completed', 'failed')),
  payload jsonb not null default '{}',
  result jsonb,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_marketing_tasks_chat on public.marketing_tasks (chat_id);

-- ---------------------------------------------------------------------------
-- marketing_artifacts
-- ---------------------------------------------------------------------------
create table if not exists public.marketing_artifacts (
  id uuid primary key default gen_random_uuid(),
  chat_id uuid not null references public.marketing_chats (id) on delete cascade,
  task_id uuid references public.marketing_tasks (id) on delete set null,
  kind text not null check (
    kind in ('image', 'video', 'copy', 'script', 'idea', 'plan', 'calendar')
  ),
  title text not null default '',
  storage_path text,
  mime_type text,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create index if not exists idx_marketing_artifacts_chat on public.marketing_artifacts (chat_id, created_at desc);

-- ---------------------------------------------------------------------------
-- RPC: upsert knowledge row with float8[] -> vector(768)
-- ---------------------------------------------------------------------------
create or replace function public.kb_insert_row(
  p_company_id uuid,
  p_kind text,
  p_title text,
  p_content text,
  p_embedding float8[],
  p_tags text[],
  p_source_system text,
  p_source_run_id uuid,
  p_source_chat_id uuid
) returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  v_id uuid;
  v_vec vector(768);
begin
  if p_embedding is not null and array_length(p_embedding, 1) is not null then
    v_vec := p_embedding::vector(768);
  else
    v_vec := null;
  end if;

  insert into public.company_knowledge (
    company_id, kind, title, content, embedding, tags,
    source_system, source_run_id, source_chat_id
  ) values (
    p_company_id, p_kind, coalesce(p_title, ''), coalesce(p_content, ''),
    v_vec, coalesce(p_tags, '{}'),
    p_source_system, p_source_run_id, p_source_chat_id
  )
  returning id into v_id;

  return v_id;
end;
$$;

-- Vector similarity search (service role / RPC from backend with JWT optional)
create or replace function public.kb_match_company_knowledge(
  p_company_id uuid,
  p_query_embedding float8[],
  p_match_count int default 8,
  p_kinds text[] default null
) returns setof public.company_knowledge
language sql
stable
security definer
set search_path = public
as $$
  select ck.*
  from public.company_knowledge ck
  where ck.company_id = p_company_id
    and ck.embedding is not null
    and (p_kinds is null or ck.kind = any (p_kinds))
  order by ck.embedding <=> (p_query_embedding::vector(768))
  limit greatest(1, least(coalesce(p_match_count, 8), 50));
$$;

-- Text fallback search (no embedding)
create or replace function public.kb_search_company_knowledge_text(
  p_company_id uuid,
  p_query text,
  p_match_count int default 8,
  p_kinds text[] default null
) returns setof public.company_knowledge
language sql
stable
security definer
set search_path = public
as $$
  select ck.*
  from public.company_knowledge ck
  where ck.company_id = p_company_id
    and (p_kinds is null or ck.kind = any (p_kinds))
    and (
      p_query is null
      or length(trim(p_query)) = 0
      or ck.content ilike '%' || p_query || '%'
      or ck.title ilike '%' || p_query || '%'
    )
  order by ck.updated_at desc nulls last, ck.created_at desc
  limit greatest(1, least(coalesce(p_match_count, 8), 50));
$$;

revoke all on function public.kb_insert_row from public;
revoke all on function public.kb_match_company_knowledge from public;
revoke all on function public.kb_search_company_knowledge_text from public;
grant execute on function public.kb_insert_row to service_role;
grant execute on function public.kb_match_company_knowledge to service_role;
grant execute on function public.kb_search_company_knowledge_text to service_role;

-- ---------------------------------------------------------------------------
-- RLS
-- ---------------------------------------------------------------------------
alter table public.companies enable row level security;
alter table public.company_knowledge enable row level security;
alter table public.company_competitors enable row level security;
alter table public.marketing_chats enable row level security;
alter table public.marketing_messages enable row level security;
alter table public.marketing_tasks enable row level security;
alter table public.marketing_artifacts enable row level security;

-- companies
create policy "companies_select_own" on public.companies
  for select using (auth.uid() = user_id);
create policy "companies_insert_own" on public.companies
  for insert with check (auth.uid() = user_id);
create policy "companies_update_own" on public.companies
  for update using (auth.uid() = user_id);
create policy "companies_delete_own" on public.companies
  for delete using (auth.uid() = user_id);

-- company_knowledge
create policy "company_knowledge_select_own" on public.company_knowledge
  for select using (
    exists (select 1 from public.companies c where c.id = company_knowledge.company_id and c.user_id = auth.uid())
  );
create policy "company_knowledge_all_own" on public.company_knowledge
  for all using (
    exists (select 1 from public.companies c where c.id = company_knowledge.company_id and c.user_id = auth.uid())
  );

-- company_competitors
create policy "company_competitors_select_own" on public.company_competitors
  for select using (
    exists (select 1 from public.companies c where c.id = company_competitors.company_id and c.user_id = auth.uid())
  );
create policy "company_competitors_all_own" on public.company_competitors
  for all using (
    exists (select 1 from public.companies c where c.id = company_competitors.company_id and c.user_id = auth.uid())
  );

-- marketing_chats
create policy "marketing_chats_select_own" on public.marketing_chats
  for select using (
    auth.uid() = user_id
    and exists (select 1 from public.companies c where c.id = marketing_chats.company_id and c.user_id = auth.uid())
  );
create policy "marketing_chats_insert_own" on public.marketing_chats
  for insert with check (
    auth.uid() = user_id
    and exists (select 1 from public.companies c where c.id = marketing_chats.company_id and c.user_id = auth.uid())
  );
create policy "marketing_chats_update_own" on public.marketing_chats
  for update using (
    auth.uid() = user_id
    and exists (select 1 from public.companies c where c.id = marketing_chats.company_id and c.user_id = auth.uid())
  );
create policy "marketing_chats_delete_own" on public.marketing_chats
  for delete using (
    auth.uid() = user_id
    and exists (select 1 from public.companies c where c.id = marketing_chats.company_id and c.user_id = auth.uid())
  );

-- marketing_messages
create policy "marketing_messages_select_own" on public.marketing_messages
  for select using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_messages.chat_id and co.user_id = auth.uid()
    )
  );
create policy "marketing_messages_all_own" on public.marketing_messages
  for all using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_messages.chat_id and co.user_id = auth.uid()
    )
  );

-- marketing_tasks
create policy "marketing_tasks_select_own" on public.marketing_tasks
  for select using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_tasks.chat_id and co.user_id = auth.uid()
    )
  );
create policy "marketing_tasks_all_own" on public.marketing_tasks
  for all using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_tasks.chat_id and co.user_id = auth.uid()
    )
  );

-- marketing_artifacts
create policy "marketing_artifacts_select_own" on public.marketing_artifacts
  for select using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_artifacts.chat_id and co.user_id = auth.uid()
    )
  );
create policy "marketing_artifacts_all_own" on public.marketing_artifacts
  for all using (
    exists (
      select 1 from public.marketing_chats ch
      join public.companies co on co.id = ch.company_id
      where ch.id = marketing_artifacts.chat_id and co.user_id = auth.uid()
    )
  );
