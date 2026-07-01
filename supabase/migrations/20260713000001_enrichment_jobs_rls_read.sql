-- Security: align enrichment_jobs SELECT with documents:read permission

drop policy if exists enrichment_jobs_select on public.enrichment_jobs;

create policy enrichment_jobs_select on public.enrichment_jobs for select
  using (public.has_permission_in_org(org_id, 'documents:read'));
