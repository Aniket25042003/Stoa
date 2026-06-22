-- Phase 4: Content at scale (AI asset generation)

create table if not exists public.content_assets (
  id uuid primary key default gen_random_uuid(),
  org_id uuid not null references public.organizations(id) on delete cascade,
  campaign_id uuid references public.campaigns(id) on delete set null,
  
  -- Generation input
  asset_type text not null check (asset_type in ('image', 'video')),
  prompt text not null,
  enriched_prompt text,        -- After KB context enrichment
  reference_asset_id uuid references public.content_assets(id) on delete set null,
  
  -- Generation config
  -- Images: { model, aspect_ratio, mime_type, number_of_images, use_fast_model }
  -- Videos: { model, aspect_ratio, resolution, duration_seconds, use_fast_model }
  config jsonb not null default '{}'::jsonb,
  
  -- Result
  status text not null default 'queued' 
    check (status in ('queued', 'generating', 'completed', 'failed')),
  error text,
  
  -- Generated files (array for multi-image batches)
  -- [{ storage_path, public_url, mime_type, width, height, duration_seconds, size_bytes }]
  files jsonb not null default '[]'::jsonb,
  
  -- Metadata
  -- { model_used, generation_time_seconds, vertex_operation_id, kb_context_refs }
  generation_metadata jsonb not null default '{}'::jsonb,
  
  created_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_content_assets_org on public.content_assets (org_id);
create index if not exists idx_content_assets_campaign on public.content_assets (campaign_id) where campaign_id is not null;
create index if not exists idx_content_assets_org_type on public.content_assets (org_id, asset_type);

create trigger content_assets_updated_at before update on public.content_assets
  for each row execute function public.set_updated_at();

alter table public.content_assets enable row level security;

drop policy if exists content_assets_org on public.content_assets;
create policy content_assets_org on public.content_assets for all
  using (org_id = public.current_org_id())
  with check (org_id = public.current_org_id());

-- Storage bucket for generated media
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'content-assets', 'content-assets', false, 104857600, -- 100MB limit
  array['image/png', 'image/jpeg', 'image/webp', 'video/mp4']
)
on conflict (id) do nothing;

-- Storage RLS policies
drop policy if exists content_assets_select on storage.objects;
create policy content_assets_select on storage.objects for select
  using (
    bucket_id = 'content-assets'
    and public.is_org_member(public.storage_org_id(name))
  );

drop policy if exists content_assets_insert on storage.objects;
create policy content_assets_insert on storage.objects for insert
  with check (
    bucket_id = 'content-assets'
    and public.has_permission_in_org(public.storage_org_id(name), 'content:write')
  );

drop policy if exists content_assets_update on storage.objects;
create policy content_assets_update on storage.objects for update
  using (
    bucket_id = 'content-assets'
    and public.has_permission_in_org(public.storage_org_id(name), 'content:write')
  );

drop policy if exists content_assets_delete on storage.objects;
create policy content_assets_delete on storage.objects for delete
  using (
    bucket_id = 'content-assets'
    and public.has_permission_in_org(public.storage_org_id(name), 'content:delete')
  );
