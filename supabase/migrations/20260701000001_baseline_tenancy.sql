-- Phase 0: Organizations, memberships (RBAC), audit log

create extension if not exists "pgcrypto";

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.organizations (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  slug text not null unique,
  website_url text,
  industry text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.memberships (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('owner', 'admin', 'analyst', 'viewer')),
  created_at timestamptz not null default now(),
  unique (org_id, user_id),
  unique (user_id)  -- one org per account
);

create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  user_id uuid references auth.users(id) on delete set null,
  action text not null,
  resource_type text not null,
  resource_id uuid,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_memberships_user on public.memberships(user_id);
create index if not exists idx_audit_log_org on public.audit_log(org_id, created_at desc);

create trigger organizations_updated_at
  before update on public.organizations
  for each row execute function public.set_updated_at();

alter table public.organizations enable row level security;
alter table public.memberships enable row level security;
alter table public.audit_log enable row level security;

-- Helper: current user's org_id
create or replace function public.current_org_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select org_id from public.memberships where user_id = auth.uid() limit 1;
$$;

create or replace function public.current_role()
returns text
language sql
stable
security definer
set search_path = public
as $$
  select role from public.memberships where user_id = auth.uid() limit 1;
$$;

-- RLS policies
create policy org_select on public.organizations
  for select using (
    id in (select org_id from public.memberships where user_id = auth.uid())
  );

create policy org_update on public.organizations
  for update using (
    id in (
      select org_id from public.memberships
      where user_id = auth.uid() and role in ('owner', 'admin')
    )
  );

create policy membership_select on public.memberships
  for select using (user_id = auth.uid());

create policy audit_select on public.audit_log
  for select using (
    org_id in (select org_id from public.memberships where user_id = auth.uid())
  );

-- Auto-provision org on first login (via service role from API; optional trigger for direct client)
create or replace function public.handle_new_user_org()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  new_org_id uuid;
  slug_base text;
begin
  if exists (select 1 from public.memberships where user_id = new.id) then
    return new;
  end if;
  slug_base := coalesce(split_part(new.email, '@', 1), 'workspace');
  insert into public.organizations (name, slug)
  values (coalesce(new.raw_user_meta_data->>'full_name', slug_base || '''s workspace'), slug_base || '-' || substr(new.id::text, 1, 8))
  returning id into new_org_id;
  insert into public.memberships (org_id, user_id, role) values (new_org_id, new.id, 'owner');
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_org on auth.users;
create trigger on_auth_user_created_org
  after insert on auth.users
  for each row execute function public.handle_new_user_org();
