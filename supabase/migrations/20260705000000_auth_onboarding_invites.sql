-- Auth workflow: app user profiles, onboarding state, and single-company invites

alter table public.organizations
  add column if not exists onboarding_completed_at timestamptz;

create table if not exists public.user_profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  full_name text,
  role_type text,
  job_title text,
  use_case text,
  auth_provider text,
  email_verified_at timestamptz,
  onboarding_completed_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.org_invites (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  email text not null,
  role text not null check (role in ('admin', 'analyst', 'viewer')),
  token_hash text not null unique,
  invited_by uuid references auth.users(id) on delete set null,
  accepted_by uuid references auth.users(id) on delete set null,
  accepted_at timestamptz,
  revoked_at timestamptz,
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_org_invites_active_email
  on public.org_invites (org_id, lower(email))
  where accepted_at is null and revoked_at is null;

create index if not exists idx_org_invites_org_created
  on public.org_invites (org_id, created_at desc);

create index if not exists idx_user_profiles_email
  on public.user_profiles (lower(email));

create trigger user_profiles_updated_at
  before update on public.user_profiles
  for each row execute function public.set_updated_at();

create trigger org_invites_updated_at
  before update on public.org_invites
  for each row execute function public.set_updated_at();

alter table public.user_profiles enable row level security;
alter table public.org_invites enable row level security;

create policy user_profiles_self_select on public.user_profiles
  for select using (user_id = auth.uid());

create policy user_profiles_self_update on public.user_profiles
  for update using (user_id = auth.uid())
  with check (user_id = auth.uid());

create policy org_invites_admin_select on public.org_invites
  for select using (
    org_id in (
      select m.org_id
      from public.memberships m
      where m.user_id = auth.uid()
        and m.role in ('owner', 'admin')
    )
  );

create or replace function public.handle_new_user_profile()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.user_profiles (
    user_id,
    email,
    full_name,
    auth_provider,
    email_verified_at
  )
  values (
    new.id,
    coalesce(new.email, ''),
    coalesce(new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'name'),
    coalesce(new.raw_app_meta_data->>'provider', 'email'),
    case
      when new.email_confirmed_at is not null then new.email_confirmed_at
      when coalesce(new.raw_app_meta_data->>'provider', 'email') <> 'email' then now()
      else null
    end
  )
  on conflict (user_id) do update
    set email = excluded.email,
        full_name = coalesce(public.user_profiles.full_name, excluded.full_name),
        auth_provider = excluded.auth_provider,
        email_verified_at = coalesce(public.user_profiles.email_verified_at, excluded.email_verified_at),
        updated_at = now();
  return new;
end;
$$;

drop trigger if exists on_auth_user_created_profile on auth.users;
create trigger on_auth_user_created_profile
  after insert on auth.users
  for each row execute function public.handle_new_user_profile();
