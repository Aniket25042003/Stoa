-- Add conversations:delete to system roles that can ask/delete conversations

update public.org_roles
set permissions = array_append(permissions, 'conversations:delete')
where role_key in ('owner', 'admin', 'analyst')
  and not ('conversations:delete' = any(permissions));

drop policy if exists conversations_delete on public.conversations;
create policy conversations_delete on public.conversations for delete
  using (public.has_permission_in_org(org_id, 'conversations:delete'));
