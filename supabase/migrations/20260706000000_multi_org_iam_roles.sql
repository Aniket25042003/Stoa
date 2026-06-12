-- Multi-org tenancy + IAM-style org_roles

-- org_roles must exist before memberships.role_id FK
create table if not exists public.org_roles (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  name text not null,
  role_key text not null default 'custom',
  description text,
  permissions text[] not null default '{}',
  is_system boolean not null default false,
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (org_id, role_key)
);

create unique index if not exists org_roles_org_name_lower_unique
  on public.org_roles (org_id, lower(name));

create index if not exists idx_org_roles_org on public.org_roles(org_id);

create trigger org_roles_updated_at
  before update on public.org_roles
  for each row execute function public.set_updated_at();

alter table public.org_roles enable row level security;

create policy org_roles_member_select on public.org_roles
  for select using (
    org_id in (select org_id from public.memberships where user_id = auth.uid())
  );

-- Allow multi-org memberships
alter table public.memberships drop constraint if exists memberships_user_id_key;

alter table public.memberships
  add column if not exists role_id uuid references public.org_roles(id) on delete restrict;

alter table public.user_profiles
  add column if not exists last_active_org_id uuid references public.organizations(id) on delete set null;

alter table public.org_invites
  add column if not exists role_id uuid references public.org_roles(id) on delete set null,
  add column if not exists profile_hints jsonb not null default '{}'::jsonb;

-- Disable auto-provision org on signup (orgs created at onboarding completion)
drop trigger if exists on_auth_user_created_org on auth.users;

-- Seed system roles for every existing org and backfill memberships.role_id
do $seed$
declare
  org record;
  owner_id uuid;
  admin_id uuid;
  analyst_id uuid;
  viewer_id uuid;
  m record;
begin
  for org in select id from public.organizations loop
    if not exists (select 1 from public.org_roles where org_id = org.id and role_key = 'owner') then
      insert into public.org_roles (org_id, name, role_key, description, permissions, is_system)
      values (
        org.id, 'Owner', 'owner',
        'Full organization access including deletion and ownership transfer.',
        array[
          'documents:read','documents:write','documents:delete',
          'data_sources:read','data_sources:write',
          'intelligence:read','intelligence:rebuild',
          'insights:read','insights:refresh',
          'conversations:read','conversations:ask',
          'competitive:read','competitive:manage','competitive:scan',
          'campaigns:read','campaigns:create','campaigns:edit',
          'team:read','team:invite','team:remove','team:assign_roles',
          'roles:manage','org:update','org:leave','audit:read',
          'org:delete','org:transfer_ownership'
        ],
        true
      ) returning id into owner_id;
    else
      select id into owner_id from public.org_roles where org_id = org.id and role_key = 'owner';
    end if;

    if not exists (select 1 from public.org_roles where org_id = org.id and role_key = 'admin') then
      insert into public.org_roles (org_id, name, role_key, description, permissions, is_system)
      values (
        org.id, 'Admin', 'admin',
        'Manage team, data, and intelligence; cannot manage custom roles.',
        array[
          'documents:read','documents:write','documents:delete',
          'data_sources:read','data_sources:write',
          'intelligence:read','intelligence:rebuild',
          'insights:read','insights:refresh',
          'conversations:read','conversations:ask',
          'competitive:read','competitive:manage','competitive:scan',
          'campaigns:read','campaigns:create','campaigns:edit',
          'team:read','team:invite','team:remove','team:assign_roles',
          'org:update','org:leave','audit:read'
        ],
        true
      ) returning id into admin_id;
    else
      select id into admin_id from public.org_roles where org_id = org.id and role_key = 'admin';
    end if;

    if not exists (select 1 from public.org_roles where org_id = org.id and role_key = 'analyst') then
      insert into public.org_roles (org_id, name, role_key, description, permissions, is_system)
      values (
        org.id, 'Analyst', 'analyst',
        'Create and edit content, run scans, and ask questions.',
        array[
          'documents:read','documents:write',
          'data_sources:read','data_sources:write',
          'intelligence:read','insights:read',
          'conversations:read','conversations:ask',
          'competitive:read','competitive:manage','competitive:scan',
          'campaigns:read','campaigns:create','campaigns:edit',
          'team:read','org:leave'
        ],
        true
      ) returning id into analyst_id;
    else
      select id into analyst_id from public.org_roles where org_id = org.id and role_key = 'analyst';
    end if;

    if not exists (select 1 from public.org_roles where org_id = org.id and role_key = 'viewer') then
      insert into public.org_roles (org_id, name, role_key, description, permissions, is_system)
      values (
        org.id, 'Viewer', 'viewer',
        'Read-only access to organization data.',
        array[
          'documents:read','data_sources:read','intelligence:read','insights:read',
          'conversations:read','competitive:read','campaigns:read','team:read','org:leave'
        ],
        true
      ) returning id into viewer_id;
    else
      select id into viewer_id from public.org_roles where org_id = org.id and role_key = 'viewer';
    end if;

    for m in select id, role from public.memberships where org_id = org.id and role_id is null loop
      update public.memberships
      set role_id = case m.role
        when 'owner' then owner_id
        when 'admin' then admin_id
        when 'analyst' then analyst_id
        else viewer_id
      end
      where id = m.id;
    end loop;
  end loop;
end
$seed$;

