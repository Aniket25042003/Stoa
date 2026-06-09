-- Storage policies for intelligence-documents bucket (org-prefixed paths)

insert into storage.buckets (id, name, public)
values ('intelligence-documents', 'intelligence-documents', false)
on conflict (id) do nothing;

create or replace function public.storage_org_id(object_name text)
returns uuid
language sql
stable
as $$
  select nullif(split_part(object_name, '/', 1), '')::uuid;
$$;

drop policy if exists intelligence_docs_select on storage.objects;
drop policy if exists intelligence_docs_insert on storage.objects;
drop policy if exists intelligence_docs_update on storage.objects;
drop policy if exists intelligence_docs_delete on storage.objects;

create policy intelligence_docs_select on storage.objects for select
  using (
    bucket_id = 'intelligence-documents'
    and public.storage_org_id(name) in (
      select org_id from public.memberships where user_id = auth.uid()
    )
  );

create policy intelligence_docs_insert on storage.objects for insert
  with check (
    bucket_id = 'intelligence-documents'
    and public.storage_org_id(name) in (
      select org_id from public.memberships
      where user_id = auth.uid() and role in ('owner', 'admin', 'analyst')
    )
  );

create policy intelligence_docs_update on storage.objects for update
  using (
    bucket_id = 'intelligence-documents'
    and public.storage_org_id(name) in (
      select org_id from public.memberships
      where user_id = auth.uid() and role in ('owner', 'admin', 'analyst')
    )
  );

create policy intelligence_docs_delete on storage.objects for delete
  using (
    bucket_id = 'intelligence-documents'
    and public.storage_org_id(name) in (
      select org_id from public.memberships
      where user_id = auth.uid() and role in ('owner', 'admin')
    )
  );
