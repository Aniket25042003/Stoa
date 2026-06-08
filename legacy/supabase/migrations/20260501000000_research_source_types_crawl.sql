-- Allow crawl-backed research items; stop accepting reddit/x on new rows.
-- Backfill legacy reddit/x rows so the stricter check can be applied.

update public.research_sources
set
  metadata = coalesce(metadata, '{}'::jsonb) || jsonb_build_object('legacy_source_type', to_jsonb(source_type)),
  source_type = 'other'
where source_type in ('reddit', 'x');

alter table public.research_sources
  drop constraint if exists research_sources_source_type_check;

alter table public.research_sources
  add constraint research_sources_source_type_check
  check (source_type in ('web', 'serp', 'crawl', 'other'));
