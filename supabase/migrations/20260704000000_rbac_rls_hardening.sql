-- Role-aware RLS: viewers read-only; analysts write; admins delete

create or replace function public.role_rank(role text)
returns int
language sql
immutable
as $$
  select case role
    when 'owner' then 4
    when 'admin' then 3
    when 'analyst' then 2
    when 'viewer' then 1
    else 0
  end;
$$;

create or replace function public.has_min_role(min_role text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select public.role_rank(public.current_role()) >= public.role_rank(min_role);
$$;

revoke all on function public.has_min_role(text) from public;
grant execute on function public.has_min_role(text) to authenticated, service_role;

-- Intelligence tables
do $policy$
declare
  t text;
begin
  foreach t in array array[
    'data_sources', 'documents', 'ingestion_jobs', 'document_chunks',
    'intelligence', 'icp_profiles', 'competitors', 'competitive_alerts',
    'campaigns', 'precomputed_insights', 'knowledge_items', 'knowledge_chunks'
  ]
  loop
    execute format('drop policy if exists %I on public.%I', t || '_org', t);
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

-- Conversations: viewers may read; writes via API (service role) for ask flow
drop policy if exists conversations_org on public.conversations;
create policy conversations_select on public.conversations for select
  using (org_id = public.current_org_id());
create policy conversations_insert on public.conversations for insert
  with check (org_id = public.current_org_id() and public.has_min_role('analyst'));
create policy conversations_update on public.conversations for update
  using (org_id = public.current_org_id() and public.has_min_role('analyst'))
  with check (org_id = public.current_org_id());
create policy conversations_delete on public.conversations for delete
  using (org_id = public.current_org_id() and public.has_min_role('admin'));

drop policy if exists messages_org on public.messages;
create policy messages_select on public.messages for select
  using (org_id = public.current_org_id());
create policy messages_insert on public.messages for insert
  with check (org_id = public.current_org_id() and public.has_min_role('analyst'));
create policy messages_update on public.messages for update
  using (org_id = public.current_org_id() and public.has_min_role('analyst'))
  with check (org_id = public.current_org_id());
create policy messages_delete on public.messages for delete
  using (org_id = public.current_org_id() and public.has_min_role('admin'));

-- Waitlist: no anonymous direct inserts
create table if not exists public.waitlist (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null unique,
  created_at timestamptz not null default now()
);

alter table public.waitlist enable row level security;

drop policy if exists "Allow anonymous inserts" on public.waitlist;
