-- Phase A1: Extended company profile on organizations

alter table public.organizations
  add column if not exists profile jsonb not null default '{}'::jsonb;

comment on column public.organizations.profile is
  'Extended workspace profile: target_customers, business_model, stage, goals, brand_voice, known_competitors_notes';
