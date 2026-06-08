-- Allow runs to be created immediately while the master plan is generated
-- asynchronously by the worker.

alter table public.gtm_runs
  drop constraint if exists gtm_runs_status_check;

alter table public.gtm_runs
  add constraint gtm_runs_status_check
  check (status in ('planning', 'awaiting_plan_approval', 'queued', 'running', 'completed', 'failed'));
