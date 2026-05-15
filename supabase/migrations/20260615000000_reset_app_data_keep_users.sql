-- Reset GTM + company-brain app data while keeping accounts.
-- Preserves auth.users and auth.identities (OAuth keeps working).
-- Clears auth sessions (everyone signs in again).
--
-- Storage: Supabase disallows DELETE on storage.objects via SQL.
-- Clear bucket `marketing-assets` from Dashboard → Storage if you want files gone.

DELETE FROM public.gtm_runs;

DELETE FROM public.companies;

DELETE FROM auth.refresh_tokens;
DELETE FROM auth.sessions;
