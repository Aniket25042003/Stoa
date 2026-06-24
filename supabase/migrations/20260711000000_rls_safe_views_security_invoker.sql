-- Fix security_invoker on safe views (RLS must apply to invoker, not view owner).

drop view if exists public.integration_connections_safe;
drop view if exists public.org_invites_safe;

create view public.integration_connections_safe
with (security_barrier = true, security_invoker = true)
as
select
  id,
  org_id,
  provider,
  status,
  label,
  provider_metadata,
  scopes,
  token_expires_at,
  last_sync_at,
  sync_cursor,
  last_error,
  data_source_id,
  created_by,
  created_at,
  updated_at
from public.integration_connections;

create view public.org_invites_safe
with (security_barrier = true, security_invoker = true)
as
select
  id,
  org_id,
  email,
  role,
  role_id,
  invited_by,
  accepted_by,
  accepted_at,
  revoked_at,
  expires_at,
  created_at,
  updated_at,
  profile_hints
from public.org_invites;

grant select on public.integration_connections_safe to authenticated, service_role;
grant select on public.org_invites_safe to authenticated, service_role;
