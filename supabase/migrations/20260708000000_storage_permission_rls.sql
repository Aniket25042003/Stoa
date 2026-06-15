-- Align storage object policies with IAM permission helpers (custom roles).

drop policy if exists intelligence_docs_select on storage.objects;
drop policy if exists intelligence_docs_insert on storage.objects;
drop policy if exists intelligence_docs_update on storage.objects;
drop policy if exists intelligence_docs_delete on storage.objects;

create policy intelligence_docs_select on storage.objects for select
  using (
    bucket_id = 'intelligence-documents'
    and public.is_org_member(public.storage_org_id(name))
  );

create policy intelligence_docs_insert on storage.objects for insert
  with check (
    bucket_id = 'intelligence-documents'
    and public.has_permission_in_org(public.storage_org_id(name), 'documents:write')
  );

create policy intelligence_docs_update on storage.objects for update
  using (
    bucket_id = 'intelligence-documents'
    and public.has_permission_in_org(public.storage_org_id(name), 'documents:write')
  );

create policy intelligence_docs_delete on storage.objects for delete
  using (
    bucket_id = 'intelligence-documents'
    and public.has_permission_in_org(public.storage_org_id(name), 'documents:delete')
  );