-- Backfill org_invites.role_id from role text
update public.org_invites oi
set role_id = r.id
from public.org_roles r
where oi.org_id = r.org_id
  and oi.role_id is null
  and r.role_key = oi.role;

-- Permission-aware RLS helpers (multi-org safe)
create or replace function public.is_org_member(check_org_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1 from public.memberships m
    where m.user_id = auth.uid() and m.org_id = check_org_id
  );
$$;

create or replace function public.member_permissions(check_org_id uuid)
returns text[]
language sql
stable
security definer
set search_path = public
as $$
  select coalesce(r.permissions, '{}'::text[])
  from public.memberships m
  join public.org_roles r on r.id = m.role_id
  where m.user_id = auth.uid() and m.org_id = check_org_id
  limit 1;
$$;

create or replace function public.is_org_owner(check_org_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.memberships m
    join public.org_roles r on r.id = m.role_id
    where m.user_id = auth.uid()
      and m.org_id = check_org_id
      and r.role_key = 'owner'
  );
$$;

create or replace function public.has_permission_in_org(check_org_id uuid, perm text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select public.is_org_owner(check_org_id)
    or perm = any(public.member_permissions(check_org_id));
$$;

create or replace function public.has_min_role_in_org(check_org_id uuid, min_role text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select public.role_rank(coalesce(
    (select r.role_key from public.memberships m join public.org_roles r on r.id = m.role_id
     where m.user_id = auth.uid() and m.org_id = check_org_id limit 1),
    'viewer'
  )) >= public.role_rank(min_role);
$$;

revoke all on function public.is_org_member(uuid) from public;
revoke all on function public.member_permissions(uuid) from public;
revoke all on function public.is_org_owner(uuid) from public;
revoke all on function public.has_permission_in_org(uuid, text) from public;
revoke all on function public.has_min_role_in_org(uuid, text) from public;
grant execute on function public.is_org_member(uuid) to authenticated, service_role;
grant execute on function public.member_permissions(uuid) to authenticated, service_role;
grant execute on function public.is_org_owner(uuid) to authenticated, service_role;
grant execute on function public.has_permission_in_org(uuid, text) to authenticated, service_role;
grant execute on function public.has_min_role_in_org(uuid, text) to authenticated, service_role;

-- Rebuild RLS policies for multi-org + permission checks
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
    execute format('drop policy if exists %I on public.%I', t || '_select', t);
    execute format('drop policy if exists %I on public.%I', t || '_insert', t);
    execute format('drop policy if exists %I on public.%I', t || '_update', t);
    execute format('drop policy if exists %I on public.%I', t || '_delete', t);
    execute format('drop policy if exists %I on public.%I', t || '_org', t);
    execute format('create policy %I on public.%I for select using (public.is_org_member(org_id))', t || '_select', t);
    execute format(
      'create policy %I on public.%I for insert with check (public.has_permission_in_org(org_id, ''documents:write''))',
      t || '_insert', t
    );
    execute format(
      'create policy %I on public.%I for update using (public.has_permission_in_org(org_id, ''documents:write'')) with check (public.is_org_member(org_id))',
      t || '_update', t
    );
    execute format(
      'create policy %I on public.%I for delete using (public.has_permission_in_org(org_id, ''documents:delete''))',
      t || '_delete', t
    );
  end loop;
end
$policy$;

drop policy if exists conversations_select on public.conversations;
drop policy if exists conversations_insert on public.conversations;
drop policy if exists conversations_update on public.conversations;
drop policy if exists conversations_delete on public.conversations;
drop policy if exists conversations_org on public.conversations;

create policy conversations_select on public.conversations for select
  using (public.is_org_member(org_id));
create policy conversations_insert on public.conversations for insert
  with check (public.has_permission_in_org(org_id, 'conversations:ask'));
create policy conversations_update on public.conversations for update
  using (public.has_permission_in_org(org_id, 'conversations:ask'))
  with check (public.is_org_member(org_id));
create policy conversations_delete on public.conversations for delete
  using (public.has_permission_in_org(org_id, 'documents:delete'));

drop policy if exists messages_select on public.messages;
drop policy if exists messages_insert on public.messages;
drop policy if exists messages_update on public.messages;
drop policy if exists messages_delete on public.messages;
drop policy if exists messages_org on public.messages;

create policy messages_select on public.messages for select
  using (public.is_org_member(org_id));
create policy messages_insert on public.messages for insert
  with check (public.has_permission_in_org(org_id, 'conversations:ask'));
create policy messages_update on public.messages for update
  using (public.has_permission_in_org(org_id, 'conversations:ask'))
  with check (public.is_org_member(org_id));
create policy messages_delete on public.messages for delete
  using (public.has_permission_in_org(org_id, 'documents:delete'));

-- Memberships: users see their own rows across orgs
drop policy if exists membership_select on public.memberships;
create policy membership_select on public.memberships
  for select using (user_id = auth.uid());

-- Organizations: members can select any org they belong to
drop policy if exists org_select on public.organizations;
create policy org_select on public.organizations
  for select using (public.is_org_member(id));

drop policy if exists org_update on public.organizations;
create policy org_update on public.organizations
  for update using (public.has_permission_in_org(id, 'org:update'));

-- Audit log
drop policy if exists audit_select on public.audit_log;
create policy audit_select on public.audit_log
  for select using (public.has_permission_in_org(org_id, 'audit:read'));
