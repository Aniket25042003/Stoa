# Supabase migration reset

The greenfield rebuild uses new migrations in `supabase/migrations/20260701*`.

## Option A: Reset existing project (recommended if keeping Google OAuth config)

1. Backup any data you need
2. Apply `20260701000000_reset_legacy_schema.sql` first (drops old GTM/marketing tables, keeps `auth.users`)
3. Apply remaining `20260701*` migrations in order

## Option B: Fresh Supabase project

1. Create new project
2. Configure Google OAuth provider + redirect URLs
3. Apply all `supabase/migrations/` files
4. Update env vars in Vercel + Render

## Storage bucket

Create bucket `intelligence-documents` (or set `STOA_STORAGE_BUCKET`) in Supabase Storage with appropriate policies for service-role uploads.
