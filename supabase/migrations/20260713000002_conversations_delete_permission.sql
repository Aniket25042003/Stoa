-- Add conversations:delete to system roles that can ask/delete conversations

update public.org_roles
set permissions = array_append(permissions, 'conversations:delete')
where role_key in ('owner', 'admin', 'analyst')
  and not ('conversations:delete' = any(permissions));
