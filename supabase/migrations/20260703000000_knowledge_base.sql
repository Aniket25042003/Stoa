-- Phase 1c: Unified knowledge base (halfvec 3072 + hybrid retrieval)

create extension if not exists vector;

create table if not exists public.knowledge_items (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  source_id uuid references public.data_sources(id) on delete set null,
  kind text not null,
  feature_origin text,
  title text not null,
  summary text,
  content text,
  uri text,
  content_hash text,
  metadata jsonb not null default '{}'::jsonb,
  status text not null default 'active'
    check (status in ('active', 'archived', 'processing', 'failed')),
  version int not null default 1,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_knowledge_items_org_uri
  on public.knowledge_items (org_id, uri)
  where uri is not null;

create index if not exists idx_knowledge_items_org_kind
  on public.knowledge_items (org_id, kind);

create index if not exists idx_knowledge_items_org_hash
  on public.knowledge_items (org_id, content_hash)
  where content_hash is not null;

create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  item_id uuid not null references public.knowledge_items(id) on delete cascade,
  chunk_index int not null,
  content text not null,
  token_count int,
  kind text not null,
  metadata jsonb not null default '{}'::jsonb,
  content_hash text,
  embedding halfvec(3072),
  content_tsv tsvector generated always as (to_tsvector('english', coalesce(content, ''))) stored,
  created_at timestamptz not null default now(),
  unique (item_id, chunk_index)
);

create index if not exists idx_knowledge_chunks_org_kind
  on public.knowledge_chunks (org_id, kind);

create index if not exists idx_knowledge_chunks_embedding
  on public.knowledge_chunks using hnsw (embedding halfvec_cosine_ops);

create index if not exists idx_knowledge_chunks_tsv
  on public.knowledge_chunks using gin (content_tsv);

create trigger knowledge_items_updated_at
  before update on public.knowledge_items
  for each row execute function public.set_updated_at();

alter table public.knowledge_items enable row level security;
alter table public.knowledge_chunks enable row level security;

create policy knowledge_items_org on public.knowledge_items for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

create policy knowledge_chunks_org on public.knowledge_chunks for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

-- Hybrid retrieval: vector + full-text fused via Reciprocal Rank Fusion (RRF)
create or replace function public.match_knowledge(
  p_org_id uuid,
  p_query_embedding halfvec(3072),
  p_query_text text,
  p_kinds text[] default null,
  p_match_count int default 40,
  p_rrf_k int default 60
)
returns table (
  chunk_id uuid,
  item_id uuid,
  content text,
  kind text,
  item_title text,
  metadata jsonb,
  vector_rank int,
  text_rank int,
  rrf_score float
)
language sql
stable
security definer
set search_path = public
as $$
  with vector_hits as (
    select
      kc.id as chunk_id,
      kc.item_id,
      kc.content,
      kc.kind,
      ki.title as item_title,
      kc.metadata,
      row_number() over (order by kc.embedding <=> p_query_embedding) as vector_rank
    from public.knowledge_chunks kc
    join public.knowledge_items ki on ki.id = kc.item_id
    where kc.org_id = p_org_id
      and kc.embedding is not null
      and ki.status = 'active'
      and (p_kinds is null or kc.kind = any(p_kinds))
    order by kc.embedding <=> p_query_embedding
    limit p_match_count
  ),
  text_hits as (
    select
      kc.id as chunk_id,
      kc.item_id,
      kc.content,
      kc.kind,
      ki.title as item_title,
      kc.metadata,
      row_number() over (
        order by ts_rank_cd(kc.content_tsv, websearch_to_tsquery('english', p_query_text)) desc
      ) as text_rank
    from public.knowledge_chunks kc
    join public.knowledge_items ki on ki.id = kc.item_id
    where kc.org_id = p_org_id
      and ki.status = 'active'
      and (p_kinds is null or kc.kind = any(p_kinds))
      and p_query_text is not null
      and length(trim(p_query_text)) > 0
      and kc.content_tsv @@ websearch_to_tsquery('english', p_query_text)
    order by ts_rank_cd(kc.content_tsv, websearch_to_tsquery('english', p_query_text)) desc
    limit p_match_count
  ),
  fused as (
    select
      coalesce(v.chunk_id, t.chunk_id) as chunk_id,
      coalesce(v.item_id, t.item_id) as item_id,
      coalesce(v.content, t.content) as content,
      coalesce(v.kind, t.kind) as kind,
      coalesce(v.item_title, t.item_title) as item_title,
      coalesce(v.metadata, t.metadata) as metadata,
      v.vector_rank,
      t.text_rank,
      coalesce(1.0 / (p_rrf_k + v.vector_rank), 0.0)
        + coalesce(1.0 / (p_rrf_k + t.text_rank), 0.0) as rrf_score
    from vector_hits v
    full outer join text_hits t on v.chunk_id = t.chunk_id
  )
  select
    f.chunk_id,
    f.item_id,
    f.content,
    f.kind,
    f.item_title,
    f.metadata,
    f.vector_rank::int,
    f.text_rank::int,
    f.rrf_score::float
  from fused f
  order by f.rrf_score desc
  limit p_match_count;
$$;

revoke all on function public.match_knowledge(uuid, halfvec, text, text[], int, int) from public;
grant execute on function public.match_knowledge(uuid, halfvec, text, text[], int, int) to service_role;

-- Backward-compatible wrapper during cutover
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
    kc.id,
    (kc.metadata->>'document_id')::uuid as document_id,
    kc.content,
    1 - (kc.embedding::vector(3072) <=> p_embedding::vector(3072)) as similarity
  from public.knowledge_chunks kc
  where kc.org_id = p_org_id
    and kc.embedding is not null
    and kc.kind = 'document'
  order by kc.embedding <=> p_embedding::halfvec(3072)
  limit p_match_count;
$$;

revoke all on function public.match_document_chunks(uuid, vector, int) from public;
grant execute on function public.match_document_chunks(uuid, vector, int) to service_role;
