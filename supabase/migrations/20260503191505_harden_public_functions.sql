-- Hardening: rls_auto_enable is an event-trigger helper and must not be exposed as PostgREST RPC.
-- See Supabase linter 0028 / 0029 (SECURITY DEFINER callable by anon or authenticated).
revoke execute on function public.rls_auto_enable() from public;
revoke execute on function public.rls_auto_enable() from anon;
revoke execute on function public.rls_auto_enable() from authenticated;
revoke execute on function public.rls_auto_enable() from service_role;

-- Lint 0011: stable search_path for trigger helper.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;
