-- Security: replace current_org_id() policies on campaign-analysis tables (multi-org fix)

do $policy$
declare
  t text;
begin
  foreach t in array array['analytics_metric_facts', 'deal_stage_snapshots']
  loop
    execute format('drop policy if exists %I on public.%I', t || '_select', t);
    execute format('drop policy if exists %I on public.%I', t || '_insert', t);
    execute format('drop policy if exists %I on public.%I', t || '_update', t);
    execute format('drop policy if exists %I on public.%I', t || '_delete', t);

    execute format(
      'create policy %I on public.%I for select using (public.is_org_member(org_id))',
      t || '_select', t
    );
    execute format(
      'create policy %I on public.%I for insert with check (public.has_permission_in_org(org_id, ''documents:write''))',
      t || '_insert', t
    );
    execute format(
      'create policy %I on public.%I for update using (public.has_permission_in_org(org_id, ''documents:write'')) with check (public.has_permission_in_org(org_id, ''documents:write''))',
      t || '_update', t
    );
    execute format(
      'create policy %I on public.%I for delete using (public.has_permission_in_org(org_id, ''documents:delete''))',
      t || '_delete', t
    );
  end loop;
end
$policy$;
